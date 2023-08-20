import json
from enum import StrEnum

from cryptography.fernet import Fernet


class Mode(StrEnum):
    RELAY = 'RELAY'
    PROXY = 'PROXY'


class Protocol(StrEnum):
    TCP = 'TCP'
    UDP = 'UDP'


class Config:
    protocol: Protocol
    mode: Mode
    debug: bool
    monitor: bool
    relay_host: str
    relay_port: int
    proxy_host: str
    proxy_port: int
    fernet: Fernet
    token: str
    serving_timeout: float
    tcp_buffer: int
    tcp_timeout: float
    message_timeout: float
    udp_payload: int
    udp_timeout: float
    udp_retries: int
    udp_capacity: int
    udp_resend_sleep: float

    def __init__(self, *, path: str) -> None:
        with open(path, 'r') as fp:
            json_dict = json.load(fp)

        self.protocol = Protocol(json_dict.get('protocol'))
        self.mode = Mode(json_dict.get('mode'))
        self.debug = json_dict.get('debug')
        self.monitor = json_dict.get('monitor')

        self.relay_host = json_dict.get('relay_host', None)
        self.relay_port = json_dict.get('relay_port', None)
        self.proxy_host = json_dict.get('proxy_host')
        self.proxy_port = json_dict.get('proxy_port')

        self.fernet = Fernet(json_dict.get('key'))
        self.token = json_dict.get('token')
        self.serving_timeout = json_dict.get('serving_timeout')
        self.tcp_buffer = json_dict.get('tcp_buffer')
        self.tcp_timeout = json_dict.get('tcp_timeout')
        self.message_timeout = json_dict.get('message_timeout', None)
        self.udp_payload = json_dict.get('udp_payload', None)
        self.udp_timeout = json_dict.get('udp_timeout', None)
        self.udp_retries = json_dict.get('udp_retries', None)
        self.udp_capacity = json_dict.get('udp_capacity', None)
        self.udp_resend_sleep = json_dict.get('udp_resend_sleep', None)
