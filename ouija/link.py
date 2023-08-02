import asyncio
from typing import Tuple
import logging

from .packet import Packet, Phase
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

    async def _process(self, *, packet: Packet) -> None:
        match packet.phase:
            case Phase.OPEN:
                if not await self.check_token(token=packet.token):
                    return

                if not self.opened.is_set():
                    self.remote_host = packet.host
                    self.remote_port = packet.port

                    self.reader, self.writer = await asyncio.open_connection(self.remote_host, self.remote_port)
                    self.opened.set()
                    self.proxy.links[self.addr] = self
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.stream())
                    loop.create_task(self.finish())

                await self.send_ack_open()
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
        self.proxy.links.pop(self.addr, None)
