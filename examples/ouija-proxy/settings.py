import sys

from cryptography.fernet import Fernet


sys.path.append('../../')


PROXY_HOST = '0.0.0.0'
PROXY_PORT = 50000

fernet = Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=')
TOKEN = 'terces'
SERVING_TIMEOUT = 30
TCP_BUFFER = 1024
TCP_TIMEOUT = 1
UDP_PAYLOAD = 512
UDP_TIMEOUT = 3
UDP_RETRIES = 5
UDP_CAPACITY = 10000
