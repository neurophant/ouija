import asyncio
import uuid

from .exception import TokenError, OnOpenError, OnServeError
from .data import Message, SEPARATOR, Packet, Phase
from .ouija import StreamOuija, DatagramOuija
from .telemetry import StreamTelemetry, DatagramTelemetry
from .tuning import StreamTuning, DatagramTuning

from typing import TYPE_CHECKING
if TYPE_CHECKING:   # pragma: no cover
    from .proxy import StreamProxy, DatagramProxy


class StreamLink(StreamOuija):
    proxy: 'StreamProxy'
    uid: str

    def __init__(
            self,
            *,
            telemetry: StreamTelemetry,
            tuning: StreamTuning,
            proxy: 'StreamProxy',
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.proxy = proxy
        self.uid = uuid.uuid4().hex
        self.crypt = False
        self.reader = reader
        self.writer = writer
        self.remote_host = None
        self.remote_port = None
        self.target_reader = None
        self.target_writer = None
        self.opened = asyncio.Event()
        self.sync = asyncio.Event()

    async def on_serve(self) -> None:
        try:
            data = await asyncio.wait_for(self.reader.readuntil(SEPARATOR), self.tuning.message_timeout)
        except (TimeoutError, asyncio.IncompleteReadError):
            raise OnServeError

        message = Message.message(data=data, fernet=self.tuning.fernet)
        if message.token != self.tuning.token:
            raise TokenError

        self.remote_host = message.host
        self.remote_port = message.port
        self.target_reader, self.target_writer = await asyncio.open_connection(self.remote_host, self.remote_port)

        message = Message(token=self.tuning.token)
        data = message.binary(fernet=self.tuning.fernet)
        self.writer.write(data)
        await self.writer.drain()

        self.proxy.links[self.uid] = self

    async def on_close(self) -> None:
        self.proxy.links.pop(self.uid, None)


class DatagramLink(DatagramOuija):
    proxy: 'DatagramProxy'
    addr: tuple[str, int]

    def __init__(
            self,
            *,
            telemetry: DatagramTelemetry,
            tuning: DatagramTuning,
            proxy: 'DatagramProxy',
            addr: tuple[str, int],
    ) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.proxy = proxy
        self.addr = addr
        self.reader = None
        self.writer = None
        self.remote_host = None
        self.remote_port = None
        self.opened = asyncio.Event()
        self.sync = asyncio.Event()
        self.sent_buf = dict()
        self.sent_seq = 0
        self.read_closed = asyncio.Event()
        self.recv_buf = dict()
        self.recv_seq = 0
        self.write_closed = asyncio.Event()

    async def on_send(self, *, data: bytes) -> None:
        self.proxy.transport.sendto(data, self.addr)

    async def on_open(self, *, packet: Packet) -> None:
        if not packet.host or not packet.port:
            raise OnOpenError

        open_ack_packet = Packet(
            phase=Phase.OPEN,
            ack=True,
            token=self.tuning.token,
        )
        if self.opened.is_set():
            await self.send_packet(packet=open_ack_packet)
            raise OnOpenError

        self.remote_host = packet.host
        self.remote_port = packet.port
        self.reader, self.writer = await asyncio.open_connection(self.remote_host, self.remote_port)
        self.opened.set()
        asyncio.create_task(self.serve())
        self.proxy.links[self.addr] = self
        await self.send_packet(packet=open_ack_packet)

    async def on_serve(self) -> None:   # pragma: no cover
        pass

    async def on_close(self) -> None:
        self.proxy.links.pop(self.addr, None)
