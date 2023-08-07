import asyncio
import logging
import time
from typing import Optional, Dict

from .telemetry import Telemetry
from .tuning import Tuning
from .packet import Phase, Packet, Sent, Received


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.ERROR,
)
logger = logging.getLogger(__name__)


class Ouija:
    telemetry: Telemetry
    tuning: Tuning
    reader: Optional[asyncio.StreamReader]
    writer: Optional[asyncio.StreamWriter]
    remote_host: Optional[str]
    remote_port: Optional[int]
    opened: asyncio.Event
    sent_buf: Dict[int, Sent]
    sent_seq: int
    read_closed: asyncio.Event
    recv_buf: Dict[int, Received]
    recv_seq: int
    write_closed: asyncio.Event

    async def sendto(self, *, data: bytes) -> None:
        raise NotImplementedError

    async def send(self, *, data: bytes) -> None:
        await self.sendto(data=data)
        self.telemetry.send(data=data)

    async def send_packet(self, *, packet: Packet) -> bytes:
        data = packet.binary(fernet=self.tuning.fernet)
        await self.send(data=data)
        return data

    async def send_retry(self, *, packet: Packet, event: asyncio.Event) -> bool:
        for _ in range(self.tuning.udp_retries):
            await self.send_packet(packet=packet)
            try:
                await asyncio.wait_for(event.wait(), self.tuning.udp_timeout)
            except asyncio.TimeoutError:
                continue
            else:
                return True
        else:
            return False

    async def read(self) -> bytes:
        return await self.reader.read(self.tuning.tcp_buffer)

    async def write(self, *, data: bytes, drain: bool) -> None:
        self.writer.write(data)
        if drain:
            await self.writer.drain()

    async def recv(self, *, seq: int, data: bytes, drain: bool) -> None:
        if seq >= self.recv_seq:
            self.recv_buf[seq] = Received(data=data, drain=drain)

        for seq in sorted(self.recv_buf.keys()):
            if seq < self.recv_seq:
                self.recv_buf.pop(seq)
            if seq == self.recv_seq:
                recv = self.recv_buf.pop(seq)
                await self.write(data=recv.data, drain=recv.drain)
                self.recv_seq += 1

        await self.send_ack_data(seq=seq)

        if len(self.recv_buf) >= self.tuning.udp_capacity:
            await self.close()
            self.telemetry.recv_buf_overload()

    async def enqueue_send(self, *, data: bytes, drain: bool) -> None:
        data_packet = Packet(
            phase=Phase.DATA,
            ack=False,
            seq=self.sent_seq,
            data=data,
            drain=drain,
        )
        self.sent_buf[self.sent_seq] = Sent(data=await self.send_packet(packet=data_packet))
        self.sent_seq += 1

        if len(self.sent_buf) >= self.tuning.udp_capacity:
            await self.close()
            self.telemetry.send_buf_overload()

    async def dequeue_send(self, *, seq: int) -> None:
        self.sent_buf.pop(seq, None)

    async def send_open(self) -> bool:
        open_packet = Packet(
            phase=Phase.OPEN,
            ack=False,
            token=self.tuning.token,
            host=self.remote_host,
            port=self.remote_port,
        )
        if not await self.send_retry(packet=open_packet, event=self.opened):
            return False

        return True

    async def send_ack_open(self) -> None:
        open_ack_packet = Packet(
            phase=Phase.OPEN,
            ack=True,
            token=self.tuning.token,
        )
        await self.send_packet(packet=open_ack_packet)

    async def check_token(self, *, token: str) -> bool:
        if token == self.tuning.token:
            return True

        await self.close()
        self.telemetry.token_error()
        return False

    async def send_ack_data(self, *, seq: int) -> None:
        data_ack_packet = Packet(
            phase=Phase.DATA,
            ack=True,
            seq=seq,
        )
        await self.send_packet(packet=data_ack_packet)

    async def send_close(self) -> None:
        close_packet = Packet(
            phase=Phase.CLOSE,
            ack=False,
        )
        await self.send_retry(packet=close_packet, event=self.read_closed)

    async def send_ack_close(self) -> None:
        close_ack_packet = Packet(
            phase=Phase.CLOSE,
            ack=True,
        )
        await self.send_packet(packet=close_ack_packet)

    async def on_open(self, packet: Packet) -> bool:
        raise NotImplementedError

    async def process_packet(self, *, data: bytes) -> None:
        self.telemetry.recv(data=data)
        packet = Packet.packet(data=data, fernet=self.tuning.fernet)

        match packet.phase:
            case Phase.OPEN:
                if not await self.check_token(token=packet.token):
                    return

                if not await self.on_open(packet=packet):
                    return

                self.telemetry.open()
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
                self.telemetry.type_error()

    async def process(self, *, data: bytes) -> None:
        try:
            await self.process_packet(data=data)
        except ConnectionError as e:
            logger.error(e)
            self.telemetry.connection_error()
        except Exception as e:
            await self.close()
            logger.error(e)
            self.telemetry.processing_error()

    async def resend_packets(self) -> None:
        while self.opened.is_set() or self.sent_buf:
            await asyncio.sleep(self.tuning.udp_timeout)

            for seq in sorted(self.sent_buf.keys()):
                delta = int(time.time()) - self.sent_buf[seq].timestamp

                if delta >= self.tuning.serving_timeout or self.sent_buf[seq].retries >= self.tuning.udp_retries:
                    await self.close()
                    return

                if delta >= self.tuning.udp_timeout:
                    await self.send(data=self.sent_buf[seq].data)
                    self.sent_buf[seq].retries += 1

        await self.send_close()

        try:
            await asyncio.wait_for(self.write_closed.wait(), self.tuning.serving_timeout)
        except asyncio.TimeoutError:
            pass

    async def resend(self) -> None:
        try:
            await asyncio.wait_for(self.resend_packets(), self.tuning.serving_timeout)
        except asyncio.TimeoutError:
            self.telemetry.timeout_error()
        except Exception as e:
            logger.error(e)
            self.telemetry.resending_error()
        finally:
            await self.close()

    async def on_serve(self) -> bool:
        raise NotImplementedError

    async def serve_stream(self) -> None:
        if not await self.on_serve():
            return

        asyncio.create_task(self.resend())

        while self.opened.is_set():
            try:
                data = await asyncio.wait_for(self.read(), self.tuning.tcp_timeout)
            except TimeoutError:
                continue

            if not data:
                break

            for idx in range(0, len(data), self.tuning.udp_payload):
                await self.enqueue_send(
                    data=data[idx:idx + self.tuning.udp_payload],
                    drain=True if len(data) - idx <= self.tuning.udp_payload else False,
                )

    async def serve(self) -> None:
        try:
            await asyncio.wait_for(self.serve_stream(), self.tuning.serving_timeout)
        except asyncio.TimeoutError:
            self.telemetry.timeout_error()
        except ConnectionError as e:
            logger.error(e)
            self.telemetry.connection_error()
        except Exception as e:
            logger.error(e)
            self.telemetry.serving_error()

    async def on_close(self) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        if self.opened.is_set():
            self.telemetry.close()

        self.opened.clear()
        self.read_closed.set()
        self.write_closed.set()

        if isinstance(self.writer, asyncio.StreamWriter) and not self.writer.is_closing():
            self.writer.close()
            await self.writer.wait_closed()

        await self.on_close()
