import asyncio

import settings
from ouija import Proxy, Telemetry, Tuning


def main() -> None:
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
    loop = asyncio.get_event_loop()
    loop.create_task(proxy.cleanup())
    #loop.create_task(proxy.monitor())
    loop.run_until_complete(proxy.serve())
    loop.run_forever()


if __name__ == '__main__':
    main()
