import asyncio
import uuid
from typing import Optional

from .exception import TokenError, OnOpenError, SendRetryError, OnServeError
from .data import Message, SEPARATOR, CONNECTION_ESTABLISHED, Packet, Phase
from .log import logger
from .ouija import StreamOuija, DatagramOuija
from .telemetry import StreamTelemetry, DatagramTelemetry
from .tuning import StreamTuning, DatagramTuning

from typing import TYPE_CHECKING
if TYPE_CHECKING:   # pragma: no cover
    from .relay import StreamRelay, DatagramRelay


class StreamConnector(StreamOuija):
    relay: 'StreamRelay'
    uid: str
    proxy_host: str
    proxy_port: int
    https: bool

    def __init__(
            self,
            *,
            telemetry: StreamTelemetry,
            tuning: StreamTuning,
            relay: 'StreamRelay',
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            proxy_host: str,
            proxy_port: int,
            remote_host: str,
            remote_port: int,
            https: bool,
    ) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.relay = relay
        self.uid = uuid.uuid4().hex
        self.crypt = True
        self.reader = reader
        self.writer = writer
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.https = https
        self.target_reader = None
        self.target_writer = None
        self.opened = asyncio.Event()
        self.sync = asyncio.Event()

    async def on_serve(self) -> None:
        self.target_reader, self.target_writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)

        message = Message(token=self.tuning.token, host=self.remote_host, port=self.remote_port)
        data = message.binary(cipher=self.tuning.cipher, entropy=self.tuning.entropy)
        self.target_writer.write(data)
        await self.target_writer.drain()

        try:
            data = await asyncio.wait_for(self.target_reader.readuntil(SEPARATOR), self.tuning.message_timeout)
        except (TimeoutError, asyncio.IncompleteReadError):
            raise OnServeError

        message = Message.message(data=data, cipher=self.tuning.cipher, entropy=self.tuning.entropy)
        if message.token != self.tuning.token:
            raise TokenError

        if self.https:
            self.writer.write(data=CONNECTION_ESTABLISHED)
            await self.writer.drain()

        self.relay.connectors[self.uid] = self

    async def on_close(self) -> None:
        self.relay.connectors.pop(self.uid, None)


class DatagramConnector(DatagramOuija, asyncio.DatagramProtocol):
    transport: Optional[asyncio.DatagramTransport]
    relay: 'DatagramRelay'
    uid: str
    proxy_host: str
    proxy_port: int
    https: bool

    def __init__(
            self,
            *,
            telemetry: DatagramTelemetry,
            tuning: DatagramTuning,
            relay: 'DatagramRelay',
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            proxy_host: str,
            proxy_port: int,
            remote_host: str,
            remote_port: int,
            https: bool,
    ) -> None:
        self.transport = None
        self.telemetry = telemetry
        self.tuning = tuning
        self.relay = relay
        self.uid = uuid.uuid4().hex
        self.reader = reader
        self.writer = writer
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.https = https
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

        if self.https:
            self.writer.write(data=CONNECTION_ESTABLISHED)
            await self.writer.drain()

        self.opened.set()
        self.relay.connectors[self.uid] = self

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
        self.relay.connectors.pop(self.uid, None)
