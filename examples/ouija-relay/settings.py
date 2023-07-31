import sys

from cryptography.fernet import Fernet


sys.path.append('../../')


RELAY_HOST = '127.0.0.1'
RELAY_PORT = 8000
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 23000

fernet = Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=')
TOKEN = 'terces'
BUFFER = 4096
SERVING = 30
TIMEOUT = 3
PAYLOAD = 512
RETRIES = 5
CAPACITY = 1000
