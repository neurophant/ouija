import asyncio
from typing import Optional
from unittest.mock import AsyncMock

import pytest

from ouija import Telemetry, StreamTuning, DatagramTuning, StreamOuija, DatagramOuija, StreamConnector, \
    DatagramConnector, StreamLink, DatagramLink, StreamRelay, DatagramRelay, StreamProxy, DatagramProxy, FernetCipher, \
    SimpleEntropy


@pytest.fixture
def telemetry_test():
    return Telemetry()


@pytest.fixture
def cipher_test():
    return FernetCipher(key='bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=')


@pytest.fixture
def entropy_test():
    return SimpleEntropy(rate=5)


@pytest.fixture
def token_test():
    return 'secret'


@pytest.fixture
def data_test():
    return b'Test data'


@pytest.fixture
def stream_tuning_test(cipher_test, entropy_test, token_test):
    return StreamTuning(
        cipher=cipher_test,
        entropy=entropy_test,
        token=token_test,
        serving_timeout=3.0,
        tcp_buffer=1024,
        tcp_timeout=1.0,
        message_timeout=2.0,
    )


@pytest.fixture
def datagram_tuning_test(cipher_test, entropy_test, token_test):
    return DatagramTuning(
        cipher=cipher_test,
        entropy=entropy_test,
        token=token_test,
        serving_timeout=3.0,
        tcp_buffer=1024,
        tcp_timeout=1.0,
        udp_min_payload=512,
        udp_max_payload=1024,
        udp_timeout=0.5,
        udp_retries=5,
        udp_capacity=10,
        udp_resend_sleep=0.1,
    )


class StreamOuijaTest(StreamOuija):
    def __init__(
            self,
            *,
            telemetry: Telemetry,
            tuning: StreamTuning,
            remote_host: Optional[str],
            remote_port: Optional[int],
    ):
        self.telemetry = telemetry
        self.tuning = tuning
        self.crypt = True
        self.reader = AsyncMock()
        self.writer = AsyncMock()
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.target_reader = AsyncMock()
        self.target_writer = AsyncMock()
        self.opened = asyncio.Event()
        self.sync = asyncio.Event()


@pytest.fixture
def stream_ouija_test(telemetry_test, stream_tuning_test):
    return StreamOuijaTest(
        telemetry=telemetry_test,
        tuning=stream_tuning_test,
        remote_host='example.com',
        remote_port=50000,
    )


class DatagramOuijaTest(DatagramOuija):
    def __init__(
            self,
            *,
            telemetry: Telemetry,
            tuning: DatagramTuning,
            remote_host: Optional[str],
            remote_port: Optional[int],
    ):
        self.telemetry = telemetry
        self.tuning = tuning
        self.reader = AsyncMock()
        self.writer = AsyncMock()
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.opened = asyncio.Event()
        self.sync = asyncio.Event()
        self.sent_buf = dict()
        self.sent_seq = 0
        self.read_closed = asyncio.Event()
        self.recv_buf = dict()
        self.recv_seq = 0
        self.write_closed = asyncio.Event()


@pytest.fixture
def datagram_ouija_test(telemetry_test, datagram_tuning_test):
    return DatagramOuijaTest(
        telemetry=telemetry_test,
        tuning=datagram_tuning_test,
        remote_host='example.com',
        remote_port=443,
    )


@pytest.fixture
def stream_connector_test(telemetry_test, stream_tuning_test):
    return StreamConnector(
        telemetry=telemetry_test,
        tuning=stream_tuning_test,
        relay=AsyncMock(),
        reader=AsyncMock(),
        writer=AsyncMock(),
        proxy_host='127.0.0.1',
        proxy_port=50000,
        remote_host='example.com',
        remote_port=443,
        https=True,
    )


@pytest.fixture
def datagram_connector_test(telemetry_test, datagram_tuning_test):
    return DatagramConnector(
        telemetry=telemetry_test,
        tuning=datagram_tuning_test,
        relay=AsyncMock(),
        reader=AsyncMock(),
        writer=AsyncMock(),
        proxy_host='127.0.0.1',
        proxy_port=50000,
        remote_host='example.com',
        remote_port=443,
        https=True,
    )


@pytest.fixture
def stream_link_test(telemetry_test, stream_tuning_test):
    return StreamLink(
        telemetry=telemetry_test,
        tuning=stream_tuning_test,
        proxy=AsyncMock(),
        reader=AsyncMock(),
        writer=AsyncMock(),
    )


@pytest.fixture
def datagram_link_test(telemetry_test, datagram_tuning_test):
    return DatagramLink(
        telemetry=telemetry_test,
        tuning=datagram_tuning_test,
        proxy=AsyncMock(),
        addr=('127.0.0.1', 60000),
    )


@pytest.fixture
def stream_relay_test(telemetry_test, stream_tuning_test):
    return StreamRelay(
        telemetry=telemetry_test,
        tuning=stream_tuning_test,
        relay_host='127.0.0.1',
        relay_port=9000,
        proxy_host='127.0.0.1',
        proxy_port=50000,
    )


@pytest.fixture
def datagram_relay_test(telemetry_test, datagram_tuning_test):
    return DatagramRelay(
        telemetry=telemetry_test,
        tuning=datagram_tuning_test,
        relay_host='127.0.0.1',
        relay_port=9000,
        proxy_host='127.0.0.1',
        proxy_port=50000,
    )


@pytest.fixture
def stream_proxy_test(telemetry_test, stream_tuning_test):
    return StreamProxy(
        telemetry=telemetry_test,
        tuning=stream_tuning_test,
        proxy_host='0.0.0.0',
        proxy_port=50000,
    )


@pytest.fixture
def datagram_proxy_test(telemetry_test, datagram_tuning_test):
    return DatagramProxy(
        telemetry=telemetry_test,
        tuning=datagram_tuning_test,
        proxy_host='0.0.0.0',
        proxy_port=50000,
    )


@pytest.fixture
def config_dict_test():
    return {
        'protocol': 'UDP',
        'mode': 'RELAY',
        'debug': True,
        'monitor': True,
        'relay_host': '127.0.0.1',
        'relay_port': 9000,
        'proxy_host': '127.0.0.1',
        'proxy_port': 50000,
        'cipher_key': 'bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=',
        'entropy_rate': 5,
        'token': '395f249c-343a-4f92-9129-68c6d83b5f55',
        'serving_timeout': 20.0,
        'tcp_buffer': 1024,
        'tcp_timeout': 1.0,
        'message_timeout': 5.0,
        'udp_min_payload': 512,
        'udp_max_payload': 1024,
        'udp_timeout': 2.0,
        'udp_retries': 5,
        'udp_capacity': 1000,
        'udp_resend_sleep': 0.25
    }


@pytest.fixture
def config_stream_relay_dict_test():
    return {
        'protocol': 'TCP',
        'mode': 'RELAY',
        'debug': True,
        'monitor': True,
        'relay_host': '127.0.0.1',
        'relay_port': 9000,
        'proxy_host': '127.0.0.1',
        'proxy_port': 50000,
        'cipher_key': 'bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=',
        'entropy_rate': 5,
        'token': '395f249c-343a-4f92-9129-68c6d83b5f55',
        'serving_timeout': 20.0,
        'tcp_buffer': 1024,
        'tcp_timeout': 1.0,
        'message_timeout': 5.0,
    }


@pytest.fixture
def config_stream_proxy_dict_test():
    return {
        'protocol': 'TCP',
        'mode': 'PROXY',
        'debug': True,
        'monitor': True,
        'proxy_host': '0.0.0.0',
        'proxy_port': 50000,
        'cipher_key': 'bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=',
        'entropy_rate': 5,
        'token': '395f249c-343a-4f92-9129-68c6d83b5f55',
        'serving_timeout': 20.0,
        'tcp_buffer': 1024,
        'tcp_timeout': 1.0,
        'message_timeout': 5.0,
    }


@pytest.fixture
def config_datagram_relay_dict_test():
    return {
        'protocol': 'UDP',
        'mode': 'RELAY',
        'debug': True,
        'monitor': True,
        'relay_host': '127.0.0.1',
        'relay_port': 9000,
        'proxy_host': '127.0.0.1',
        'proxy_port': 50000,
        'cipher_key': 'bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=',
        'entropy_rate': 5,
        'token': '395f249c-343a-4f92-9129-68c6d83b5f55',
        'serving_timeout': 20.0,
        'tcp_buffer': 1024,
        'tcp_timeout': 1.0,
        'udp_min_payload': 512,
        'udp_max_payload': 1024,
        'udp_timeout': 2.0,
        'udp_retries': 5,
        'udp_capacity': 1000,
        'udp_resend_sleep': 0.25
    }


@pytest.fixture
def config_datagram_proxy_dict_test():
    return {
        'protocol': 'UDP',
        'mode': 'PROXY',
        'debug': True,
        'monitor': True,
        'proxy_host': '0.0.0.0',
        'proxy_port': 50000,
        'cipher_key': 'bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=',
        'entropy_rate': 5,
        'token': '395f249c-343a-4f92-9129-68c6d83b5f55',
        'serving_timeout': 20.0,
        'tcp_buffer': 1024,
        'tcp_timeout': 1.0,
        'udp_min_payload': 512,
        'udp_max_payload': 1024,
        'udp_timeout': 2.0,
        'udp_retries': 5,
        'udp_capacity': 1000,
        'udp_resend_sleep': 0.25
    }
