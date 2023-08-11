import sys
sys.path.append('../')

import asyncio
import logging

from cryptography.fernet import Fernet

from ouija import Interface, Tuning, Telemetry


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG,
)


async def main() -> None:
    tuning = Tuning(
        fernet=Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
        token='secret',
        serving_timeout=30,
        tcp_buffer=1024,
        tcp_timeout=1,
        udp_payload=1024,
        udp_timeout=3,
        udp_retries=3,
        udp_capacity=10000,
    )
    interface = Interface(
        telemetry=Telemetry(),
        tuning=tuning,
        proxy_host='127.0.0.1',
        proxy_port=50000,
    )
    asyncio.create_task(interface.debug())
    server = await asyncio.start_server(
        interface.serve,
        '127.0.0.1',
        9000,
    )
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
