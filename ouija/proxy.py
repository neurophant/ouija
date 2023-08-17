import asyncio
import os
from typing import Optional

from .link import StreamLink, DatagramLink
from .tuning import StreamTuning, DatagramTuning
from .telemetry import StreamTelemetry, DatagramTelemetry
from .log import logger


class StreamProxy:
    telemetry: StreamTelemetry
    tuning: StreamTuning
    index: int
    sessions: dict[int, asyncio.Task]

    def __init__(self, *, telemetry: StreamTelemetry, tuning: StreamTuning) -> None:
        self.telemetry = telemetry
        self.tuning = tuning
        self.index = 0
        self.sessions = dict()

    async def session_wrapped(self, *, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        link = StreamLink(
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
        """Proxy TCP server entry point
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


class DatagramProxy(asyncio.DatagramProtocol):
    transport: Optional[asyncio.DatagramTransport]
    telemetry: DatagramTelemetry
    tuning: DatagramTuning
    proxy_host: str
    proxy_port: int
    links: dict[tuple[str, int], DatagramLink]

    def __init__(
            self,
            *,
            telemetry: DatagramTelemetry,
            tuning: DatagramTuning,
            proxy_host: str,
            proxy_port: int,
    ) -> None:
        self.transport = None
        self.telemetry = telemetry
        self.tuning = tuning
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.links = dict()

    def connection_made(self, transport) -> None:
        self.transport = transport

    async def datagram_received_async(self, *, data, addr) -> None:
        link = self.links.get(addr, DatagramLink(telemetry=self.telemetry, proxy=self, addr=addr, tuning=self.tuning))
        await link.process(data=data)

    def datagram_received(self, data, addr) -> None:
        asyncio.create_task(self.datagram_received_async(data=data, addr=addr))

    def error_received(self, exc) -> None:  # pragma: no cover
        logger.error(exc)

    def connection_lost(self, exc) -> None:
        self.transport.close()
        logger.error(exc)

    async def serve(self) -> None:
        """Proxy UDP server entry point
        :returns: None
        """

        loop = asyncio.get_event_loop()
        await loop.create_datagram_endpoint(lambda: self, local_addr=(self.proxy_host, self.proxy_port))

    async def debug(self) -> None:    # pragma: no cover
        """Debug monitor with telemetry output
        :returns: None
        """

        while True:
            await asyncio.sleep(1)
            self.telemetry.link(links=len(self.links))
            os.system('clear')
            print(self.telemetry)
