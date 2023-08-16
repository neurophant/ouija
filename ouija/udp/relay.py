import asyncio
from typing import Optional

from ..exception import OnOpenError, OnServeError, SendRetryError
from .telemetry import Telemetry
from .tuning import Tuning
from .ouija import Ouija
from .packet import Packet, Phase
from ..log import logger


class Relay(Ouija, asyncio.DatagramProtocol):
    transport: Optional[asyncio.DatagramTransport]
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
        self.transport = None
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

    async def on_open(self, *, packet: Packet) -> None:
        if not packet.ack or self.opened.is_set():
            raise OnOpenError

        self.writer.write(data=b'HTTP/1.1 200 Connection Established\r\n\r\n')
        await self.writer.drain()
        self.opened.set()

    async def on_serve(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, remote_addr=(self.proxy_host, self.proxy_port))

        open_packet = Packet(
            phase=Phase.OPEN,
            ack=False,
            token=self.tuning.token,
            host=self.remote_host,
            port=self.remote_port,
        )
        try:
            await self.send_retry(packet=open_packet, event=self.opened)
        except SendRetryError:
            raise OnServeError

    async def on_close(self) -> None:
        if isinstance(self.transport, asyncio.DatagramTransport) and not self.transport.is_closing():
            self.transport.close()
