import asyncio
from typing import Optional

import pytest
from cryptography.fernet import Fernet

from ouija import Telemetry, Tuning, Ouija


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
