import sys

from cryptography.fernet import Fernet


sys.path.append('../../')


PROXY_HOST = '127.0.0.1'
PROXY_PORT = 23000

fernet = Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=')
TOKEN = 'terces'
SERVING = 30
TIMEOUT = 2
PAYLOAD = 1024
RETRIES = 5
CAPACITY = 1000
