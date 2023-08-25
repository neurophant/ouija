import asyncio
import os
from typing import Union

from .tuning import StreamTuning, DatagramTuning
from .connector import StreamConnector, DatagramConnector
from .telemetry import Telemetry
from .data import Parser, SEPARATOR, HTTP_PORT, HTTPS_PORT, CONNECT
from .log import logger


class Relay:
    telemetry: Telemetry
    tuning: Union[StreamTuning, DatagramTuning]
    relay_host: str
    relay_port: int
    proxy_host: str
    proxy_port: int
    connectors: dict[str, Union[StreamConnector, DatagramConnector]]

    def __init__(
            self,
            *,
            telemetry: Telemetry,
            tuning: Union[StreamTuning, DatagramTuning],
            relay_host: str,
            relay_port: int,
            proxy_host: str,
            proxy_port: int,
    ) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.relay_host = relay_host
        self.relay_port = relay_port
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.connectors = dict()

    async def request_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
            https: bool,
    ) -> None:
        """Request handler - should be overridden with protocol-based implementation
        :returns: None"""
        raise NotImplementedError

    async def connect_wrapped(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        data = await reader.readuntil(SEPARATOR)
        request = Parser(data=data)
        if request.error:
            logger.error('Parse error')
            return

        if request.method != CONNECT:
            reader.feed_data(data)

        await self.request_handler(
            reader=reader,
            writer=writer,
            remote_host=request.host,
            remote_port=request.port or (HTTPS_PORT if request.method == CONNECT else HTTP_PORT),
            https=True if request.method == CONNECT else False,
        )

    async def connect(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            await asyncio.wait_for(self.connect_wrapped(reader=reader, writer=writer), self.tuning.serving_timeout * 2)
        except TimeoutError:
            self.telemetry.timeout_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.serving_error()

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        asyncio.create_task(self.connect(reader=reader, writer=writer))

    async def serve(self) -> None:
        """HTTPS proxy server entry point
        :returns: None
        """
        server = await asyncio.start_server(
            self.handle,
            self.relay_host,
            self.relay_port,
        )
        async with server:
            await server.serve_forever()

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
    async def request_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
            https: bool,
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
            https=https,
        )
        await connector.serve()


class DatagramRelay(Relay):
    async def request_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
            https: bool,
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
            https=https,
        )
        await connector.serve()
