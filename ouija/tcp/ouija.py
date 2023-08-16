import asyncio
from enum import IntEnum
from typing import Optional

from .exception import TokenError
from .message import Message
from .telemetry import Telemetry
from .tuning import Tuning
from ..log import logger


class Direction(IntEnum):
    RELAY = 1
    PROXY = 2


class Ouija:
    telemetry: Telemetry
    tuning: Tuning
    direction: Direction
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
                data = await asyncio.wait_for(reader.read(self.tuning.tcp_buffer), self.tuning.tcp_timeout)
            except TimeoutError:
                continue

            if not data:
                break

            self.telemetry.recv(data=data)

#            if crypt:
#                data = Message.encrypt(data=data, fernet=self.tuning.fernet)
#            else:
#                data = Message.decrypt(data=data, fernet=self.tuning.fernet)

            writer.write(data)
            await writer.drain()
            self.telemetry.send(data=data)

        self.sync.clear()

    async def forward(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, crypt: bool) -> None:
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
        raise NotImplemented

    async def serve_wrapped(self) -> None:
        await self.on_serve()
        self.opened.set()
        self.telemetry.open()

        self.sync.set()
        match self.direction:
            case Direction.RELAY:
                await asyncio.gather(
                    self.forward(reader=self.reader, writer=self.target_writer, crypt=True),
                    self.forward(reader=self.target_reader, writer=self.writer, crypt=False),
                )
            case Direction.PROXY:
                await asyncio.gather(
                    self.forward(reader=self.reader, writer=self.target_writer, crypt=False),
                    self.forward(reader=self.target_reader, writer=self.writer, crypt=True),
                )
            case _:
                pass

    async def serve(self) -> None:
        try:
            await asyncio.wait_for(self.serve_wrapped(), self.tuning.serving_timeout)
        except TokenError:
            self.telemetry.token_error()
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
        self.sync.clear()

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
