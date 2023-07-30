import asyncio
import logging
import os
from contextlib import closing
from typing import Dict

from .tuning import Tuning
from .relay import Relay
from .telemetry import Telemetry
from .utils import RawParser


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class Interface:
    telemetry: Telemetry
    __tuning: Tuning
    __proxy_host: str
    __proxy_port: int
    __index: int
    __sessions: Dict[int, asyncio.Task]

    def __init__(self, *, telemetry: Telemetry, tuning: Tuning, proxy_host: str, proxy_port: int) -> None:
        self.telemetry = telemetry
        self.__tuning = tuning
        self.__proxy_host = proxy_host
        self.__proxy_port = proxy_port
        self.__index = 0
        self.__sessions = dict()

    async def __https_handler(
            self,
            *,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            remote_host: str,
            remote_port: int,
    ) -> None:
        relay = Relay(
            telemetry=self.telemetry,
            tuning=self.__tuning,
            reader=reader,
            writer=writer,
            proxy_host=self.__proxy_host,
            proxy_port=self.__proxy_port,
            remote_host=remote_host,
            remote_port=remote_port,
        )
        await relay.stream()

    async def __session(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        with closing(writer):
            data = await reader.readuntil(b'\r\n\r\n')
            addr = writer.get_extra_info('peername')

            request = RawParser(data=data)

            if request.error:
                logger.error('Parse error')
            elif request.method == 'CONNECT':  # https
                await self.__https_handler(
                    reader=reader,
                    writer=writer,
                    remote_host=request.host,
                    remote_port=request.port,
                )
            else:
                logger.error(f'{request.method} method is not supported')

    async def _session(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            await asyncio.wait_for(self.__session(reader=reader, writer=writer), self.__tuning.serving)
        except asyncio.TimeoutError:
            logger.error('Timeout')

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        loop = asyncio.get_event_loop()
        self.__sessions[self.__index] = loop.create_task(self._session(reader=reader, writer=writer))
        self.__index += 1

    async def cleanup(self) -> None:
        while True:
            await asyncio.sleep(1)
            for index in sorted(self.__sessions.keys()):
                if self.__sessions[index].done():
                    self.__sessions.pop(index)
            self.telemetry.links = len(self.__sessions)

    async def monitor(self) -> None:
        while True:
            await asyncio.sleep(1)
            os.system('clear')
            print(self.telemetry)
