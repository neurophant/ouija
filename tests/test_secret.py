import uuid

from cryptography.fernet import Fernet
from pytest_mock import MockerFixture

from ouija.secret import main


def test_main(mocker: MockerFixture, capsys):
    cipher_key = Fernet.generate_key()
    mocked_fernet = mocker.patch('ouija.secret.Fernet')
    mocked_fernet.generate_key.return_value = cipher_key
    token = uuid.uuid4()
    mocked_uuid = mocker.patch('ouija.secret.uuid')
    mocked_uuid.uuid4.return_value = token

    main()

    captured = capsys.readouterr()
    assert captured.out == f'Cipher key: {cipher_key.decode("utf8")}\nToken: {token}\n\n'
