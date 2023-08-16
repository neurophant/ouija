import asyncio
import os

from .link import Link
from .tuning import Tuning
from .telemetry import Telemetry
from ..log import logger


class Proxy:
    telemetry: Telemetry
    tuning: Tuning
    index: int
    sessions: dict[int, asyncio.Task]

    def __init__(self, *, telemetry: Telemetry, tuning: Tuning) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.index = 0
        self.sessions = dict()

    async def session_wrapped(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        link = Link(
            telemetry=self.telemetry,
            tuning=self.tuning,
            reader=reader,
            writer=writer,
        )
        await link.serve()

    async def session(self, *, index: int, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            await asyncio.wait_for(self.session_wrapped(reader=reader, writer=writer), self.tuning.serving_timeout * 2)
        except TimeoutError:
            self.telemetry.timeout_error()
        except Exception as e:
            logger.exception(e)
            self.telemetry.serving_error()
        finally:
            _ = self.sessions.pop(index, None)

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Relay TCP server entry point
        :returns: None
        """

        self.sessions[self.index] = asyncio.create_task(self.session(index=self.index, reader=reader, writer=writer))
        self.index += 1

    async def debug(self) -> None:    # pragma: no cover
        """Debug monitor with telemetry output
        :returns: None
        """

        while True:
            await asyncio.sleep(1)
            self.telemetry.link(links=len(self.sessions))
            os.system('clear')
            print(self.telemetry)
