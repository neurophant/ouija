import sys
sys.path.append('../')

import asyncio
import logging

from cryptography.fernet import Fernet

from ouija import DatagramRelay as Relay, DatagramTuning as Tuning, DatagramTelemetry as Telemetry, SpaceEntropy


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
    relay = Relay(
        telemetry=Telemetry(),
        tuning=tuning,
        relay_host='127.0.0.1',
        relay_port=9000,
        proxy_host='127.0.0.1',
        proxy_port=50000,
    )
    asyncio.create_task(relay.debug())
    await relay.serve()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
