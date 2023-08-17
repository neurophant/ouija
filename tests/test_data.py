import pytest

from ouija import Parser, Packet, Phase


def test_parser_connect():
    request = Parser(data=b'CONNECT example.com:443 HTTP/1.1')

    assert request.method == 'CONNECT'
    assert request.uri == 'example.com:443'
    assert request.host == 'example.com'
    assert request.port == 443
    assert not request.error


def test_parser_get():
    request = Parser(data=b'GET example.com HTTP/1.1')

    assert not request.error


def test_parser_error():
    request = Parser(data=b'GET /index.html HTTP/1.1')

    assert request.error


def test_parser():
    request = Parser(data=b'CONNECT example.com:443 HTTP/1.1')
    expected = dict(URI=request.uri, HOST=request.host, PORT=request.port, METHOD=request.method)

    assert str(request) == str(expected)


@pytest.mark.parametrize('packet', (
    Packet(phase=Phase.OPEN, ack=False, token='secret', host='example.com', port=443),
    Packet(phase=Phase.OPEN, ack=True, token='secret'),
    Packet(phase=Phase.DATA, ack=False, seq=0, data=b'test data 1', drain=False),
    Packet(phase=Phase.DATA, ack=False, seq=1, data=b'test data 2', drain=True),
    Packet(phase=Phase.DATA, ack=True, seq=0),
    Packet(phase=Phase.DATA, ack=True, seq=1),
    Packet(phase=Phase.CLOSE, ack=False),
    Packet(phase=Phase.CLOSE, ack=True),
))
def test_packet(packet, fernet_test):
    encoded = packet.binary(fernet=fernet_test)
    decoded = Packet.packet(data=encoded, fernet=fernet_test)

    assert decoded == packet
