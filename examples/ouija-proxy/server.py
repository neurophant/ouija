import asyncio

import settings
from ouija import Proxy, Telemetry, Tuning


async def main() -> None:
    tuning = Tuning(
        fernet=settings.fernet,
        token=settings.TOKEN,
        serving_timeout=settings.SERVING_TIMEOUT,
        tcp_buffer=settings.TCP_BUFFER,
        tcp_timeout=settings.TCP_TIMEOUT,
        udp_payload=settings.UDP_PAYLOAD,
        udp_timeout=settings.UDP_TIMEOUT,
        udp_retries=settings.UDP_RETRIES,
        udp_capacity=settings.UDP_CAPACITY,
    )
    proxy = Proxy(
        telemetry=Telemetry(),
        tuning=tuning,
        proxy_host=settings.PROXY_HOST,
        proxy_port=settings.PROXY_PORT,
    )
    asyncio.create_task(proxy.cleanup())
    asyncio.create_task(proxy.monitor())
    await proxy.serve()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
