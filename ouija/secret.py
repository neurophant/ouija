import uuid

from cryptography.fernet import Fernet


def main() -> None:
    print(f'Cipher key: {Fernet.generate_key().decode("utf8")}\nToken: {uuid.uuid4()}\n')


if __name__ == '__main__':
    main()
