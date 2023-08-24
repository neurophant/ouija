import sys
sys.path.append('../')

import asyncio
import logging

from cryptography.fernet import Fernet

from ouija import DatagramProxy as Proxy, DatagramTelemetry as Telemetry, DatagramTuning as Tuning, SpaceEntropy


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG,
)


async def main() -> None:
    tuning = Tuning(
        fernet=Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
        token='secret',
        entropy=SpaceEntropy(every=5),
        serving_timeout=20.0,
        tcp_buffer=1024,
        tcp_timeout=1.0,
        udp_payload=1024,
        udp_timeout=2.0,
        udp_retries=5,
        udp_capacity=10000,
        udp_resend_sleep=0.1,
    )
    proxy = Proxy(
        telemetry=Telemetry(),
        tuning=tuning,
        proxy_host='0.0.0.0',
        proxy_port=50000,
    )
    asyncio.create_task(proxy.debug())
    await proxy.serve()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
