import asyncio

from .exception import TokenError
from .message import Message, SEPARATOR
from .ouija import Ouija
from .telemetry import Telemetry
from .tuning import Tuning


class Relay(Ouija):
    proxy_host: str
    proxy_port: int

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
        self.crypt = True
        self.reader = reader
        self.writer = writer
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.target_reader = None
        self.target_writer = None
        self.opened = asyncio.Event()
        self.sync = asyncio.Event()

    async def on_serve(self) -> None:
        self.target_reader, self.target_writer = await asyncio.open_connection(self.proxy_host, self.proxy_port)

        message = Message(token=self.tuning.token, host=self.remote_host, port=self.remote_port)
        data = message.binary(fernet=self.tuning.fernet)
        self.target_writer.write(data)
        await self.target_writer.drain()

        data = await asyncio.wait_for(self.target_reader.readuntil(SEPARATOR), self.tuning.message_timeout)
        message = Message.message(data=data, fernet=self.tuning.fernet)
        if message.token != self.tuning.token:
            raise TokenError

        self.writer.write(data=b'HTTP/1.1 200 Connection Established\r\n\r\n')
        await self.writer.drain()
