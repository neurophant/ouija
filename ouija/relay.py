import asyncio

from .telemetry import Telemetry
from .tuning import Tuning
from .ouija import Ouija
from .packet import Packet
from .log import logger


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
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.opened = asyncio.Event()
        self.sync = asyncio.Event()
        self.sent_buf = dict()
        self.sent_seq = 0
        self.read_closed = asyncio.Event()
        self.recv_buf = dict()
        self.recv_seq = 0
        self.write_closed = asyncio.Event()

    def connection_made(self, transport) -> None:
        self.transport = transport

    async def datagram_received_async(self, *, data, addr) -> None:
        await self.process(data=data)

    def datagram_received(self, data, addr) -> None:
        asyncio.create_task(self.datagram_received_async(data=data, addr=addr))

    def error_received(self, exc) -> None:
        logger.error(exc)   # pragma: no cover

    def connection_lost(self, exc) -> None:
        asyncio.create_task(self.close())

    async def on_send(self, *, data: bytes) -> None:
        self.transport.sendto(data)

    async def on_open(self, *, packet: Packet) -> bool:
        if not packet.ack or self.opened.is_set():
            return False

        await self.write(data=b'HTTP/1.1 200 Connection Established\r\n\r\n', drain=True)
        self.opened.set()
        return True

    async def on_serve(self) -> bool:
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, remote_addr=(self.proxy_host, self.proxy_port))

        if not await self.send_open():
            return False

        return True

    async def on_close(self) -> None:
        if not self.transport.is_closing():
            self.transport.close()
