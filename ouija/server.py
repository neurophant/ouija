import asyncio
import logging
import sys

from .cipher import FernetCipher
from .entropy import SimpleEntropy
from .tuning import StreamTuning, DatagramTuning
from .telemetry import Telemetry
from .relay import StreamRelay, DatagramRelay
from .proxy import StreamProxy, DatagramProxy
from .config import Config, Mode, Protocol


async def main_async() -> None:
    if len(sys.argv[1:]) != 1:  # pragma: no cover
        print('Usage: ouija <config.json>\n')
        sys.exit(0)

    config = Config(path=sys.argv[1])

    logging.basicConfig(
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
        level=logging.DEBUG if config.debug else logging.ERROR,
    )

    cipher = FernetCipher(key=config.cipher_key) if config.cipher_key else None
    entropy = SimpleEntropy(rate=config.entropy_rate) if config.entropy_rate else None

    match config.protocol:
        case Protocol.TCP:
            relay_class, proxy_class = StreamRelay, StreamProxy
            tuning = StreamTuning(
                cipher=cipher,
                entropy=entropy,
                token=config.token,
                serving_timeout=config.serving_timeout,
                tcp_buffer=config.tcp_buffer,
                tcp_timeout=config.tcp_timeout,
                message_timeout=config.message_timeout,
            )
        case Protocol.UDP:
            relay_class, proxy_class = DatagramRelay, DatagramProxy
            tuning = DatagramTuning(
                cipher=cipher,
                entropy=entropy,
                token=config.token,
                serving_timeout=config.serving_timeout,
                tcp_buffer=config.tcp_buffer,
                tcp_timeout=config.tcp_timeout,
                udp_min_payload=config.udp_min_payload,
                udp_max_payload=config.udp_max_payload,
                udp_timeout=config.udp_timeout,
                udp_retries=config.udp_retries,
                udp_capacity=config.udp_capacity,
                udp_resend_sleep=config.udp_resend_sleep,
            )
        case _:     # pragma: no cover
            raise NotImplementedError

    match config.mode:
        case Mode.RELAY:
            server = relay_class(
                telemetry=Telemetry(),
                tuning=tuning,
                relay_host=config.relay_host,
                relay_port=config.relay_port,
                proxy_host=config.proxy_host,
                proxy_port=config.proxy_port,
            )
        case Mode.PROXY:
            server = proxy_class(
                telemetry=Telemetry(),
                tuning=tuning,
                proxy_host=config.proxy_host,
                proxy_port=config.proxy_port,
            )
        case _:     # pragma: no cover
            raise NotImplementedError

    if config.monitor:
        asyncio.create_task(server.debug())

    await server.serve()


def main() -> None:     # pragma: no cover
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.run_forever()


if __name__ == '__main__':  # pragma: no cover
    main()
