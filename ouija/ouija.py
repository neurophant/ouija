import asyncio
import time
from typing import Optional, Dict

from .telemetry import Telemetry
from .tuning import Tuning
from .packet import Phase, Packet, Sent, Received
from .log import logger


class Ouija:
    telemetry: Telemetry
    tuning: Tuning
    reader: Optional[asyncio.StreamReader]
    writer: Optional[asyncio.StreamWriter]
    remote_host: Optional[str]
    remote_port: Optional[int]
    opened: asyncio.Event
    sync: asyncio.Event
    sent_buf: Dict[int, Sent]
    sent_seq: int
    read_closed: asyncio.Event
    recv_buf: Dict[int, Received]
    recv_seq: int
    write_closed: asyncio.Event

    async def on_send(self, *, data: bytes) -> None:
        """Hook - send binary data via UDP

        :param data: binary data
        :returns: None"""
        raise NotImplementedError

    async def send(self, *, data: bytes) -> None:
        await self.on_send(data=data)
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
            except TimeoutError:
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

    async def recv_data(self, *, packet: Packet) -> None:
        if packet.seq >= self.recv_seq:
            self.recv_buf[packet.seq] = Received(data=packet.data, drain=packet.drain)

        for seq in sorted(self.recv_buf.keys()):
            if seq != self.recv_seq:
                continue

            recv = self.recv_buf.pop(seq)
            await self.write(data=recv.data, drain=recv.drain)
            self.recv_seq += 1

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
        """Hook - process phase open packet

        :param packet: Packet
        :returns: True on opened link, False on fail"""
        raise NotImplementedError

    async def process_wrapped(self, *, data: bytes) -> None:
        self.telemetry.recv(data=data)
        packet = Packet.packet(data=data, fernet=self.tuning.fernet)

        match packet.phase:
            case Phase.OPEN:
                if packet.token != self.tuning.token:
                    await self.close()
                    self.telemetry.token_error()
                    return

                if not await self.on_open(packet=packet):
                    return

                self.telemetry.open()
            case Phase.DATA:
                if not self.opened.is_set():
                    return

                if packet.ack:
                    await self.dequeue_send(seq=packet.seq)
                else:
                    await self.send_ack_data(seq=packet.seq)
                    if self.write_closed.is_set():
                        return
                    await self.recv_data(packet=packet)
            case Phase.CLOSE:
                if not self.opened.is_set():
                    return

                if packet.ack:
                    self.read_closed.set()
                else:
                    self.write_closed.set()
                    await self.send_ack_close()
            case _:     # pragma: no cover
                pass

    async def process(self, *, data: bytes) -> None:
        """Decode and process packet

        :param data: binary packet
        :returns: None"""
        try:
            await self.process_wrapped(data=data)
        except ConnectionError as e:
            logger.error(e)
            self.telemetry.connection_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.processing_error()
        else:
            return

        await self.close()

    async def resend_wrapped(self) -> None:
        while self.sync.is_set() or self.sent_buf:
            await asyncio.sleep(self.tuning.udp_resend_sleep)
            for seq in sorted(self.sent_buf.keys()):
                delta = int(time.time()) - self.sent_buf[seq].timestamp

                if delta >= self.tuning.serving_timeout or self.sent_buf[seq].retries >= self.tuning.udp_retries:
                    break

                if delta >= self.tuning.udp_timeout:
                    await self.send(data=self.sent_buf[seq].data)
                    self.sent_buf[seq].retries += 1
        self.sync.clear()

    async def resend(self) -> None:
        try:
            await asyncio.wait_for(self.resend_wrapped(), self.tuning.serving_timeout)
        except TimeoutError:
            self.telemetry.timeout_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.resending_error()

        await self.close()

    async def on_serve(self) -> bool:
        """Hook - executed before serving

        :returns: True - start serving, False - return"""
        raise NotImplementedError

    async def serve_wrapped(self) -> None:
        if not await self.on_serve():
            return

        self.sync.set()
        asyncio.create_task(self.resend())

        while self.sync.is_set():
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
        self.sync.clear()

    async def serve(self) -> None:
        """Serve TCP stream with timeout

        :returns: None"""
        try:
            await asyncio.wait_for(self.serve_wrapped(), self.tuning.serving_timeout)
        except TimeoutError:
            self.telemetry.timeout_error()
        except ConnectionError as e:
            logger.error(e)
            self.telemetry.connection_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.serving_error()
        else:
            return

        await self.close()

    async def on_close(self) -> None:
        """Hook - executed on close

        :returns: None"""
        raise NotImplementedError

    async def read_close(self) -> None:
        if not self.read_closed.is_set():
            try:
                await self.send_close()
            except Exception:
                pass
            self.read_closed.set()

    async def write_close(self) -> None:
        if not self.write_closed.is_set():
            try:
                await asyncio.wait_for(self.write_closed.wait(), self.tuning.serving_timeout)
            except Exception:
                pass
            self.write_closed.set()

        if isinstance(self.writer, asyncio.StreamWriter) and not self.writer.is_closing():
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

    async def close(self) -> None:
        self.sync.clear()
        await self.read_close()
        await self.write_close()
        if self.opened.is_set():
            self.opened.clear()
            self.telemetry.close()
        await self.on_close()
