import asyncio
from typing import Tuple
import logging

from .packet import Packet
from .telemetry import Telemetry
from .tuning import Tuning
from .ouija import Ouija

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from proxy import Proxy


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG,
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
        self.telemetry.packets_sent += 1
        self.telemetry.bytes_sent += len(data)
        if len(data) > self.telemetry.max_packet_size:
            self.telemetry.max_packet_size = len(data)

    async def phase_open(self, *, packet: Packet) -> None:
        if not self.opened.is_set():
            self.remote_host = packet.host
            self.remote_port = packet.port

            self.reader, self.writer = await asyncio.open_connection(self.remote_host, self.remote_port)
            self.opened.set()
            self.proxy.links[self.addr] = self
            loop = asyncio.get_event_loop()
            loop.create_task(self.stream())
            loop.create_task(self.finish())
            self.telemetry.opened += 1

        await self.send_ack_open()

    async def handshake(self) -> bool:
        return True

    async def terminate(self) -> None:
        self.proxy.links.pop(self.addr, None)
