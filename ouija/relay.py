import asyncio
import os
from typing import Union

from .tuning import StreamTuning, DatagramTuning
from .connector import StreamConnector, DatagramConnector
from .telemetry import StreamTelemetry, DatagramTelemetry
from .data import Parser, SEPARATOR
from .log import logger


class Relay:
    telemetry: Union[StreamTelemetry, DatagramTelemetry]
    tuning: Union[StreamTuning, DatagramTuning]
    proxy_host: str
    proxy_port: int
    connectors: dict[str, Union[StreamConnector, DatagramConnector]]

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
        self.connectors = dict()

    async def https_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
    ) -> None:
        """HTTPS handler - should be overridden with protocol-based implementation
        :returns: None"""
        raise NotImplementedError

    async def connect_wrapped(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
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

    async def connect(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            await asyncio.wait_for(self.connect_wrapped(reader=reader, writer=writer), self.tuning.serving_timeout * 2)
        except TimeoutError:
            self.telemetry.timeout_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.serving_error()

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """HTTPS proxy server entry point
        :returns: None
        """

        asyncio.create_task(self.connect(reader=reader, writer=writer))

    async def debug(self) -> None:    # pragma: no cover
        """Debug monitor with telemetry output
        :returns: None
        """

        while True:
            await asyncio.sleep(1)
            self.telemetry.collect(active=len(self.connectors))
            os.system('clear')
            print(self.telemetry)


class StreamRelay(Relay):
    async def https_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
    ) -> None:
        connector = StreamConnector(
            telemetry=self.telemetry,
            tuning=self.tuning,
            relay=self,
            reader=reader,
            writer=writer,
            proxy_host=self.proxy_host,
            proxy_port=self.proxy_port,
            remote_host=remote_host,
            remote_port=remote_port,
        )
        await connector.serve()


class DatagramRelay(Relay):
    async def https_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
    ) -> None:
        connector = DatagramConnector(
            telemetry=self.telemetry,
            tuning=self.tuning,
            relay=self,
            reader=reader,
            writer=writer,
            proxy_host=self.proxy_host,
            proxy_port=self.proxy_port,
            remote_host=remote_host,
            remote_port=remote_port,
        )
        await connector.serve()
