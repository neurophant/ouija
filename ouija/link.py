import asyncio
import time
from typing import Dict, Tuple, Optional
import logging

from .packet import Packet, Phase
from .primitives import Sent, Received
from .telemetry import Telemetry
from .tuning import Tuning

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from proxy import Proxy


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class Link:
    telemetry: Telemetry
    __proxy: 'Proxy'
    __addr: Tuple[str, int]
    __tuning: Tuning
    __reader: Optional[asyncio.StreamReader]
    __writer: Optional[asyncio.StreamWriter]
    __remote_host: Optional[str]
    __remote_port: Optional[int]
    __opened: asyncio.Event
    __sent_buf: Dict[int, Sent]
    __sent_seq: int
    __read_closed: asyncio.Event
    __recv_buf: Dict[int, Received]
    __recv_seq: int
    __write_closed: asyncio.Event
    __stream_task: Optional[asyncio.Task]
    __finish_task: Optional[asyncio.Task]

    def __init__(self,  *, telemetry: Telemetry,  proxy: 'Proxy', addr: Tuple[str, int], tuning: Tuning) -> None:
        self.telemetry = telemetry
        self.__proxy = proxy
        self.__addr = addr
        self.__tuning = tuning
        self.__reader = None
        self.__writer = None
        self.__remote_host = None
        self.__remote_port = None
        self.__opened = asyncio.Event()
        self.__sent_buf = dict()
        self.__sent_seq = 0
        self.__read_closed = asyncio.Event()
        self.__recv_buf = dict()
        self.__recv_seq = 0
        self.__write_closed = asyncio.Event()
        self.__stream_task = None
        self.__finish_task = None

    async def __sendto(self, *, data: bytes) -> None:
        self.__proxy.transport.sendto(data, self.__addr)
        self.telemetry.packets_sent += 1
        self.telemetry.bytes_sent += len(data)
        if len(data) > self.telemetry.max_packet_size:
            self.telemetry.max_packet_size = len(data)

    async def __sendto_retry(self, *, data: bytes, event: asyncio.Event) -> bool:
        for _ in range(self.__tuning.retries):
            await self.__sendto(data=data)
            try:
                await asyncio.wait_for(event.wait(), self.__tuning.timeout)
            except asyncio.TimeoutError:
                self.telemetry.resent += 1
                continue
            else:
                return True
        else:
            return False

    async def __process(self, *, packet: Packet) -> None:
        match packet.phase:
            case Phase.OPEN:
                if packet.token != self.__tuning.token:
                    await self.__terminate()
                    self.telemetry.token_errors += 1
                    return

                if not self.__opened.is_set():
                    self.__remote_host = packet.host
                    self.__remote_port = packet.port

                    self.__reader, self.__writer = await asyncio.open_connection(self.__remote_host, self.__remote_port)
                    self.__opened.set()
                    self.__proxy.links[self.__addr] = self
                    loop = asyncio.get_event_loop()
                    self.__stream_task = loop.create_task(self._stream())
                    self.__finish_task = loop.create_task(self._finish())

                open_ack_packet = Packet(
                    phase=Phase.OPEN,
                    ack=True,
                    token=self.__tuning.token,
                    data=b'HTTP/1.1 200 Connection Established\r\n\r\n',
                )
                await self.__sendto(data=await open_ack_packet.binary(fernet=self.__tuning.fernet))
                self.telemetry.opened += 1
            case Phase.DATA:
                if not self.__opened.is_set() or self.__write_closed.is_set():
                    return

                if packet.ack:
                    self.__sent_buf.pop(packet.seq, None)
                else:
                    if packet.seq >= self.__recv_seq:
                        self.__recv_buf[packet.seq] = Received(data=packet.data)

                    for seq in sorted(self.__recv_buf.keys()):
                        if seq < self.__recv_seq:
                            self.__recv_buf.pop(seq)
                        if seq == self.__recv_seq:
                            self.__writer.write(self.__recv_buf.pop(seq).data)
                            await self.__writer.drain()
                            self.__recv_seq += 1

                    data_ack_packet = Packet(
                        phase=Phase.DATA,
                        ack=True,
                        seq=packet.seq,
                    )
                    await self.__sendto(data=await data_ack_packet.binary(fernet=self.__tuning.fernet))

                    if len(self.__recv_buf) >= self.__tuning.capacity:
                        await self.__terminate()
                        self.telemetry.recv_buf_overloads += 1
                        return
            case Phase.CLOSE:
                if packet.ack:
                    self.__read_closed.set()
                else:
                    close_ack_packet = Packet(
                        phase=Phase.CLOSE,
                        ack=True,
                    )
                    await self.__sendto(data=await close_ack_packet.binary(fernet=self.__tuning.fernet))
                    self.__write_closed.set()
            case _:
                self.telemetry.type_errors += 1

    async def process(self, *, packet: Packet) -> None:
        try:
            await self.__process(packet=packet)
        except ConnectionError:
            self.telemetry.connection_errors += 1
        except Exception as e:
            await self.__terminate()
            logger.error(e)
            self.telemetry.processing_errors += 1

    async def __finish(self) -> None:
        while self.__opened.is_set() or self.__sent_buf:
            await asyncio.sleep(self.__tuning.timeout)
            for seq in sorted(self.__sent_buf.keys()):
                delta = int(time.time()) - self.__sent_buf[seq].timestamp
                if delta >= self.__tuning.serving or self.__sent_buf[seq].retries >= self.__tuning.retries:
                    await self.__terminate()
                    self.telemetry.unfinished += 1
                    break
                if delta >= self.__tuning.timeout:
                    await self.__sendto(data=self.__sent_buf[seq].data)
                    self.__sent_buf[seq].retries += 1
                    self.telemetry.resent += 1

        close_packet = Packet(
            phase=Phase.CLOSE,
            ack=False,
        )
        await self.__sendto_retry(
            data=await close_packet.binary(fernet=self.__tuning.fernet),
            event=self.__read_closed,
        )

        try:
            await asyncio.wait_for(self.__write_closed.wait(), self.__tuning.serving)
        except asyncio.TimeoutError:
            pass

    async def _finish(self) -> None:
        try:
            await asyncio.wait_for(self.__finish(), self.__tuning.serving)
        except asyncio.TimeoutError:
            self.telemetry.timeout_errors += 1
        except Exception as e:
            logger.error(e)
            self.telemetry.finishing_errors += 1
        finally:
            await self.__terminate()

    async def __stream(self) -> None:
        while self.__opened.is_set():
            try:
                data = await asyncio.wait_for(self.__reader.read(self.__tuning.payload), self.__tuning.timeout)
            except TimeoutError:
                continue

            if not data:
                break

            data_packet = Packet(
                phase=Phase.DATA,
                ack=False,
                seq=self.__sent_seq,
                data=data,
            )
            binary = await data_packet.binary(fernet=self.__tuning.fernet)
            self.__sent_buf[self.__sent_seq] = Sent(data=binary)
            await self.__sendto(data=binary)
            self.__sent_seq += 1

            if len(self.__sent_buf) >= self.__tuning.capacity:
                await self.__terminate()
                self.telemetry.sent_buf_overloads += 1
                break

    async def _stream(self) -> None:
        try:
            await asyncio.wait_for(self.__stream(), self.__tuning.serving)
        except asyncio.TimeoutError:
            self.telemetry.timeout_errors += 1
        except ConnectionError:
            self.telemetry.connection_errors += 1
        except Exception as e:
            logger.error(e)
            self.telemetry.streaming_errors += 1

    async def __terminate(self) -> None:
        self.__opened.clear()
        self.__read_closed.set()
        self.__write_closed.set()
        if isinstance(self.__writer, asyncio.StreamWriter) and not self.__writer.is_closing():
            self.__writer.close()
            await self.__writer.wait_closed()
        self.__proxy.links.pop(self.__addr, None)
        self.telemetry.closed += 1
