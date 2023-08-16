from dataclasses import dataclass

from cryptography.fernet import Fernet


@dataclass(kw_only=True)
class Tuning:
    fernet: Fernet
    token: str
    serving_timeout: float
    message_buffer: int
    tcp_buffer: int
    tcp_timeout: float
