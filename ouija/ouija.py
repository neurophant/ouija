import asyncio
import time
from random import randrange
from typing import Optional

from .exception import TokenError, SendRetryError, BufOverloadError, OnOpenError, OnServeError
from .data import Message, SEPARATOR, Sent, Received, Packet, Phase
from .telemetry import Telemetry
from .tuning import StreamTuning, DatagramTuning
from .log import logger


class StreamOuija:
    """Core ouija class for TCP connector/link"""

    telemetry: Telemetry
    tuning: StreamTuning
    crypt: bool
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    remote_host: Optional[str]
    remote_port: Optional[int]
    target_reader: Optional[asyncio.StreamReader]
    target_writer: Optional[asyncio.StreamWriter]
    opened: asyncio.Event
    sync: asyncio.Event

    async def forward_wrapped(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, crypt: bool) -> None:
        while self.sync.is_set():
            try:
                data = await asyncio.wait_for(reader.read(self.tuning.tcp_buffer), self.tuning.tcp_timeout) if crypt \
                    else await asyncio.wait_for(reader.readuntil(SEPARATOR), self.tuning.message_timeout)
            except TimeoutError:
                continue
            except asyncio.IncompleteReadError:
                break

            if not data:
                break

            if not crypt:
                self.telemetry.recv(data=data, entropy=self.tuning.entropy)
            data = Message.encrypt(data=data, cipher=self.tuning.cipher, entropy=self.tuning.entropy) if crypt \
                else Message.decrypt(data=data, cipher=self.tuning.cipher, entropy=self.tuning.entropy)

            writer.write(data)
            await writer.drain()
            if crypt:
                self.telemetry.send(data=data, entropy=self.tuning.entropy)

        self.sync.clear()

    async def forward(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, crypt: bool) -> None:
        """Forward TCP stream with timeout
        :param reader: asyncio.StreamReader
        :param writer: asyncio.StreamWriter
        :param crypt: bool - on True decrypts read data, on False encrypts data before writing
        :returns: None"""

        try:
            await asyncio.wait_for(
                self.forward_wrapped(reader=reader, writer=writer, crypt=crypt),
                self.tuning.serving_timeout,
            )
        except TimeoutError:
            self.telemetry.timeout_error()
        except ConnectionError as e:
            logger.error(e)
            self.telemetry.connection_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.serving_error()

        await self.close()

    async def on_serve(self) -> None:
        """Hook - executed before serving, should raise TokenError/OnServeError if pre-serve failed
        :returns: None"""

        raise NotImplementedError

    async def serve_wrapped(self) -> None:
        await self.on_serve()
        self.opened.set()
        self.telemetry.open()

        self.sync.set()
        await asyncio.gather(
            self.forward(reader=self.reader, writer=self.target_writer, crypt=self.crypt),
            self.forward(reader=self.target_reader, writer=self.writer, crypt=not self.crypt),
        )

    async def serve(self) -> None:
        """Serve TCP streams with timeout
        :returns: None"""

        try:
            await asyncio.wait_for(self.serve_wrapped(), self.tuning.serving_timeout)
        except TokenError:
            self.telemetry.token_error()
        except OnServeError:
            pass
        except TimeoutError:
            self.telemetry.timeout_error()
        except ConnectionError as e:
            logger.error(e)
            self.telemetry.connection_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.serving_error()

        await self.close()

    async def on_close(self) -> None:
        """Hook - executed on close
        :returns: None"""

        raise NotImplementedError

    async def close(self) -> None:
        self.sync.clear()

        for writer in (self.target_writer, self.writer):
            if isinstance(writer, asyncio.StreamWriter) and not writer.is_closing():
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

        if self.opened.is_set():
            self.opened.clear()
            self.telemetry.close()
        await self.on_close()


class DatagramOuija:
    """Core ouija class for UDP connector/link"""

    telemetry: Telemetry
    tuning: DatagramTuning
    reader: Optional[asyncio.StreamReader]
    writer: Optional[asyncio.StreamWriter]
    remote_host: Optional[str]
    remote_port: Optional[int]
    opened: asyncio.Event
    sync: asyncio.Event
    sent_buf: dict[int, Sent]
    sent_seq: int
    read_closed: asyncio.Event
    recv_buf: dict[int, Received]
    recv_seq: int
    write_closed: asyncio.Event

    async def on_send(self, *, data: bytes) -> None:
        """Hook - send binary data via UDP
        :param data: binary data
        :returns: None"""

        raise NotImplementedError

    async def send(self, *, data: bytes) -> None:
        await self.on_send(data=data)
        self.telemetry.send(data=data, entropy=self.tuning.entropy)

    def packet_binary(self, *, packet: Packet) -> bytes:
        return packet.binary(cipher=self.tuning.cipher, entropy=self.tuning.entropy)

    async def send_packet(self, *, packet: Packet) -> None:
        await self.send(data=self.packet_binary(packet=packet))

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
        """Hook - process phase open packet, should raise OnOpenError if open failed
        :param packet: Packet
        :returns: None"""

        raise NotImplementedError

    async def process_wrapped(self, *, data: bytes) -> None:
        self.telemetry.recv(data=data, entropy=self.tuning.entropy)
        packet = Packet.packet(data=data, cipher=self.tuning.cipher, entropy=self.tuning.entropy)

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
            return
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

                if delta >= self.tuning.udp_timeout * self.tuning.udp_retries:
                    self.sent_buf.pop(seq, None)
                    continue

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
        """Hook - executed before serving, should raise OnServeError if pre-serve failed
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

            idx = 0
            while idx < len(data):
                c_len = randrange(self.tuning.udp_min_payload, self.tuning.udp_max_payload + 1)

                data_packet = Packet(
                    phase=Phase.DATA,
                    ack=False,
                    seq=self.sent_seq,
                    data=data[idx:idx + c_len],
                    drain=True if idx + c_len >= len(data) else False,
                )
                self.sent_buf[self.sent_seq] = Sent(data=self.packet_binary(packet=data_packet))
                await self.send_packet(packet=data_packet)
                self.sent_seq += 1
                idx += c_len

                if len(self.sent_buf) >= self.tuning.udp_capacity:
                    raise BufOverloadError

        self.sync.clear()

    async def serve(self) -> None:
        """Serve TCP stream with timeout
        :returns: None"""

        try:
            await asyncio.wait_for(self.serve_wrapped(), self.tuning.serving_timeout)
        except OnServeError:
            return
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
