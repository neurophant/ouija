from unittest.mock import AsyncMock

import pytest

from ouija import Packet, Phase


@pytest.mark.asyncio
async def test_send(ouija_test):
    ouija_test.sendto = AsyncMock()
    await ouija_test.send(data=b'test data')
    ouija_test.sendto.assert_called_with(data=b'test data')


@pytest.mark.asyncio
async def test_send_packet(ouija_test, fernet_test):
    ouija_test.send = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=b'test data', drain=True)
    await ouija_test.send_packet(packet=packet)
    ouija_test.send.assert_called()
