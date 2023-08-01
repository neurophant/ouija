import sys

from cryptography.fernet import Fernet


sys.path.append('../../')


RELAY_HOST = '127.0.0.1'
RELAY_PORT = 9000
PROXY_HOST = '127.0.0.1'
PROXY_PORT = 50000

fernet = Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=')
TOKEN = 'terces'
SERVING = 60
TIMEOUT = 5
PAYLOAD = 768
RETRIES = 5
CAPACITY = 1000
