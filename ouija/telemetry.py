import datetime


class Telemetry:
    links: int = 0
    opened: int = 0
    closed: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    processing_errors: int = 0
    token_errors: int = 0
    type_errors: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    serving_errors: int = 0
    resending_errors: int = 0

    def __str__(self):
        return \
            f'{datetime.datetime.now()}\n' \
            f'\tlinks: {self.links:,}\n' \
            f'\topened|closed: {self.opened:,}|{self.closed:,}\n' \
            f'\tpackets sent|received: {self.packets_sent:,}|{self.packets_received:,}\n' \
            f'\tbytes sent|received: {self.bytes_sent:,}|{self.bytes_received:,}\n' \
            f'\tprocessing|token|type errors: {self.processing_errors:,}|{self.token_errors:,}' \
            f'|{self.type_errors:,}\n' \
            f'\ttimeout|connection|serving|resending errors: {self.timeout_errors:,}|{self.connection_errors:,}' \
            f'|{self.serving_errors:,}|{self.resending_errors:,}\n'
