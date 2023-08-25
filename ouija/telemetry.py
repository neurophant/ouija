from dataclasses import dataclass
import datetime
from typing import Optional

from .entropy import Entropy


@dataclass(kw_only=True)
class StreamTelemetry:
    active: int = 0
    opened: int = 0
    closed: int = 0
    bytes_sent: int = 0
    bytes_recv: int = 0
    entropy_min: float = 0.0
    entropy_max: float = 0.0
    entropy_count: int = 0
    entropy_sum: float = 0.0
    entropy_avg: float = 0.0
    token_errors: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    serving_errors: int = 0

    def __str__(self) -> str:
        return \
            f'{datetime.datetime.now()}\n' \
            f'\tactive: {self.active:,}\n' \
            f'\topened|closed: {self.opened:,}|{self.closed:,}\n' \
            f'\tbytes sent|received: {self.bytes_sent:,}|{self.bytes_recv:,}\n' \
            f'\tentropy min|avg|max: {self.entropy_min:.4f}|{self.entropy_avg:.4f}|{self.entropy_max:.4f}\n' \
            f'\ttoken|timeout|connection|serving errors: {self.token_errors:,}|{self.timeout_errors:,}' \
            f'|{self.connection_errors:,}|{self.serving_errors:,}'

    def collect(self, *, active: int) -> None:
        self.active = active

    def open(self) -> None:
        self.opened += 1

    def close(self) -> None:
        self.closed += 1

    def send(self, *, data: bytes, entropy: Optional[Entropy]) -> None:
        self.bytes_sent += len(data)

        if entropy:
            value = entropy.calculate(data=data)
            if value < self.entropy_min or self.entropy_min == 0.0:
                self.entropy_min = value
            if value > self.entropy_max:
                self.entropy_max = value

            self.entropy_count += 1
            self.entropy_sum += value
            self.entropy_avg = self.entropy_sum / self.entropy_count if self.entropy_count > 0 else 0.0

    def recv(self, *, data: bytes, entropy: Optional[Entropy]) -> None:
        self.bytes_recv += len(data)

        if entropy:
            value = entropy.calculate(data=data)
            if value < self.entropy_min or self.entropy_min == 0.0:
                self.entropy_min = value
            if value > self.entropy_max:
                self.entropy_max = value

            self.entropy_count += 1
            self.entropy_sum += value
            self.entropy_avg = self.entropy_sum / self.entropy_count if self.entropy_count > 0 else 0.0

    def token_error(self) -> None:
        self.token_errors += 1

    def timeout_error(self) -> None:
        self.timeout_errors += 1

    def connection_error(self) -> None:
        self.connection_errors += 1

    def serving_error(self) -> None:
        self.serving_errors += 1


@dataclass(kw_only=True)
class DatagramTelemetry:
    active: int = 0
    opened: int = 0
    closed: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    bytes_sent: int = 0
    bytes_recv: int = 0
    min_packet_size: int = 0
    max_packet_size: int = 0
    packet_count: int = 0
    packet_sum: int = 0
    avg_packet_size: int = 0
    entropy_min: float = 0.0
    entropy_max: float = 0.0
    entropy_count: int = 0
    entropy_sum: float = 0.0
    entropy_avg: float = 0.0
    processing_errors: int = 0
    token_errors: int = 0
    type_errors: int = 0
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
            f'\tpackets sent|received: {self.packets_sent:,}|{self.packets_recv:,}\n' \
            f'\tbytes sent|received: {self.bytes_sent:,}|{self.bytes_recv:,}\n' \
            f'\tmin|avg|max packet size: {self.min_packet_size:,}|{self.avg_packet_size:,}|{self.max_packet_size:,}\n' \
            f'\tentropy min|avg|max: {self.entropy_min:.4f}|{self.entropy_avg:.4f}|{self.entropy_max:.4f}\n' \
            f'\tprocessing|token|type errors: {self.processing_errors:,}|{self.token_errors:,}' \
            f'|{self.type_errors:,}\n' \
            f'\ttimeout|connection|serving|resending errors: {self.timeout_errors:,}|{self.connection_errors:,}' \
            f'|{self.serving_errors:,}|{self.resending_errors:,}\n' \
            f'\tsend|recv buf overloads: {self.send_buf_overloads:,}|{self.recv_buf_overloads:,}'

    def collect(self, *, active: int) -> None:
        self.active = active

    def open(self) -> None:
        self.opened += 1

    def close(self) -> None:
        self.closed += 1

    def send(self, *, data: bytes, entropy: Optional[Entropy]) -> None:
        self.packets_sent += 1
        self.bytes_sent += len(data)
        self.packet_count += 1
        self.packet_sum += len(data)
        self.avg_packet_size = int(self.packet_sum / self.packet_count)

        if len(data) < self.min_packet_size or self.min_packet_size == 0:
            self.min_packet_size = len(data)
        if len(data) > self.max_packet_size:
            self.max_packet_size = len(data)

        if entropy:
            value = entropy.calculate(data=data)
            if value < self.entropy_min or self.entropy_min == 0.0:
                self.entropy_min = value
            if value > self.entropy_max:
                self.entropy_max = value

            self.entropy_count += 1
            self.entropy_sum += value
            self.entropy_avg = self.entropy_sum / self.entropy_count if self.entropy_count > 0 else 0.0

    def recv(self, *, data: bytes, entropy: Optional[Entropy]) -> None:
        self.packets_recv += 1
        self.bytes_recv += len(data)
        self.packet_count += 1
        self.packet_sum += len(data)
        self.avg_packet_size = int(self.packet_sum / self.packet_count)

        if len(data) < self.min_packet_size or self.min_packet_size == 0:
            self.min_packet_size = len(data)
        if len(data) > self.max_packet_size:
            self.max_packet_size = len(data)

        if entropy:
            value = entropy.calculate(data=data)
            if value < self.entropy_min or self.entropy_min == 0.0:
                self.entropy_min = value
            if value > self.entropy_max:
                self.entropy_max = value

            self.entropy_count += 1
            self.entropy_sum += value
            self.entropy_avg = self.entropy_sum / self.entropy_count if self.entropy_count > 0 else 0.0

    def processing_error(self) -> None:
        self.processing_errors += 1

    def token_error(self) -> None:
        self.token_errors += 1

    def type_error(self) -> None:
        self.type_errors += 1

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
