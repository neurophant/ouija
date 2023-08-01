import asyncio

import settings
from ouija import Interface, Tuning, Telemetry


async def main() -> None:
    tuning = Tuning(
        fernet=settings.fernet,
        token=settings.TOKEN,
        serving=settings.SERVING,
        timeout=settings.TIMEOUT,
        payload=settings.PAYLOAD,
        retries=settings.RETRIES,
        capacity=settings.CAPACITY,
    )
    interface = Interface(
        telemetry=Telemetry(),
        tuning=tuning,
        proxy_host=settings.PROXY_HOST,
        proxy_port=settings.PROXY_PORT,
    )
    loop = asyncio.get_event_loop()
    loop.create_task(interface.cleanup())
    #loop.create_task(interface.monitor())
    server = await asyncio.start_server(interface.serve, settings.RELAY_HOST, settings.RELAY_PORT)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
