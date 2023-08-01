import asyncio
import logging
import time
from typing import Dict, Optional

from .packet import Phase, Packet
from .primitives import Sent, Received
from .telemetry import Telemetry
from .tuning import Tuning


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


class Relay(asyncio.DatagramProtocol):
    transport: asyncio.DatagramTransport
    telemetry: Telemetry
    __tuning: Tuning
    __reader: asyncio.StreamReader
    __writer: asyncio.StreamWriter
    __wrote: int
    __proxy_host: str
    __proxy_port: int
    __remote_host: str
    __remote_port: int
    __opened: asyncio.Event
    __sent_buf: Dict[int, Sent]
    __sent_seq: int
    __read_closed: asyncio.Event
    __recv_buf: Dict[int, Received]
    __recv_seq: int
    __write_closed: asyncio.Event
    __finish_task: Optional[asyncio.Task]

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
        self.__tuning = tuning
        self.__reader = reader
        self.__writer = writer
        self.__wrote = 0
        self.__proxy_host = proxy_host
        self.__proxy_port = proxy_port
        self.__remote_host = remote_host
        self.__remote_port = remote_port
        self.__opened = asyncio.Event()
        self.__sent_buf = dict()
        self.__sent_seq = 0
        self.__read_closed = asyncio.Event()
        self.__recv_buf = dict()
        self.__recv_seq = 0
        self.__write_closed = asyncio.Event()
        self.__finish_task = None

    def connection_made(self, transport) -> None:
        self.transport = transport

    def datagram_received(self, data, addr) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self.__datagram_received_async(data=data, addr=addr))

    def error_received(self, exc) -> None:
        logger.error(exc)

    def connection_lost(self, exc) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self.__terminate())

    async def __sendto(self, *, data: bytes) -> None:
        self.transport.sendto(data)
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

    async def __datagram_received_async(self, *, data, addr) -> None:
        self.telemetry.packets_received += 1
        self.telemetry.bytes_received += len(data)
        try:
            packet = await Packet.packet(data=data, fernet=self.__tuning.fernet)
        except Exception as e:
            logger.error(e)
            self.telemetry.decoding_errors += 1
            return
        await self.process(packet=packet)

    async def __read(self) -> bytes:
        return await self.__reader.read(self.__tuning.buffer)

    async def __write(self, *, data: bytes) -> None:
        self.__writer.write(data)
        self.__wrote += len(data)
        await self.__drain()

    async def __drain(self, *, force: bool = False) -> None:
        if self.__wrote >= self.__tuning.buffer or force:
            await self.__writer.drain()
            self.__wrote = 0

    async def __recv(self, *, seq: int, data: bytes) -> None:
        if seq >= self.__recv_seq:
            self.__recv_buf[seq] = Received(data=data)

        for seq in sorted(self.__recv_buf.keys()):
            if seq < self.__recv_seq:
                self.__recv_buf.pop(seq)
            if seq == self.__recv_seq:
                await self.__write(data=self.__recv_buf.pop(seq).data)
                self.__recv_seq += 1

        await self.__send_ack_data(seq=seq)

        if len(self.__recv_buf) >= self.__tuning.capacity:
            await self.__terminate()
            self.telemetry.recv_buf_overloads += 1

    async def __enqueue_send(self, *, data: bytes) -> None:
        data_packet = Packet(
            phase=Phase.DATA,
            ack=False,
            seq=self.__sent_seq,
            data=data,
        )
        data_ = await data_packet.binary(fernet=self.__tuning.fernet)
        self.__sent_buf[self.__sent_seq] = Sent(data=data_)
        await self.__sendto(data=data_)
        self.__sent_seq += 1

        if len(self.__sent_buf) >= self.__tuning.capacity:
            await self.__terminate()
            self.telemetry.sent_buf_overloads += 1

    async def __dequeue_send(self, *, seq: int) -> None:
        self.__sent_buf.pop(seq, None)

    async def __send_open(self) -> bool:
        open_packet = Packet(
            phase=Phase.OPEN,
            ack=False,
            token=self.__tuning.token,
            host=self.__remote_host,
            port=self.__remote_port,
        )
        if not await self.__sendto_retry(
                data=await open_packet.binary(fernet=self.__tuning.fernet),
                event=self.__opened,
        ):
            return False

        return True

    async def __send_ack_open(self) -> None:
        open_ack_packet = Packet(
            phase=Phase.OPEN,
            ack=True,
            token=self.__tuning.token,
            data=b'HTTP/1.1 200 Connection Established\r\n\r\n',
        )
        await self.__sendto(data=await open_ack_packet.binary(fernet=self.__tuning.fernet))

    async def __check_token(self, *, token: str) -> bool:
        if token == self.__tuning.token:
            return True

        await self.__terminate()
        self.telemetry.token_errors += 1
        return False

    async def __send_ack_data(self, *, seq: int) -> None:
        data_ack_packet = Packet(
            phase=Phase.DATA,
            ack=True,
            seq=seq,
        )
        await self.__sendto(data=await data_ack_packet.binary(fernet=self.__tuning.fernet))

    async def __send_close(self) -> None:
        close_packet = Packet(
            phase=Phase.CLOSE,
            ack=False,
        )
        await self.__sendto_retry(
            data=await close_packet.binary(fernet=self.__tuning.fernet),
            event=self.__read_closed,
        )

    async def __send_ack_close(self) -> None:
        close_ack_packet = Packet(
            phase=Phase.CLOSE,
            ack=True,
        )
        await self.__sendto(data=await close_ack_packet.binary(fernet=self.__tuning.fernet))

    async def __process(self, *, packet: Packet) -> None:
        match packet.phase:
            case Phase.OPEN:
                if not await self.__check_token(token=packet.token):
                    return

                if packet.ack and not self.__opened.is_set():
                    await self.__write(data=packet.data)
                    await self.__drain(force=True)
                    self.__opened.set()
                    self.telemetry.opened += 1
            case Phase.DATA:
                if not self.__opened.is_set() or self.__write_closed.is_set():
                    return

                if packet.ack:
                    await self.__dequeue_send(seq=packet.seq)
                else:
                    await self.__recv(seq=packet.seq, data=packet.data)
            case Phase.CLOSE:
                if packet.ack:
                    self.__read_closed.set()
                else:
                    await self.__drain(force=True)
                    await self.__send_ack_close()
                    self.__write_closed.set()
            case _:
                self.telemetry.type_errors += 1

    async def process(self, *, packet: Packet) -> None:
        try:
            await self.__process(packet=packet)
        except ConnectionError as e:
            logger.error(e)
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

        await self.__send_close()

        try:
            await asyncio.wait_for(self.__write_closed.wait(), self.__tuning.serving)
        except asyncio.TimeoutError:
            pass

    async def _finish(self) -> None:
        try:
            await asyncio.wait_for(self.__finish(), self.__tuning.serving)
        except asyncio.TimeoutError as e:
            logger.error(e)
            self.telemetry.timeout_errors += 1
        except Exception as e:
            logger.error(e)
            self.telemetry.finishing_errors += 1
        finally:
            await self.__terminate()

    async def __stream(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, remote_addr=(self.__proxy_host, self.__proxy_port))

        if not await self.__send_open():
            return

        self.__finish_task = loop.create_task(self._finish())

        while self.__opened.is_set():
            try:
                data = await asyncio.wait_for(self.__read(), self.__tuning.timeout)
            except TimeoutError:
                continue

            if not data:
                break

            for idx in range(0, len(data), self.__tuning.payload):
                await self.__enqueue_send(data=data[idx:idx + self.__tuning.payload])

    async def stream(self) -> None:
        try:
            await asyncio.wait_for(self.__stream(), self.__tuning.serving)
        except asyncio.TimeoutError:
            self.telemetry.timeout_errors += 1
        except ConnectionError as e:
            logger.error(e)
            self.telemetry.connection_errors += 1
        except Exception as e:
            logger.error(e)
            self.telemetry.streaming_errors += 1

    async def __terminate(self) -> None:
        self.__opened.clear()
        self.__read_closed.set()
        self.__write_closed.set()

        if isinstance(self.__writer, asyncio.StreamWriter) and not self.__writer.is_closing():
            await self.__drain(force=True)
            self.__writer.close()
            await self.__writer.wait_closed()

        if not self.transport.is_closing():
            self.transport.close()

        self.telemetry.closed += 1
