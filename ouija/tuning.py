from dataclasses import dataclass
from typing import Optional

from cryptography.fernet import Fernet

from .entropy import Entropy


@dataclass(kw_only=True)
class StreamTuning:
    fernet: Fernet
    token: str
    entropy: Optional[Entropy]
    serving_timeout: float
    tcp_buffer: int
    tcp_timeout: float
    message_timeout: float


@dataclass(kw_only=True)
class DatagramTuning:
    fernet: Fernet
    token: str
    entropy: Optional[Entropy]
    serving_timeout: float
    tcp_buffer: int
    tcp_timeout: float
    udp_payload: int
    udp_timeout: float
    udp_retries: int
    udp_capacity: int
    udp_resend_sleep: float
