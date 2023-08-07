import asyncio
from typing import Tuple
import logging

from .packet import Packet
from .telemetry import Telemetry
from .tuning import Tuning
from .ouija import Ouija

from typing import TYPE_CHECKING
if TYPE_CHECKING:   # pragma: no cover
    from proxy import Proxy


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.ERROR,
)
logger = logging.getLogger(__name__)


class Link(Ouija):
    proxy: 'Proxy'
    addr: Tuple[str, int]

    def __init__(self,  *, telemetry: Telemetry,  proxy: 'Proxy', addr: Tuple[str, int], tuning: Tuning) -> None:
        self.telemetry = telemetry
        self.proxy = proxy
        self.addr = addr
        self.tuning = tuning
        self.reader = None
        self.writer = None
        self.remote_host = None
        self.remote_port = None
        self.opened = asyncio.Event()
        self.sent_buf = dict()
        self.sent_seq = 0
        self.read_closed = asyncio.Event()
        self.recv_buf = dict()
        self.recv_seq = 0
        self.write_closed = asyncio.Event()

    async def sendto(self, *, data: bytes) -> None:
        self.proxy.transport.sendto(data, self.addr)

    async def on_open(self, *, packet: Packet) -> bool:
        if self.opened.is_set():
            await self.send_ack_open()
            return False

        self.remote_host = packet.host
        self.remote_port = packet.port
        self.reader, self.writer = await asyncio.open_connection(self.remote_host, self.remote_port)
        self.opened.set()
        asyncio.create_task(self.serve())
        self.proxy.links[self.addr] = self
        await self.send_ack_open()
        return True

    async def on_serve(self) -> bool:
        return True     # pragma: no cover

    async def on_close(self) -> None:
        self.proxy.links.pop(self.addr, None)
