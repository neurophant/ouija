import sys
sys.path.append('../')

import asyncio
import logging

from ouija import StreamRelay as Relay, StreamTuning as Tuning, Telemetry, SimpleEntropy, FernetCipher


logging.basicConfig(
    format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG,
)


async def main() -> None:
    tuning = Tuning(
        cipher=FernetCipher(key='bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
        entropy=SimpleEntropy(rate=5),
        token='395f249c-343a-4f92-9129-68c6d83b5f55',
        serving_timeout=20.0,
        tcp_buffer=1024,
        tcp_timeout=1.0,
        message_timeout=5.0,
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
