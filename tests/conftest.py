import asyncio
from typing import Optional
from unittest.mock import AsyncMock

import pytest
from cryptography.fernet import Fernet

from ouija import Telemetry, Tuning, Ouija, Relay, Link, Interface, Proxy


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
def telemetry_test():
    return Telemetry()


@pytest.fixture
def tuning_test(fernet_test, token_test):
    return Tuning(
        fernet=fernet_test,
        token=token_test,
        serving_timeout=5,
        tcp_buffer=1024,
        tcp_timeout=1,
        udp_payload=512,
        udp_timeout=1,
        udp_retries=2,
        udp_capacity=1000,
    )


class OuijaTest(Ouija):
    def __init__(
            self,
            *,
            telemetry: Telemetry,
            tuning: Tuning,
            remote_host: Optional[str],
            remote_port: Optional[int],
    ):
        self.telemetry = telemetry
        self.tuning = tuning
        self.reader = None
        self.writer = None
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.opened = asyncio.Event()
        self.sent_buf = dict()
        self.sent_seq = 0
        self.read_closed = asyncio.Event()
        self.recv_buf = dict()
        self.recv_seq = 0
        self.write_closed = asyncio.Event()


@pytest.fixture
def ouija_test(telemetry_test, tuning_test):
    return OuijaTest(
        telemetry=telemetry_test,
        tuning=tuning_test,
        remote_host='example.com',
        remote_port=443,
    )


@pytest.fixture
def relay_test(telemetry_test, tuning_test):
    return Relay(
        telemetry=telemetry_test,
        tuning=tuning_test,
        reader=AsyncMock(),
        writer=AsyncMock(),
        proxy_host='127.0.0.1',
        proxy_port=50000,
        remote_host='example.com',
        remote_port=443,
    )


@pytest.fixture
def link_test(telemetry_test, tuning_test):
    return Link(
        telemetry=telemetry_test,
        proxy=AsyncMock(),
        addr=('127.0.0.1', 60000),
        tuning=tuning_test,
    )


@pytest.fixture
def interface_test(telemetry_test, tuning_test):
    return Interface(
        telemetry=telemetry_test,
        tuning=tuning_test,
        proxy_host='127.0.0.1',
        proxy_port=50000,
    )


@pytest.fixture
def proxy_test(telemetry_test, tuning_test):
    return Proxy(
        telemetry=telemetry_test,
        tuning=tuning_test,
        proxy_host='0.0.0.0',
        proxy_port=50000,
)
