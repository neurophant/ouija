import sys
sys.path.append('../')

import asyncio
import logging

from ouija import StreamProxy as Proxy, Telemetry, StreamTuning as Tuning, SimpleEntropy, FernetCipher


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
