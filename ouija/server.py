import asyncio
import logging
import sys

from .tuning import StreamTuning, DatagramTuning
from .telemetry import StreamTelemetry, DatagramTelemetry
from .relay import StreamRelay, DatagramRelay
from .proxy import StreamProxy, DatagramProxy
from .config import Config, Mode, Protocol


async def main() -> None:
    if len(sys.argv[1:]) != 1:
        print('Usage: python -m ouija.server <config.json>')
        sys.exit(0)

    config = Config(path=sys.argv[1])

    logging.basicConfig(
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
        level=logging.DEBUG if config.debug else logging.ERROR,
    )

    match config.protocol:
        case Protocol.TCP:
            telemetry_class = StreamTelemetry
            tuning = StreamTuning(
                fernet=config.fernet,
                token=config.token,
                serving_timeout=config.serving_timeout,
                tcp_buffer=config.tcp_buffer,
                tcp_timeout=config.tcp_timeout,
                message_timeout=config.message_timeout,
            )
            relay_class = StreamRelay
            proxy_class = StreamProxy
        case Protocol.TCP:
            telemetry_class = DatagramTelemetry
            tuning = DatagramTuning(
                fernet=config.fernet,
                token=config.token,
                serving_timeout=config.serving_timeout,
                tcp_buffer=config.tcp_buffer,
                tcp_timeout=config.tcp_timeout,
                udp_payload=config.udp_payload,
                udp_timeout=config.udp_timeout,
                udp_retries=config.udp_retries,
                udp_capacity=config.udp_capacity,
                udp_resend_sleep=config.udp_resend_sleep,
            )
            relay_class = DatagramRelay
            proxy_class = DatagramProxy
        case _:
            raise NotImplementedError

    match config.mode:
        case Mode.RELAY:
            server = relay_class(
                telemetry=telemetry_class(),
                tuning=tuning,
                relay_host=config.relay_host,
                relay_port=config.relay_port,
                proxy_host=config.proxy_host,
                proxy_port=config.proxy_port,
            )
        case Mode.PROXY:
            server = proxy_class(
                telemetry=telemetry_class(),
                tuning=tuning,
                proxy_host=config.proxy_host,
                proxy_port=config.proxy_port,
            )
        case _:
            raise NotImplementedError

    if config.monitor:
        asyncio.create_task(server.debug())

    await server.serve()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
