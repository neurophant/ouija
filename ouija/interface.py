import asyncio
import logging
import os
from typing import Dict

from .tuning import Tuning
from .relay import Relay
from .telemetry import Telemetry
from .rawparser import RawParser


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.ERROR,
)
logger = logging.getLogger(__name__)


class Interface:
    telemetry: Telemetry
    tuning: Tuning
    proxy_host: str
    proxy_port: int
    index: int
    sessions: Dict[int, asyncio.Task]

    def __init__(self, *, telemetry: Telemetry, tuning: Tuning, proxy_host: str, proxy_port: int) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.index = 0
        self.sessions = dict()

    async def https_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
    ) -> None:
        relay = Relay(
            telemetry=self.telemetry,
            tuning=self.tuning,
            reader=reader,
            writer=writer,
            proxy_host=self.proxy_host,
            proxy_port=self.proxy_port,
            remote_host=remote_host,
            remote_port=remote_port,
        )
        await relay.serve()

    async def handle_session(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        data = await reader.readuntil(b'\r\n\r\n')
        request = RawParser(data=data)
        print(data)
        if request.error:
            logger.error('Parse error')
        elif request.method == 'CONNECT':
            await self.https_handler(
                reader=reader,
                writer=writer,
                remote_host=request.host,
                remote_port=request.port,
            )
        else:
            logger.error(f'{request.method} method is not supported')

    async def session(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            await asyncio.wait_for(self.handle_session(reader=reader, writer=writer), self.tuning.serving_timeout)
        except asyncio.TimeoutError:
            logger.error('Timeout')

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.sessions[self.index] = asyncio.create_task(self.session(reader=reader, writer=writer))
        self.index += 1

    async def cleanup(self) -> None:    # pragma: no cover
        while True:
            await asyncio.sleep(1)
            for index in sorted(self.sessions.keys()):
                if self.sessions[index].done():
                    self.sessions.pop(index)
            self.telemetry.link(links=len(self.sessions))

    async def monitor(self) -> None:    # pragma: no cover
        while True:
            await asyncio.sleep(1)
            os.system('clear')
            print(self.telemetry)
