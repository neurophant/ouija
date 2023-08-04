import asyncio
import os
from typing import Dict, Tuple
import logging

from .telemetry import Telemetry
from .tuning import Tuning
from .link import Link


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.ERROR,
)
logger = logging.getLogger(__name__)


class Proxy(asyncio.DatagramProtocol):
    transport: asyncio.DatagramTransport
    telemetry: Telemetry
    links: Dict[Tuple[str, int], Link]
    tuning: Tuning
    proxy_host: str
    proxy_port: int

    def __init__(self, *, telemetry: Telemetry, tuning: Tuning, proxy_host: str, proxy_port: int) -> None:
        self.links = dict()
        self.telemetry = telemetry
        self.tuning = tuning
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def connection_made(self, transport) -> None:
        self.transport = transport

    async def _datagram_received_async(self, *, data, addr) -> None:
        link = self.links.get(addr, Link(telemetry=self.telemetry, proxy=self, addr=addr, tuning=self.tuning))
        await link.process(data=data)

    def datagram_received(self, data, addr) -> None:
        asyncio.create_task(self._datagram_received_async(data=data, addr=addr))

    def error_received(self, exc) -> None:
        logger.error(exc)

    def connection_lost(self, exc) -> None:
        self.transport.close()
        logger.error(exc)

    async def serve(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, local_addr=(self.proxy_host, self.proxy_port))

    async def cleanup(self) -> None:
        while True:
            await asyncio.sleep(1)
            self.telemetry.links = len(self.links)

    async def monitor(self) -> None:
        while True:
            await asyncio.sleep(1)
            os.system('clear')
            print(self.telemetry)
