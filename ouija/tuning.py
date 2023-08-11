import dataclasses

from cryptography.fernet import Fernet


@dataclasses.dataclass(kw_only=True)
class Tuning:
    fernet: Fernet
    token: str
    serving_timeout: float
    tcp_buffer: int
    tcp_timeout: float
    udp_payload: int
    udp_timeout: float
    udp_retries: int
    udp_capacity: int
    udp_resend_sleep: float
