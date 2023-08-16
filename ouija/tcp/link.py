import asyncio

from ..exception import TokenError
from .message import Message, SEPARATOR
from .ouija import Ouija
from .telemetry import Telemetry
from .tuning import Tuning


class Link(Ouija):
    def __init__(
            self,
            *,
            telemetry: Telemetry,
            tuning: Tuning,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.crypt = False
        self.reader = reader
        self.writer = writer
        self.remote_host = None
        self.remote_port = None
        self.target_reader = None
        self.target_writer = None
        self.opened = asyncio.Event()
        self.sync = asyncio.Event()

    async def on_serve(self) -> None:
        data = await asyncio.wait_for(self.reader.readuntil(SEPARATOR), self.tuning.message_timeout)
        message = Message.message(data=data, fernet=self.tuning.fernet)
        if message.token != self.tuning.token:
            raise TokenError

        self.remote_host = message.host
        self.remote_port = message.port
        self.target_reader, self.target_writer = await asyncio.open_connection(self.remote_host, self.remote_port)

        message = Message(token=self.tuning.token)
        data = message.binary(fernet=self.tuning.fernet)
        self.writer.write(data)
        await self.writer.drain()
