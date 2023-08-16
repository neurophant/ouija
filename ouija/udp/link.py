import asyncio

from ..exception import OnOpenError
from .packet import Packet, Phase
from .telemetry import Telemetry
from .tuning import Tuning
from .ouija import Ouija

from typing import TYPE_CHECKING
if TYPE_CHECKING:   # pragma: no cover
    from proxy import Proxy


class Link(Ouija):
    proxy: 'Proxy'
    addr: tuple[str, int]

    def __init__(self,  *, telemetry: Telemetry,  proxy: 'Proxy', addr: tuple[str, int], tuning: Tuning) -> None:
        self.telemetry = telemetry
        self.proxy = proxy
        self.addr = addr
        self.tuning = tuning
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
        return

    async def on_serve(self) -> None:   # pragma: no cover
        pass

    async def on_close(self) -> None:
        self.proxy.links.pop(self.addr, None)
