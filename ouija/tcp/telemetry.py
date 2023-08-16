from dataclasses import dataclass
import datetime


@dataclass(kw_only=True)
class Telemetry:
    links: int = 0
    opened: int = 0
    closed: int = 0
    bytes_sent: int = 0
    bytes_recv: int = 0
    token_errors: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    serving_errors: int = 0

    def __str__(self) -> str:
        return \
            f'{datetime.datetime.now()}\n' \
            f'\tlinks: {self.links:,}\n' \
            f'\topened|closed: {self.opened:,}|{self.closed:,}\n' \
            f'\tbytes sent|received: {self.bytes_sent:,}|{self.bytes_recv:,}\n' \
            f'\ttoken|timeout|connection|serving errors: {self.token_errors:,}|{self.timeout_errors:,}' \
            f'|{self.connection_errors:,}|{self.serving_errors:,}'

    def link(self, *, links: int) -> None:
        self.links = links

    def open(self) -> None:
        self.opened += 1

    def close(self) -> None:
        self.closed += 1

    def send(self, *, data: bytes) -> None:
        self.bytes_sent += len(data)

    def recv(self, *, data: bytes) -> None:
        self.bytes_recv += len(data)

    def token_error(self) -> None:
        self.token_errors += 1

    def timeout_error(self) -> None:
        self.timeout_errors += 1

    def connection_error(self) -> None:
        self.connection_errors += 1

    def serving_error(self) -> None:
        self.serving_errors += 1
