from dataclasses import dataclass
import datetime
from typing import Optional

from .entropy import Entropy


@dataclass(kw_only=True)
class Telemetry:
    """Telemetry collector"""

    active: int = 0
    opened: int = 0
    closed: int = 0
    payloads_sent: int = 0
    payloads_recv: int = 0
    bytes_sent: int = 0
    bytes_recv: int = 0
    payload_count: int = 0
    payload_sum: int = 0
    min_payload_size: int = 0
    max_payload_size: int = 0
    avg_payload_size: int = 0
    entropy_count: int = 0
    entropy_sum: float = 0.0
    min_entropy: float = 0.0
    max_entropy: float = 0.0
    avg_entropy: float = 0.0
    processing_errors: int = 0
    token_errors: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    serving_errors: int = 0
    resending_errors: int = 0
    send_buf_overloads: int = 0
    recv_buf_overloads: int = 0

    def __str__(self) -> str:
        return \
            f'{datetime.datetime.now()}\n' \
            f'\tactive: {self.active:,}\n' \
            f'\topened|closed: {self.opened:,}|{self.closed:,}\n' \
            f'\tpayloads sent|received: {self.payloads_sent:,}|{self.payloads_recv:,}\n' \
            f'\tbytes sent|received: {self.bytes_sent:,}|{self.bytes_recv:,}\n' \
            f'\tmin|avg|max payload size: ' \
            f'{self.min_payload_size:,}|{self.avg_payload_size:,}|{self.max_payload_size:,}\n' \
            f'\tmin|avg|max entropy: {self.min_entropy:.4f}|{self.avg_entropy:.4f}|{self.max_entropy:.4f}\n' \
            f'\ttoken errors: {self.token_errors:,}\n' \
            f'\tprocessing|resending errors: {self.processing_errors:,}|{self.resending_errors:,}\n' \
            f'\ttimeout|connection|serving errors: ' \
            f'{self.timeout_errors:,}|{self.connection_errors:,}|{self.serving_errors:,}\n' \
            f'\tsend|recv buf overloads: {self.send_buf_overloads:,}|{self.recv_buf_overloads:,}'

    def collect(self, *, active: int) -> None:
        self.active = active

    def open(self) -> None:
        self.opened += 1

    def close(self) -> None:
        self.closed += 1

    def payload(self, *, data: bytes, entropy: Optional[Entropy]) -> None:
        self.payload_count += 1
        self.payload_sum += len(data)

        if len(data) < self.min_payload_size or self.min_payload_size == 0:
            self.min_payload_size = len(data)
        if len(data) > self.max_payload_size:
            self.max_payload_size = len(data)
        self.avg_payload_size = int(self.payload_sum / self.payload_count)

        if entropy:
            value = entropy.calculate(data=data)
            if value < self.min_entropy or self.min_entropy == 0.0:
                self.min_entropy = value
            if value > self.max_entropy:
                self.max_entropy = value

            self.entropy_count += 1
            self.entropy_sum += value
            self.avg_entropy = self.entropy_sum / self.entropy_count if self.entropy_count > 0 else 0.0

    def send(self, *, data: bytes, entropy: Optional[Entropy]) -> None:
        self.payloads_sent += 1
        self.bytes_sent += len(data)
        self.payload(data=data, entropy=entropy)

    def recv(self, *, data: bytes, entropy: Optional[Entropy]) -> None:
        self.payloads_recv += 1
        self.bytes_recv += len(data)
        self.payload(data=data, entropy=entropy)

    def processing_error(self) -> None:
        self.processing_errors += 1

    def token_error(self) -> None:
        self.token_errors += 1

    def timeout_error(self) -> None:
        self.timeout_errors += 1

    def connection_error(self) -> None:
        self.connection_errors += 1

    def serving_error(self) -> None:
        self.serving_errors += 1

    def resending_error(self) -> None:
        self.resending_errors += 1

    def send_buf_overload(self) -> None:
        self.send_buf_overloads += 1

    def recv_buf_overload(self) -> None:
        self.recv_buf_overloads += 1
