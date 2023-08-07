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


@pytest.mark.asyncio
async def test_recv(ouija_test):
    ouija_test.write = AsyncMock()
    ouija_test.send_ack_data = AsyncMock()
    await ouija_test.recv(seq=1, data=b'test data', drain=False)
    await ouija_test.recv(seq=2, data=b'test data', drain=False)
    await ouija_test.recv(seq=0, data=b'test data', drain=False)
    ouija_test.write.assert_awaited()
    ouija_test.send_ack_data.assert_awaited()


@pytest.mark.asyncio
async def test_recv_overload(ouija_test):
    ouija_test.write = AsyncMock()
    ouija_test.send_ack_data = AsyncMock()
    ouija_test.close = AsyncMock()
    ouija_test.tuning.udp_capacity = 1
    await ouija_test.recv(seq=1, data=b'test data', drain=False)
    await ouija_test.recv(seq=2, data=b'test data', drain=False)
    ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_enqueue_send(ouija_test):
    ouija_test.send_packet = AsyncMock()
    await ouija_test.enqueue_send(data=b'test data', drain=True)
    ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_enqueue_send_overload(ouija_test):
    ouija_test.send_packet = AsyncMock()
    ouija_test.close = AsyncMock()
    ouija_test.tuning.udp_capacity = 1
    await ouija_test.enqueue_send(data=b'test data', drain=False)
    await ouija_test.enqueue_send(data=b'test data', drain=True)
    ouija_test.send_packet.assert_awaited()
    ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_dequeue_send(ouija_test):
    ouija_test.sent_buf = AsyncMock()
    await ouija_test.dequeue_send(seq=1)
    ouija_test.sent_buf.pop.assert_called()


@pytest.mark.asyncio
async def test_send_open(ouija_test):
    ouija_test.send_retry = AsyncMock()
    await ouija_test.send_open()
    ouija_test.send_retry.assert_awaited()


@pytest.mark.asyncio
async def test_send_ack_open(ouija_test):
    ouija_test.send_packet = AsyncMock()
    await ouija_test.send_ack_open()
    ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_check_token_ok(ouija_test):
    assert await ouija_test.check_token(token='secret')


@pytest.mark.asyncio
async def test_check_token_error(ouija_test):
    ouija_test.close = AsyncMock()
    result = await ouija_test.check_token(token='token')
    ouija_test.close.assert_awaited()
    assert not result


@pytest.mark.asyncio
async def test_send_ack_data(ouija_test):
    ouija_test.send_packet = AsyncMock()
    await ouija_test.send_ack_data(seq=0)
    ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_send_close(ouija_test):
    ouija_test.send_retry = AsyncMock()
    await ouija_test.send_close()
    ouija_test.send_retry.assert_awaited()


@pytest.mark.asyncio
async def test_send_ack_close(ouija_test):
    ouija_test.send_packet = AsyncMock()
    await ouija_test.send_ack_close()
    ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_process_packet_open_ok(ouija_test):
    ouija_test.check_token = AsyncMock(return_value=True)
    ouija_test.on_open = AsyncMock(return_value=True)
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token='secret',
        host='example.com',
        port=443,
    )
    await ouija_test.process_packet(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.check_token.assert_awaited()
    ouija_test.on_open.assert_awaited()


@pytest.mark.asyncio
async def test_process_packet_open_check_token_err(ouija_test):
    ouija_test.check_token = AsyncMock(return_value=False)
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token='secret',
        host='example.com',
        port=443,
    )
    await ouija_test.process_packet(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.check_token.assert_awaited()


@pytest.mark.asyncio
async def test_process_packet_open_on_open_err(ouija_test):
    ouija_test.on_open = AsyncMock(return_value=False)
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token='secret',
        host='example.com',
        port=443,
    )
    await ouija_test.process_packet(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.on_open.assert_awaited()


@pytest.mark.asyncio
async def test_process_packet_data_ack_ok(ouija_test):
    ouija_test.opened.set()
    ouija_test.dequeue_send = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=True,
        seq=0,
    )
    await ouija_test.process_packet(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.dequeue_send.assert_awaited()


@pytest.mark.asyncio
async def test_process_packet_data_ok(ouija_test):
    ouija_test.opened.set()
    ouija_test.recv = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=0,
        data=b'test data',
        drain=False,
    )
    await ouija_test.process_packet(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.recv.assert_awaited()


@pytest.mark.asyncio
async def test_process_packet_data_err(ouija_test):
    ouija_test.dequeue_send = AsyncMock()
    ouija_test.recv = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=0,
        data=b'test data',
        drain=False,
    )
    await ouija_test.process_packet(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.dequeue_send.assert_not_awaited()
    ouija_test.recv.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_packet_close_ack(ouija_test):
    packet = Packet(
        phase=Phase.CLOSE,
        ack=True,
    )
    await ouija_test.process_packet(data=packet.binary(fernet=ouija_test.tuning.fernet))
    assert ouija_test.read_closed.is_set()


@pytest.mark.asyncio
async def test_process_packet_close(ouija_test):
    ouija_test.send_ack_close = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )
    await ouija_test.process_packet(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.send_ack_close.assert_awaited()


@pytest.mark.asyncio
async def test_process(ouija_test):
    ouija_test.process_packet = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )
    await ouija_test.process(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.process_packet.assert_awaited()
