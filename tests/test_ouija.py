import asyncio
from unittest.mock import AsyncMock

import pytest

from ouija import Packet, Phase


@pytest.mark.asyncio
async def test_send(ouija_test):
    ouija_test.sendto = AsyncMock()
    await ouija_test.send(data=b'test data')
    ouija_test.sendto.assert_awaited_with(data=b'test data')


@pytest.mark.asyncio
async def test_send_packet(ouija_test):
    ouija_test.send = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=b'test data', drain=True)
    await ouija_test.send_packet(packet=packet)
    ouija_test.send.assert_awaited()


@pytest.mark.asyncio
async def test_send_retry_success(ouija_test):
    ouija_test.send_packet = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=b'test data', drain=True)
    event = asyncio.Event()
    event.set()
    result = await ouija_test.send_retry(packet=packet, event=event)
    ouija_test.send_packet.assert_awaited()
    assert result


@pytest.mark.asyncio
async def test_send_retry_fail(ouija_test):
    ouija_test.send_packet = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=b'test data', drain=True)
    event = asyncio.Event()
    result = await ouija_test.send_retry(packet=packet, event=event)
    ouija_test.send_packet.assert_awaited()
    assert not result


@pytest.mark.asyncio
async def test_read(ouija_test):
    ouija_test.reader = AsyncMock()
    await ouija_test.read()
    ouija_test.reader.read.assert_called()


@pytest.mark.asyncio
async def test_write(ouija_test):
    ouija_test.writer = AsyncMock()
    await ouija_test.write(data=b'test data', drain=False)
    ouija_test.writer.write.assert_called()


@pytest.mark.asyncio
async def test_write_drain(ouija_test):
    ouija_test.writer = AsyncMock()
    await ouija_test.write(data=b'test data', drain=True)
    ouija_test.writer.write.assert_called()
    ouija_test.writer.drain.assert_awaited()
