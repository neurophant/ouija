import pytest

from ouija import Cipher


@pytest.mark.xfail(raises=NotImplementedError)
def test_cipher_encrypt(data_test):
    cipher = Cipher()
    cipher.encrypt(data=data_test)


@pytest.mark.xfail(raises=NotImplementedError)
def test_cipher_decrypt(data_test):
    cipher = Cipher()
    cipher.decrypt(data=data_test)


def test_fernet_cipher(cipher_test, data_test):
    encrypted = cipher_test.encrypt(data=data_test)
    decrypted = cipher_test.decrypt(data=encrypted)

    assert decrypted == data_test
