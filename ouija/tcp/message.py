from dataclasses import dataclass
from typing import Optional

import pbjson
from cryptography.fernet import Fernet


TOKENS = {
    'token': 'tn',
    'host': 'ht',
    'port': 'pt',
}


SEPARATOR = b'\r\n\r\n'


@dataclass(kw_only=True)
class Message:
    token: str
    host: Optional[str] = None
    port: Optional[int] = None

    @staticmethod
    def message(*, data: bytes, fernet: Fernet) -> 'Message':
        json = pbjson.loads(fernet.decrypt(data[:-len(SEPARATOR)]))
        return Message(
            token=json.get(TOKENS['token']),
            host=json.get(TOKENS['host'], None),
            port=json.get(TOKENS['port'], None),
        )

    def binary(self, *, fernet: Fernet) -> bytes:
        json = {TOKENS[k]: v for k, v in self.__dict__.items() if v is not None}
        return fernet.encrypt(pbjson.dumps(json)) + SEPARATOR

    @staticmethod
    def encrypt(*, data: bytes, fernet: Fernet) -> bytes:
        return fernet.encrypt(data) + SEPARATOR

    @staticmethod
    def decrypt(*, data: bytes, fernet: Fernet) -> bytes:
        return fernet.decrypt(data[:-len(SEPARATOR)])
