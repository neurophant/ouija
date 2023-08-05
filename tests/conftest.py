import pytest
from cryptography.fernet import Fernet


@pytest.fixture
def fernet():
    return Fernet(Fernet.generate_key())
