from cryptography.fernet import Fernet


class Tuning:
    fernet: Fernet
    token: str
    serving_timeout: int
    tcp_buffer: int
    tcp_timeout: int
    udp_payload: int
    udp_timeout: int
    udp_retries: int
    udp_capacity: int

    def __init__(
            self,
            *,
            fernet: Fernet,
            token: str,
            serving_timeout: int,
            tcp_buffer: int,
            tcp_timeout: int,
            udp_payload: int,
            udp_timeout: int,
            udp_retries: int,
            udp_capacity: int,
    ) -> None:
        self.fernet = fernet
        self.token = token
        self.serving_timeout = serving_timeout
        self.tcp_buffer = tcp_buffer
        self.tcp_timeout = tcp_timeout
        self.udp_payload = udp_payload
        self.udp_timeout = udp_timeout
        self.udp_retries = udp_retries
        self.udp_capacity = udp_capacity
