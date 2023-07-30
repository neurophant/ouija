import asyncio
import os
from typing import Dict, Tuple
import logging

from .packet import Packet
from .telemetry import Telemetry
from .tuning import Tuning
from .link import Link


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class Proxy(asyncio.DatagramProtocol):
    transport: asyncio.DatagramTransport
    telemetry: Telemetry
    links: Dict[Tuple[str, int], Link]
    __tuning: Tuning
    __proxy_host: str
    __proxy_port: int

    def __init__(self, *, telemetry: Telemetry, tuning: Tuning, proxy_host: str, proxy_port: int) -> None:
        self.links = dict()
        self.telemetry = telemetry
        self.__tuning = tuning
        self.__proxy_host = proxy_host
        self.__proxy_port = proxy_port

    def connection_made(self, transport) -> None:
        self.transport = transport

    def datagram_received(self, data, addr) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self.__datagram_received_async(data=data, addr=addr))

    def error_received(self, exc) -> None:
        logger.error(exc)

    def connection_lost(self, exc) -> None:
        self.transport.close()
        logger.error(exc)

    async def __datagram_received_async(self, *, data, addr) -> None:
        self.telemetry.packets_received += 1
        self.telemetry.bytes_received += len(data)
        try:
            packet = await Packet.packet(data=data, fernet=self.__tuning.fernet)
        except Exception as e:
            logger.error(e)
            self.telemetry.decoding_errors += 1
            return

        link = self.links.get(addr, Link(telemetry=self.telemetry, proxy=self, addr=addr, tuning=self.__tuning))
        await link.process(packet=packet)

    async def serve(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, local_addr=(self.__proxy_host, self.__proxy_port))

    async def cleanup(self) -> None:
        while True:
            await asyncio.sleep(1)
            self.telemetry.links = len(self.links)

    async def monitor(self) -> None:
        while True:
            await asyncio.sleep(1)
            os.system('clear')
            print(self.telemetry)
