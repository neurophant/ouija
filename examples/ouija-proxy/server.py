import asyncio

import settings
from ouija import Proxy, Telemetry, Tuning


async def main() -> None:
    tuning = Tuning(
        fernet=settings.fernet,
        token=settings.TOKEN,
        buffer=settings.BUFFER,
        serving=settings.SERVING,
        timeout=settings.TIMEOUT,
        payload=settings.PAYLOAD,
        retries=settings.RETRIES,
        capacity=settings.CAPACITY,
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
