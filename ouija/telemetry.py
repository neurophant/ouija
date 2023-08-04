import dataclasses
import datetime


@dataclasses.dataclass(kw_only=True)
class Telemetry:
    links: int = 0
    opened: int = 0
    closed: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    min_packet_size: int = 0
    max_packet_size: int = 0
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
            f'\tlinks: {self.links:,}\n' \
            f'\topened|closed: {self.opened:,}|{self.closed:,}\n' \
            f'\tpackets sent|received: {self.packets_sent:,}|{self.packets_received:,}\n' \
            f'\tbytes sent|received: {self.bytes_sent:,}|{self.bytes_received:,}\n' \
            f'\tmin|max packet size: {self.min_packet_size}|{self.max_packet_size}\n' \
            f'\tprocessing|token|type errors: {self.processing_errors:,}|{self.token_errors:,}' \
            f'|{self.type_errors:,}\n' \
            f'\ttimeout|connection|serving|resending errors: {self.timeout_errors:,}|{self.connection_errors:,}' \
            f'|{self.serving_errors:,}|{self.resending_errors:,}\n' \
            f'\tsend|recv buf overloads: {self.send_buf_overloads:,}|{self.recv_buf_overloads:,}'

    def link(self, *, links: int) -> None:
        self.links = links

    def open(self) -> None:
        self.opened += 1

    def close(self) -> None:
        self.closed += 1

    def send(self, *, data: bytes) -> None:
        self.packets_sent += 1
        self.bytes_sent += len(data)
        if len(data) < self.min_packet_size or self.min_packet_size == 0:
            self.min_packet_size = len(data)
        if len(data) > self.max_packet_size:
            self.max_packet_size = len(data)

    def recv(self, *, data: bytes) -> None:
        self.packets_received += 1
        self.bytes_received += len(data)
        if len(data) < self.min_packet_size or self.min_packet_size == 0:
            self.min_packet_size = len(data)
        if len(data) > self.max_packet_size:
            self.max_packet_size = len(data)

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
