import dataclasses

from cryptography.fernet import Fernet


@dataclasses.dataclass(kw_only=True)
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
