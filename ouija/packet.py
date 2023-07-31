from enum import IntEnum
from typing import Optional

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
}


class Packet:
    phase: Phase
    ack: bool
    token: Optional[str]
    host: Optional[str]
    port: Optional[int]
    seq: Optional[int]
    data: Optional[bytes]

    def __init__(
            self, 
            *, 
            phase: Phase,
            ack: bool,
            token: Optional[str] = None,
            host: Optional[str] = None,
            port: Optional[int] = None,
            seq: Optional[int] = None,
            data: Optional[bytes] = None,
    ) -> None:
        self.phase = phase
        self.ack = ack
        self.token = token
        self.host = host
        self.port = port
        self.seq = seq
        self.data = data

    @classmethod
    async def packet(cls, *, data: bytes, fernet: Fernet) -> 'Packet':
        json = pbjson.loads(fernet.decrypt(data))
        return Packet(
            phase=json.get(TOKENS['phase']),
            ack=json.get(TOKENS['ack']),
            token=json.get(TOKENS['token'], None),
            host=json.get(TOKENS['host'], None),
            port=json.get(TOKENS['port'], None),
            seq=json.get(TOKENS['seq'], None),
            data=json.get(TOKENS['data'], None),
        )

    async def binary(self, *, fernet: Fernet) -> bytes:
        return fernet.encrypt(pbjson.dumps({TOKENS[k]: v for k, v in self.__dict__.items() if v is not None}))
