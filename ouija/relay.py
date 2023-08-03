import asyncio
import logging

from .telemetry import Telemetry
from .tuning import Tuning
from .ouija import Ouija
from .packet import Packet


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


class Relay(Ouija, asyncio.DatagramProtocol):
    transport: asyncio.DatagramTransport
    proxy_host: str
    proxy_port: int

    def __init__(
            self, 
            *,
            telemetry: Telemetry,
            tuning: Tuning,
            reader: asyncio.StreamReader, 
            writer: asyncio.StreamWriter,
            proxy_host: str,
            proxy_port: int,
            remote_host: str,
            remote_port: int,
    ) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.reader = reader
        self.writer = writer
        self.wrote = 0
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.opened = asyncio.Event()
        self.sent_buf = dict()
        self.sent_seq = 0
        self.read_closed = asyncio.Event()
        self.recv_buf = dict()
        self.recv_seq = 0
        self.write_closed = asyncio.Event()

    def connection_made(self, transport) -> None:
        self.transport = transport

    async def _datagram_received_async(self, *, data, addr) -> None:
        self.telemetry.packets_received += 1
        self.telemetry.bytes_received += len(data)
        try:
            packet = await Packet.packet(data=data, fernet=self.tuning.fernet)
        except Exception as e:
            logger.error(e)
            self.telemetry.decoding_errors += 1
            return
        await self.process(packet=packet)

    def datagram_received(self, data, addr) -> None:
        asyncio.create_task(self._datagram_received_async(data=data, addr=addr))

    def error_received(self, exc) -> None:
        logger.error(exc)

    def connection_lost(self, exc) -> None:
        asyncio.create_task(self.close())

    async def sendto(self, *, data: bytes) -> None:
        self.transport.sendto(data)

    async def open(self, *, packet: Packet) -> bool:
        if not packet.ack or self.opened.is_set():
            return False

        await self.write(data=packet.data, drain=packet.drain)
        self.opened.set()
        return True

    async def handshake(self) -> bool:
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, remote_addr=(self.proxy_host, self.proxy_port))

        if not await self.send_open():
            return False

        return True

    async def close(self) -> None:
        if not self.transport.is_closing():
            self.transport.close()
