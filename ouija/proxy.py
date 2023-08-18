import asyncio
import os
from typing import Optional, Union

from .link import StreamLink, DatagramLink
from .tuning import StreamTuning, DatagramTuning
from .telemetry import StreamTelemetry, DatagramTelemetry
from .log import logger


class Proxy:
    telemetry: Union[StreamTelemetry, DatagramTelemetry]
    tuning: Union[StreamTuning, DatagramTuning]
    proxy_host: str
    proxy_port: int
    links: dict[Union[str, tuple[str, int]], Union[StreamLink, DatagramLink]]

    async def serve(self) -> None:
        """Proxy server entry point - should be overridden with protocol-based implementation
        :returns: None"""
        raise NotImplementedError

    async def debug(self) -> None:    # pragma: no cover
        """Debug monitor with telemetry output
        :returns: None
        """

        while True:
            await asyncio.sleep(1)
            self.telemetry.collect(active=len(self.links))
            os.system('clear')
            print(self.telemetry)


class StreamProxy(Proxy):
    def __init__(
            self,
            *,
            telemetry: StreamTelemetry,
            tuning: StreamTuning,
            proxy_host: str,
            proxy_port: int,
    ) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.links = dict()

    async def link_wrapped(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        link = StreamLink(
            telemetry=self.telemetry,
            tuning=self.tuning,
            proxy=self,
            reader=reader,
            writer=writer,
        )
        await link.serve()

    async def link(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            await asyncio.wait_for(self.link_wrapped(reader=reader, writer=writer), self.tuning.serving_timeout * 2)
        except TimeoutError:
            self.telemetry.timeout_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.serving_error()

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        asyncio.create_task(self.link(reader=reader, writer=writer))

    async def serve(self) -> None:
        server = await asyncio.start_server(
            self.handle,
            self.proxy_host,
            self.proxy_port,
        )
        async with server:
            await server.serve_forever()


class DatagramProxy(Proxy, asyncio.DatagramProtocol):
    transport: Optional[asyncio.DatagramTransport]

    def __init__(
            self,
            *,
            telemetry: DatagramTelemetry,
            tuning: DatagramTuning,
            proxy_host: str,
            proxy_port: int,
    ) -> None:
        self.transport = None
        self.telemetry = telemetry
        self.tuning = tuning
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.links = dict()

    def connection_made(self, transport) -> None:
        self.transport = transport

    async def datagram_received_async(self, *, data, addr) -> None:
        link = self.links.get(addr, DatagramLink(telemetry=self.telemetry, tuning=self.tuning, proxy=self, addr=addr))
        await link.process(data=data)

    def datagram_received(self, data, addr) -> None:
        asyncio.create_task(self.datagram_received_async(data=data, addr=addr))

    def error_received(self, exc) -> None:  # pragma: no cover
        logger.error(exc)

    def connection_lost(self, exc) -> None:
        self.transport.close()
        logger.error(exc)

    async def serve(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, local_addr=(self.proxy_host, self.proxy_port))
