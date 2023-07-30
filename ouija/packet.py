from enum import IntEnum
from typing import Optional

import pbjson
from cryptography.fernet import Fernet


class PacketType(IntEnum):
    CONNECT = 1
    DATA = 2
    DISCONNECT = 3


class Packet:
    token: str
    packet_type: PacketType
    ack: bool
    seq: Optional[int]
    host: Optional[str]
    port: Optional[int]
    data: Optional[bytes]

    def __init__(
            self, 
            *, 
            token: str,
            packet_type: PacketType, 
            ack: bool,
            seq: Optional[int] = None, 
            host: Optional[str] = None,
            port: Optional[int] = None,
            data: Optional[bytes] = None,
    ) -> None:
        self.token = token
        self.packet_type = packet_type
        self.ack = ack
        self.seq = seq
        self.host = host
        self.port = port
        self.data = data

    @classmethod
    async def packet(cls, *, data: bytes, fernet: Fernet) -> 'Packet':
        json = pbjson.loads(fernet.decrypt(data))
        return Packet(
            token=json['token'],
            packet_type=json['packet_type'],
            ack=json['ack'],
            seq=json['seq'],
            host=json['host'],
            port=json['port'],
            data=json['data'],
        )

    async def binary(self, *, fernet: Fernet) -> bytes:
        return fernet.encrypt(pbjson.dumps(self.__dict__))
