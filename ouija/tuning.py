from cryptography.fernet import Fernet


class Tuning:
    fernet: Fernet
    token: str
    buffer: int
    serving: int
    timeout: int
    payload: int
    retries: int
    capacity: int

    def __init__(
            self,
            *,
            fernet: Fernet,
            token: str,
            buffer: int,
            serving: int,
            timeout: int,
            payload: int,
            retries: int,
            capacity: int,
    ) -> None:
        self.fernet = fernet
        self.token = token
        self.buffer = buffer
        self.serving = serving
        self.timeout = timeout
        self.payload = payload
        self.retries = retries
        self.capacity = capacity
