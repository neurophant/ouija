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

    def __init__(self, *, data: bytes):
        self.data = data
