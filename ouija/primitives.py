import time


class Sent:
    timestamp: int
    data: bytes
    retries: int

    def __init__(self, *, data: bytes):
        self.timestamp = int(time.time())
        self.data = data
        self.retries = 1


class Received:
    data: bytes
    drain: bool

    def __init__(self, *, data: bytes, drain: bool):
        self.data = data
        self.drain = drain
