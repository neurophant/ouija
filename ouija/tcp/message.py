from dataclasses import dataclass
import base64
from typing import Optional

import pbjson
from cryptography.fernet import Fernet


TOKENS = {
    'token': 'tn',
    'host': 'ht',
    'port': 'pt',
}


@dataclass(kw_only=True)
class Message:
    token: str
    host: Optional[str] = None
    port: Optional[int] = None

    @staticmethod
    def message(*, data: bytes, fernet: Fernet) -> 'Message':
        json = pbjson.loads(fernet.decrypt(base64.urlsafe_b64encode(data)))
        return Message(
            token=json.get(TOKENS['token']),
            host=json.get(TOKENS['host'], None),
            port=json.get(TOKENS['port'], None),
        )

    def binary(self, *, fernet: Fernet) -> bytes:
        json = {TOKENS[k]: v for k, v in self.__dict__.items() if v is not None}
        return base64.urlsafe_b64decode(fernet.encrypt(pbjson.dumps(json)))

    @staticmethod
    def encrypt(*, data: bytes, fernet: Fernet) -> bytes:
        return base64.urlsafe_b64decode(fernet.encrypt(data))

    @staticmethod
    def decrypt(*, data: bytes, fernet: Fernet) -> bytes:
        return fernet.decrypt(base64.urlsafe_b64encode(data))
