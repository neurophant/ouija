import asyncio
import logging

from .telemetry import Telemetry
from .tuning import Tuning
from .ouija import Ouija
from .packet import Phase, Packet


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
        loop = asyncio.get_event_loop()
        loop.create_task(self._datagram_received_async(data=data, addr=addr))

    def error_received(self, exc) -> None:
        logger.error(exc)

    def connection_lost(self, exc) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self.terminate())

    async def sendto(self, *, data: bytes) -> None:
        self.transport.sendto(data)
        self.telemetry.packets_sent += 1
        self.telemetry.bytes_sent += len(data)
        if len(data) > self.telemetry.max_packet_size:
            self.telemetry.max_packet_size = len(data)

    async def _process(self, *, packet: Packet) -> None:
        match packet.phase:
            case Phase.OPEN:
                if not await self.check_token(token=packet.token):
                    return

                if packet.ack and not self.opened.is_set():
                    await self.write(data=packet.data, drain=packet.drain)
                    self.opened.set()
                    self.telemetry.opened += 1
            case Phase.DATA:
                if not self.opened.is_set() or self.write_closed.is_set():
                    return

                if packet.ack:
                    await self.dequeue_send(seq=packet.seq)
                else:
                    await self.recv(seq=packet.seq, data=packet.data, drain=packet.drain)
            case Phase.CLOSE:
                if packet.ack:
                    self.read_closed.set()
                else:
                    await self.send_ack_close()
                    self.write_closed.set()
            case _:
                self.telemetry.type_errors += 1

    async def _stream(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, remote_addr=(self.proxy_host, self.proxy_port))

        if not await self.send_open():
            return

        loop.create_task(self.finish())

        while self.opened.is_set():
            try:
                data = await asyncio.wait_for(self.read(), self.tuning.timeout)
            except TimeoutError:
                continue

            if not data:
                break

            for idx in range(0, len(data), self.tuning.payload):
                await self.enqueue_send(
                    data=data[idx:idx + self.tuning.payload],
                    drain=True if len(data) - idx <= self.tuning.payload else False,
                )

    async def _terminate(self) -> None:
        if not self.transport.is_closing():
            self.transport.close()
