from dataclasses import dataclass
from typing import Optional

from .cipher import Cipher
from .entropy import Entropy


@dataclass(kw_only=True)
class StreamTuning:
    """TCP relay/proxy and connector/link tuning"""

    cipher: Optional[Cipher]
    entropy: Optional[Entropy]
    token: str
    serving_timeout: float
    tcp_buffer: int
    tcp_timeout: float
    message_timeout: float


@dataclass(kw_only=True)
class DatagramTuning:
    """UDP relay/proxy and connector/link tuning"""

    cipher: Optional[Cipher]
    entropy: Optional[Entropy]
    token: str
    serving_timeout: float
    tcp_buffer: int
    tcp_timeout: float
    udp_min_payload: int
    udp_max_payload: int
    udp_timeout: float
    udp_retries: int
    udp_capacity: int
    udp_resend_sleep: float
