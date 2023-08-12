import pytest

from ouija import Phase, Packet


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
