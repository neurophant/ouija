import base64

from cryptography.fernet import Fernet


class Cipher:
    """Base class for cipher implementation"""

    def encrypt(self, *, data: bytes) -> bytes:
        raise NotImplementedError

    def decrypt(self, *, data: bytes) -> bytes:
        raise NotImplementedError


class FernetCipher(Cipher):
    """Fernet cipher"""

    key: str
    fernet: Fernet

    def __init__(self, *, key: str) -> None:
        self.key = key
        self.fernet = Fernet(self.key)

    def encrypt(self, *, data: bytes) -> bytes:
        return base64.urlsafe_b64decode(self.fernet.encrypt(data))

    def decrypt(self, *, data: bytes) -> bytes:
        return self.fernet.decrypt(base64.urlsafe_b64encode(data))
