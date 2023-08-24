from dataclasses import dataclass

from cryptography.fernet import Fernet


@dataclass(kw_only=True)
class StreamTuning:
    fernet: Fernet
    token: str
    entropy: bool
    serving_timeout: float
    tcp_buffer: int
    tcp_timeout: float
    message_timeout: float


@dataclass(kw_only=True)
class DatagramTuning:
    fernet: Fernet
    token: str
    entropy: bool
    serving_timeout: float
    tcp_buffer: int
    tcp_timeout: float
    udp_payload: int
    udp_timeout: float
    udp_retries: int
    udp_capacity: int
    udp_resend_sleep: float
