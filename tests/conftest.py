import asyncio
from typing import Optional
from unittest.mock import AsyncMock

import pytest
from cryptography.fernet import Fernet

from ouija import StreamTelemetry, DatagramTelemetry, StreamTuning, DatagramTuning, StreamOuija, DatagramOuija, \
    StreamConnector, DatagramConnector, StreamLink, DatagramLink, StreamRelay, DatagramRelay, StreamProxy, DatagramProxy


@pytest.fixture
def token_test():
    return 'secret'


@pytest.fixture
def data_test():
    return b'Test data'


@pytest.fixture
def fernet_test():
    return Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=')


@pytest.fixture
def stream_telemetry_test():
    return StreamTelemetry()


@pytest.fixture
def datagram_telemetry_test():
    return DatagramTelemetry()


@pytest.fixture
def stream_tuning_test(fernet_test, token_test):
    return StreamTuning(
        fernet=fernet_test,
        token=token_test,
        serving_timeout=3.0,
        tcp_buffer=1024,
        tcp_timeout=1.0,
        message_timeout=2.0,
    )


@pytest.fixture
def datagram_tuning_test(fernet_test, token_test):
    return DatagramTuning(
        fernet=fernet_test,
        token=token_test,
        serving_timeout=3.0,
        tcp_buffer=1024,
        tcp_timeout=1.0,
        udp_payload=512,
        udp_timeout=0.5,
        udp_retries=5,
        udp_capacity=10,
        udp_resend_sleep=0.1,
    )


class DatagramOuijaTest(DatagramOuija):
    def __init__(
            self,
            *,
            telemetry: DatagramTelemetry,
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
def datagram_ouija_test(datagram_telemetry_test, datagram_tuning_test):
    return DatagramOuijaTest(
        telemetry=datagram_telemetry_test,
        tuning=datagram_tuning_test,
        remote_host='example.com',
        remote_port=443,
    )


@pytest.fixture
def stream_connector_test(stream_telemetry_test, stream_tuning_test):
    return StreamConnector(
        telemetry=stream_telemetry_test,
        tuning=stream_tuning_test,
        relay=AsyncMock(),
        reader=AsyncMock(),
        writer=AsyncMock(),
        proxy_host='127.0.0.1',
        proxy_port=50000,
        remote_host='example.com',
        remote_port=443,
    )


@pytest.fixture
def datagram_connector_test(datagram_telemetry_test, datagram_tuning_test):
    return DatagramConnector(
        telemetry=datagram_telemetry_test,
        tuning=datagram_tuning_test,
        relay=AsyncMock(),
        reader=AsyncMock(),
        writer=AsyncMock(),
        proxy_host='127.0.0.1',
        proxy_port=50000,
        remote_host='example.com',
        remote_port=443,
    )


@pytest.fixture
def stream_link_test(stream_telemetry_test, stream_tuning_test):
    return StreamLink(
        telemetry=stream_telemetry_test,
        tuning=stream_tuning_test,
        proxy=AsyncMock(),
        reader=AsyncMock(),
        writer=AsyncMock(),
    )


@pytest.fixture
def datagram_link_test(datagram_telemetry_test, datagram_tuning_test):
    return DatagramLink(
        telemetry=datagram_telemetry_test,
        tuning=datagram_tuning_test,
        proxy=AsyncMock(),
        addr=('127.0.0.1', 60000),
    )


@pytest.fixture
def datagram_relay_test(datagram_telemetry_test, datagram_tuning_test):
    return DatagramRelay(
        telemetry=datagram_telemetry_test,
        tuning=datagram_tuning_test,
        proxy_host='127.0.0.1',
        proxy_port=50000,
    )


@pytest.fixture
def datagram_proxy_test(datagram_telemetry_test, datagram_tuning_test):
    return DatagramProxy(
        telemetry=datagram_telemetry_test,
        tuning=datagram_tuning_test,
        proxy_host='0.0.0.0',
        proxy_port=50000,
    )
