import base64
import re
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

import pbjson
from cryptography.fernet import Fernet


HTTP_PORT = 80
HTTPS_PORT = 443
CONNECT = 'CONNECT'
SEPARATOR = b'\r\n\r\n'
CONNECTION_ESTABLISHED = b'HTTP/1.1 200 Connection Established\r\n\r\n'


class Parser:
    pattern = re.compile(
        br'(?P<method>[a-zA-Z]+) '
        br'(?P<uri>(\w+://)'
        br'?(?P<host>[^\s\'\"<>\[\]{}|/:]+)'
        br'(:(?P<port>\d+))'
        br'?[^\s\'\"<>\[\]{}|]*) '
    )
    uri: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    method: Optional[str] = None
    error: bool = False

    def __init__(self, *, data: bytes) -> None:
        rex = self.pattern.match(data)
        if rex:
            self.uri = self.to_str(item=rex.group('uri'))
            self.host = self.to_str(item=rex.group('host'))
            self.method = self.to_str(item=rex.group('method'))
            self.port = self.to_int(item=rex.group('port'))
        else:
            self.error = True

    @staticmethod
    def to_str(*, item: Optional[bytes]) -> Optional[str]:
        if item:
            return item.decode('charmap')

    @staticmethod
    def to_int(*, item: Optional[bytes]) -> Optional[int]:
        if item:
            return int(item)

    def __str__(self) -> str:
        return str(dict(URI=self.uri, HOST=self.host, PORT=self.port, METHOD=self.method))


MAPPING = {
    'phase': 'pe',
    'ack': 'ak',
    'token': 'tn',
    'host': 'ht',
    'port': 'pt',
    'seq': 'sq',
    'data': 'da',
    'drain': 'dn',
}


@dataclass(kw_only=True)
class Message:
    token: str
    host: Optional[str] = None
    port: Optional[int] = None

    @staticmethod
    def message(*, data: bytes, fernet: Fernet) -> 'Message':
        json = pbjson.loads(fernet.decrypt(data[:-len(SEPARATOR)]))
        return Message(
            token=json.get(MAPPING['token']),
            host=json.get(MAPPING['host'], None),
            port=json.get(MAPPING['port'], None),
        )

    def binary(self, *, fernet: Fernet) -> bytes:
        json = {MAPPING[k]: v for k, v in self.__dict__.items() if v is not None}
        return fernet.encrypt(pbjson.dumps(json)) + SEPARATOR

    @staticmethod
    def encrypt(*, data: bytes, fernet: Fernet) -> bytes:
        return fernet.encrypt(data) + SEPARATOR

    @staticmethod
    def decrypt(*, data: bytes, fernet: Fernet) -> bytes:
        return fernet.decrypt(data[:-len(SEPARATOR)])


class Phase(IntEnum):
    OPEN = 1
    DATA = 2
    CLOSE = 3


@dataclass(kw_only=True)
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
            phase=Phase(json.get(MAPPING['phase'])),
            ack=json.get(MAPPING['ack']),
            token=json.get(MAPPING['token'], None),
            host=json.get(MAPPING['host'], None),
            port=json.get(MAPPING['port'], None),
            seq=json.get(MAPPING['seq'], None),
            data=json.get(MAPPING['data'], None),
            drain=json.get(MAPPING['drain'], None),
        )

    def binary(self, *, fernet: Fernet) -> bytes:
        json = {MAPPING[k]: v for k, v in self.__dict__.items() if v is not None}
        return base64.urlsafe_b64decode(fernet.encrypt(pbjson.dumps(json)))


@dataclass(kw_only=True)
class Sent:
    data: bytes
    timestamp: float = field(default_factory=time.time)
    retries: int = 1


@dataclass(kw_only=True)
class Received:
    data: bytes
    drain: bool
