import asyncio
import os
from typing import Optional

from .telemetry import Telemetry
from .tuning import Tuning
from .link import Link
from ..log import logger


class Proxy(asyncio.DatagramProtocol):
    transport: Optional[asyncio.DatagramTransport]
    telemetry: Telemetry
    links: dict[tuple[str, int], Link]
    tuning: Tuning
    proxy_host: str
    proxy_port: int

    def __init__(self, *, telemetry: Telemetry, tuning: Tuning, proxy_host: str, proxy_port: int) -> None:
        self.transport = None
        self.links = dict()
        self.telemetry = telemetry
        self.tuning = tuning
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def connection_made(self, transport) -> None:
        self.transport = transport

    async def datagram_received_async(self, *, data, addr) -> None:
        link = self.links.get(addr, Link(telemetry=self.telemetry, proxy=self, addr=addr, tuning=self.tuning))
        await link.process(data=data)

    def datagram_received(self, data, addr) -> None:
        asyncio.create_task(self.datagram_received_async(data=data, addr=addr))

    def error_received(self, exc) -> None:  # pragma: no cover
        logger.error(exc)

    def connection_lost(self, exc) -> None:
        self.transport.close()
        logger.error(exc)

    async def serve(self) -> None:
        """Proxy UDP server entry point
        :returns: None
        """

        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, local_addr=(self.proxy_host, self.proxy_port))

    async def debug(self) -> None:    # pragma: no cover
        """Debug monitor with telemetry output
        :returns: None
        """

        while True:
            await asyncio.sleep(1)
            self.telemetry.link(links=len(self.links))
            os.system('clear')
            print(self.telemetry)
