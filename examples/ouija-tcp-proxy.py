import sys
sys.path.append('../')

import asyncio
import logging

from cryptography.fernet import Fernet

from ouija import ProxyTCP as Proxy, TelemetryTCP as Telemetry, TuningTCP as Tuning


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG,
)


async def main() -> None:
    tuning = Tuning(
        fernet=Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
        token='secret',
        serving_timeout=20.0,
        message_buffer=1024,
        tcp_buffer=1024,
        tcp_timeout=1.0,
    )
    proxy = Proxy(
        telemetry=Telemetry(),
        tuning=tuning,
    )
    asyncio.create_task(proxy.debug())
    server = await asyncio.start_server(
        proxy.serve,
        '0.0.0.0',
        50000,
    )
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
