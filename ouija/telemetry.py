import datetime


class Telemetry:
    links: int = 0
    opened: int = 0
    closed: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    decoding_errors: int = 0
    processing_errors: int = 0
    token_errors: int = 0
    type_errors: int = 0
    timeout_errors: int = 0
    connection_errors: int = 0
    serving_errors: int = 0
    resending_errors: int = 0
    sent_buf_overloads: int = 0
    recv_buf_overloads: int = 0
    max_packet_size: int = 0
    resent: int = 0
    unfinished: int = 0

    def __str__(self):
        return \
            f'{datetime.datetime.now()}\n' \
            f'\tlinks: {self.links}\n' \
            f'\topened/closed: {self.opened}/{self.closed}\n' \
            f'\tpackets sent/received: {self.packets_sent}/{self.packets_received}\n' \
            f'\tbytes sent/received: {self.bytes_sent}/{self.bytes_received}\n' \
            f'\tdecoding/processing/token/type/timeout/connection/serving/resending errors: ' \
            f'{self.decoding_errors}/{self.processing_errors}/{self.token_errors}/{self.type_errors}/' \
            f'{self.timeout_errors}/{self.connection_errors}/{self.serving_errors}/{self.resending_errors}\n' \
            f'\tsent/received buffer overloads: {self.sent_buf_overloads}/{self.recv_buf_overloads}\n' \
            f'\tmax packet size: {self.max_packet_size}\n' \
            f'\tresent/unfinished: {self.resent}/{self.unfinished}'
