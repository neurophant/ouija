import asyncio
from typing import Optional

from .message import Message
from .telemetry import Telemetry
from .tuning import Tuning
from ..log import logger


class Relay:
    telemetry: Telemetry
    tuning: Tuning
    reader: Optional[asyncio.StreamReader]
    writer: Optional[asyncio.StreamWriter]
    proxy_host: str
    proxy_port: int
    remote_host: Optional[str]
    remote_port: Optional[int]
    target_reader: Optional[asyncio.StreamReader]
    target_writer: Optional[asyncio.StreamWriter]
    opened: asyncio.Event

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
        self.tuning = tuning
        self.reader = reader
        self.writer = writer
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.target_reader = None
        self.target_writer = None
        self.opened = asyncio.Event()

    async def forward_wrapped(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while self.opened.is_set():
            try:
                data = await asyncio.wait_for(reader.read(self.tuning.tcp_buffer), self.tuning.tcp_timeout)
            except TimeoutError:
                continue

            if not data:
                self.opened.clear()
                break

            writer.write(data)
            await writer.drain()

    async def forward(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await asyncio.wait_for(self.forward_wrapped(reader=reader, writer=writer), self.tuning.serving_timeout)
        except TimeoutError:
            self.telemetry.timeout_error()
        except ConnectionError as e:
            logger.error(e)
            self.telemetry.connection_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.serving_error()

        await self.close()

    async def serve_wrapped(self) -> None:
        self.target_reader, self.target_writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)

        message = Message(token=self.tuning.token, host=self.remote_host, port=self.remote_port)
        data = message.binary(fernet=self.tuning.fernet)
        self.target_writer.write(data)
        await self.target_writer.drain()

        data = await self.target_reader.read(len(data))
        message = Message.message(data=data, fernet=self.tuning.fernet)
        if message.token != self.tuning.token:
            return

        self.writer.write(data=b'HTTP/1.1 200 Connection Established\r\n\r\n')
        await self.writer.drain()

        self.opened.set()
        self.telemetry.open()

        await asyncio.gather(
            self.forward(reader=self.reader, writer=self.target_writer),
            self.forward(reader=self.target_reader, writer=self.writer),
        )

    async def serve(self) -> None:
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

        await self.close()

    async def close(self) -> None:
        if self.opened.is_set():
            self.opened.clear()
            self.telemetry.close()

        for writer in (self.target_writer, self.writer):
            if isinstance(writer, asyncio.StreamWriter) and not writer.is_closing():
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
