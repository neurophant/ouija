import sys

from cryptography.fernet import Fernet


sys.path.append('../../')


PROXY_HOST = '127.0.0.1'
PROXY_PORT = 50000

fernet = Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=')
TOKEN = 'terces'
BUFFER = 1024
SERVING = 30
TIMEOUT = 3
PAYLOAD = 256
RETRIES = 5
CAPACITY = 10000
