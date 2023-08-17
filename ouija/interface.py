import asyncio
import os
from typing import Union

from .tuning import StreamTuning, DatagramTuning
from .relay import StreamRelay, DatagramRelay
from .telemetry import StreamTelemetry, DatagramTelemetry
from .data import Parser, SEPARATOR
from .log import logger


class Interface:
    telemetry: Union[StreamTelemetry, DatagramTelemetry]
    tuning: Union[StreamTuning, DatagramTuning]
    proxy_host: str
    proxy_port: int
    index: int
    sessions: dict[int, asyncio.Task]

    def __init__(
            self,
            *,
            telemetry: Union[StreamTelemetry, DatagramTelemetry],
            tuning: Union[StreamTuning, DatagramTuning],
            proxy_host: str,
            proxy_port: int,
    ) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.index = 0
        self.sessions = dict()

    async def https_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
    ) -> None:
        """HTTPS handler - should be overridden with protocol-oriented implementation
        :returns: None"""
        raise NotImplemented

    async def session_wrapped(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        data = await reader.readuntil(SEPARATOR)
        request = Parser(data=data)
        if request.error:
            logger.error('Parse error')
        elif request.method == 'CONNECT':
            await self.https_handler(
                reader=reader,
                writer=writer,
                remote_host=request.host,
                remote_port=request.port,
            )
        else:
            logger.error(f'{request.method} method is not supported')

    async def session(self, *, index: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            await asyncio.wait_for(self.session_wrapped(reader=reader, writer=writer), self.tuning.serving_timeout * 2)
        except TimeoutError:
            self.telemetry.timeout_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.serving_error()
        finally:
            _ = self.sessions.pop(index, None)

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """HTTPS proxy server entry point
        :returns: None
        """

        self.sessions[self.index] = asyncio.create_task(self.session(index=self.index, reader=reader, writer=writer))
        self.index += 1

    async def debug(self) -> None:    # pragma: no cover
        """Debug monitor with telemetry output
        :returns: None
        """

        while True:
            await asyncio.sleep(1)
            self.telemetry.link(links=len(self.sessions))
            os.system('clear')
            print(self.telemetry)


class StreamInterface(Interface):
    async def https_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
    ) -> None:
        relay = StreamRelay(
            telemetry=self.telemetry,
            tuning=self.tuning,
            reader=reader,
            writer=writer,
            proxy_host=self.proxy_host,
            proxy_port=self.proxy_port,
            remote_host=remote_host,
            remote_port=remote_port,
        )
        await relay.serve()


class DatagramInterface(Interface):
    async def https_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
    ) -> None:
        relay = DatagramRelay(
            telemetry=self.telemetry,
            tuning=self.tuning,
            reader=reader,
            writer=writer,
            proxy_host=self.proxy_host,
            proxy_port=self.proxy_port,
            remote_host=remote_host,
            remote_port=remote_port,
        )
        await relay.serve()
