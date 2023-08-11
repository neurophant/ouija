import dataclasses
import time
from enum import IntEnum
from typing import Optional
import base64

import pbjson
from cryptography.fernet import Fernet


class Phase(IntEnum):
    OPEN = 1
    DATA = 2
    CLOSE = 3


TOKENS = {
    'phase': 'pe',
    'ack': 'ak',
    'token': 'tn',
    'host': 'ht',
    'port': 'pt',
    'seq': 'sq',
    'data': 'da',
    'drain': 'dn',
}


@dataclasses.dataclass(kw_only=True)
class Packet:
    phase: Phase
    ack: bool
    token: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    seq: Optional[int] = None
    data: Optional[bytes] = None
    drain: Optional[bool] = None

    @staticmethod
    def packet(*, data: bytes, fernet: Fernet) -> 'Packet':
        json = pbjson.loads(fernet.decrypt(base64.urlsafe_b64encode(data)))
        return Packet(
            phase=Phase(json.get(TOKENS['phase'])),
            ack=json.get(TOKENS['ack']),
            token=json.get(TOKENS['token'], None),
            host=json.get(TOKENS['host'], None),
            port=json.get(TOKENS['port'], None),
            seq=json.get(TOKENS['seq'], None),
            data=json.get(TOKENS['data'], None),
            drain=json.get(TOKENS['drain'], None),
        )

    def binary(self, *, fernet: Fernet) -> bytes:
        json = {TOKENS[k]: v for k, v in self.__dict__.items() if v is not None}
        return base64.urlsafe_b64decode(fernet.encrypt(pbjson.dumps(json)))


@dataclasses.dataclass(kw_only=True)
class Sent:
    data: bytes
    timestamp: float = time.time()
    retries: int = 1


@dataclasses.dataclass(kw_only=True)
class Received:
    data: bytes
    drain: bool
