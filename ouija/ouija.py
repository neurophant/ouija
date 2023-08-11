import asyncio
import time
from typing import Optional, Dict

from .exception import OnOpenError, TokenError, BufOverloadError, OnServeError, SendRetryError
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

    async def send_retry(self, *, packet: Packet, event: asyncio.Event) -> None:
        for _ in range(self.tuning.udp_retries):
            await self.send_packet(packet=packet)

            try:
                await asyncio.wait_for(event.wait(), self.tuning.udp_timeout)
            except TimeoutError:
                continue
            else:
                return

        raise SendRetryError

    async def on_open(self, packet: Packet) -> None:
        """Hook - process phase open packet, on fail should raise OnOpenError
        :param packet: Packet
        :returns: None"""

        raise NotImplementedError

    async def process_wrapped(self, *, data: bytes) -> None:
        self.telemetry.recv(data=data)
        packet = Packet.packet(data=data, fernet=self.tuning.fernet)

        match packet.phase:
            case Phase.OPEN:
                if packet.token != self.tuning.token:
                    raise TokenError

                await self.on_open(packet=packet)
                self.telemetry.open()
            case Phase.DATA:
                if not self.opened.is_set():
                    return

                if packet.ack:
                    self.sent_buf.pop(packet.seq, None)
                else:
                    data_ack_packet = Packet(
                        phase=Phase.DATA,
                        ack=True,
                        seq=packet.seq,
                    )
                    await self.send_packet(packet=data_ack_packet)

                    if self.write_closed.is_set():
                        return

                    if packet.seq >= self.recv_seq:
                        self.recv_buf[packet.seq] = Received(data=packet.data, drain=packet.drain)

                    for seq in sorted(self.recv_buf.keys()):
                        if seq != self.recv_seq:
                            continue

                        recv = self.recv_buf.pop(seq)
                        self.writer.write(recv.data)
                        if recv.drain:
                            await self.writer.drain()
                        self.recv_seq += 1

                    if len(self.recv_buf) >= self.tuning.udp_capacity:
                        raise BufOverloadError
            case Phase.CLOSE:
                if not self.opened.is_set():
                    return

                if packet.ack:
                    self.read_closed.set()
                else:
                    self.write_closed.set()
                    close_ack_packet = Packet(
                        phase=Phase.CLOSE,
                        ack=True,
                    )
                    await self.send_packet(packet=close_ack_packet)
            case _:     # pragma: no cover
                pass

    async def process(self, *, data: bytes) -> None:
        """Decode and process packet
        :param data: binary packet
        :returns: None"""

        try:
            await self.process_wrapped(data=data)
        except TokenError:
            self.telemetry.token_error()
        except OnOpenError:
            pass
        except BufOverloadError:
            self.telemetry.recv_buf_overload()
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
                sent = self.sent_buf[seq]
                delta = time.time() - sent.timestamp

                if delta >= self.tuning.serving_timeout or sent.retries >= self.tuning.udp_retries:
                    break

                if delta >= self.tuning.udp_timeout * sent.retries:
                    await self.send(data=sent.data)
                    sent.retries += 1

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

    async def on_serve(self) -> None:
        """Hook - executed before serving, on fail should raise OnServeError
        :returns: None"""

        raise NotImplementedError

    async def serve_wrapped(self) -> None:
        await self.on_serve()

        self.sync.set()
        asyncio.create_task(self.resend())

        while self.sync.is_set():
            try:
                data = await asyncio.wait_for(self.reader.read(self.tuning.tcp_buffer), self.tuning.tcp_timeout)
            except TimeoutError:
                continue

            if not data:
                break

            for idx in range(0, len(data), self.tuning.udp_payload):
                data_packet = Packet(
                    phase=Phase.DATA,
                    ack=False,
                    seq=self.sent_seq,
                    data=data[idx:idx + self.tuning.udp_payload],
                    drain=True if len(data) - idx <= self.tuning.udp_payload else False,
                )
                self.sent_buf[self.sent_seq] = Sent(data=await self.send_packet(packet=data_packet))
                self.sent_seq += 1

                if len(self.sent_buf) >= self.tuning.udp_capacity:
                    raise BufOverloadError

        self.sync.clear()

    async def serve(self) -> None:
        """Serve TCP stream with timeout
        :returns: None"""

        try:
            await asyncio.wait_for(self.serve_wrapped(), self.tuning.serving_timeout)
        except OnServeError:
            pass
        except BufOverloadError:
            self.telemetry.send_buf_overload()
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

    async def close(self) -> None:
        self.sync.clear()

        if not self.read_closed.is_set():
            try:
                close_packet = Packet(
                    phase=Phase.CLOSE,
                    ack=False,
                )
                await self.send_retry(packet=close_packet, event=self.read_closed)
            except Exception:
                pass
            self.read_closed.set()

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

        if self.opened.is_set():
            self.opened.clear()
            self.telemetry.close()
        await self.on_close()
