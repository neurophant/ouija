import asyncio
from unittest.mock import AsyncMock

import pytest

from ouija import Packet, Phase


@pytest.mark.asyncio
@pytest.mark.xfail(raises=NotImplementedError)
async def test_on_send(ouija_test, data_test):
    await ouija_test.on_send(data=data_test)


@pytest.mark.asyncio
async def test_send(ouija_test, data_test):
    ouija_test.on_send = AsyncMock()
    await ouija_test.send(data=data_test)
    ouija_test.on_send.assert_awaited_with(data=data_test)


@pytest.mark.asyncio
async def test_send_packet(ouija_test, data_test):
    ouija_test.send = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=data_test, drain=True)
    await ouija_test.send_packet(packet=packet)
    ouija_test.send.assert_awaited()


@pytest.mark.asyncio
async def test_send_retry(ouija_test, data_test):
    ouija_test.send_packet = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=data_test, drain=True)
    event = asyncio.Event()
    event.set()
    result = await ouija_test.send_retry(packet=packet, event=event)
    ouija_test.send_packet.assert_awaited()
    assert result


@pytest.mark.asyncio
async def test_send_retry_event_not_set(ouija_test, data_test):
    ouija_test.send_packet = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=data_test, drain=True)
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
async def test_write(ouija_test, data_test):
    ouija_test.writer = AsyncMock()
    await ouija_test.write(data=data_test, drain=False)
    ouija_test.writer.write.assert_called()


@pytest.mark.asyncio
async def test_write_drain(ouija_test, data_test):
    ouija_test.writer = AsyncMock()
    await ouija_test.write(data=data_test, drain=True)
    ouija_test.writer.write.assert_called()
    ouija_test.writer.drain.assert_awaited()


@pytest.mark.asyncio
async def test_recv(ouija_test, data_test):
    ouija_test.write = AsyncMock()
    ouija_test.send_ack_data = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=1,
        data=data_test,
        drain=False,
    )
    await ouija_test.recv(packet=packet)
    packet.seq = 2
    await ouija_test.recv(packet=packet)
    packet.seq = 0
    await ouija_test.recv(packet=packet)
    ouija_test.write.assert_awaited()
    ouija_test.send_ack_data.assert_awaited()


@pytest.mark.asyncio
async def test_recv_overload(ouija_test, data_test):
    ouija_test.write = AsyncMock()
    ouija_test.send_ack_data = AsyncMock()
    ouija_test.close = AsyncMock()
    ouija_test.tuning.udp_capacity = 1
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=1,
        data=data_test,
        drain=False,
    )
    await ouija_test.recv(packet=packet)
    packet.seq = 2
    await ouija_test.recv(packet=packet)
    ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_enqueue_send(ouija_test, data_test):
    ouija_test.send_packet = AsyncMock()
    await ouija_test.enqueue_send(data=data_test, drain=True)
    ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_enqueue_send_overload(ouija_test, data_test):
    ouija_test.send_packet = AsyncMock()
    ouija_test.close = AsyncMock()
    ouija_test.tuning.udp_capacity = 1
    await ouija_test.enqueue_send(data=data_test, drain=False)
    await ouija_test.enqueue_send(data=data_test, drain=True)
    ouija_test.send_packet.assert_awaited()
    ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_dequeue_send(ouija_test):
    ouija_test.sent_buf = AsyncMock()
    await ouija_test.dequeue_send(seq=1)
    ouija_test.sent_buf.pop.assert_called()


@pytest.mark.asyncio
async def test_send_open(ouija_test):
    ouija_test.send_retry = AsyncMock(return_value=True)
    assert await ouija_test.send_open()
    ouija_test.send_retry.assert_awaited()


@pytest.mark.asyncio
async def test_send_open_send_retry_false(ouija_test):
    ouija_test.send_retry = AsyncMock(return_value=False)
    assert not await ouija_test.send_open()
    ouija_test.send_retry.assert_awaited()


@pytest.mark.asyncio
async def test_send_ack_open(ouija_test):
    ouija_test.send_packet = AsyncMock()
    await ouija_test.send_ack_open()
    ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_check_token(ouija_test, token_test):
    assert await ouija_test.check_token(token=token_test)


@pytest.mark.asyncio
async def test_check_token_false(ouija_test, token_test):
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
@pytest.mark.xfail(raises=NotImplementedError)
async def test_on_open(ouija_test, token_test):
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )
    await ouija_test.on_open(packet=packet)


@pytest.mark.asyncio
async def test_send_ack_close(ouija_test):
    ouija_test.send_packet = AsyncMock()
    await ouija_test.send_ack_close()
    ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_process_wrapped_open(ouija_test, token_test):
    ouija_test.check_token = AsyncMock(return_value=True)
    ouija_test.on_open = AsyncMock(return_value=True)
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )
    await ouija_test.process_wrapped(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.check_token.assert_awaited()
    ouija_test.on_open.assert_awaited()


@pytest.mark.asyncio
async def test_process_wrapped_open_check_token_false(ouija_test, token_test):
    ouija_test.check_token = AsyncMock(return_value=False)
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )
    await ouija_test.process_wrapped(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.check_token.assert_awaited()


@pytest.mark.asyncio
async def test_process_wrapped_open_on_open_false(ouija_test, token_test):
    ouija_test.on_open = AsyncMock(return_value=False)
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )
    await ouija_test.process_wrapped(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.on_open.assert_awaited()


@pytest.mark.asyncio
async def test_process_wrapped_data_ack(ouija_test):
    ouija_test.opened.set()
    ouija_test.dequeue_send = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=True,
        seq=0,
    )
    await ouija_test.process_wrapped(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.dequeue_send.assert_awaited()


@pytest.mark.asyncio
async def test_process_wrapped_data(ouija_test, data_test):
    ouija_test.opened.set()
    ouija_test.recv = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=0,
        data=data_test,
        drain=False,
    )
    await ouija_test.process_wrapped(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.recv.assert_awaited()


@pytest.mark.asyncio
async def test_process_wrapped_data_not_opened(ouija_test, data_test):
    ouija_test.dequeue_send = AsyncMock()
    ouija_test.recv = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=0,
        data=data_test,
        drain=False,
    )
    await ouija_test.process_wrapped(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.dequeue_send.assert_not_awaited()
    ouija_test.recv.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_wrapped_close_ack(ouija_test):
    packet = Packet(
        phase=Phase.CLOSE,
        ack=True,
    )
    await ouija_test.process_wrapped(data=packet.binary(fernet=ouija_test.tuning.fernet))
    assert ouija_test.read_closed.is_set()


@pytest.mark.asyncio
async def test_process_wrapped_close(ouija_test):
    ouija_test.send_ack_close = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )
    await ouija_test.process_wrapped(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.send_ack_close.assert_awaited()


@pytest.mark.asyncio
async def test_process(ouija_test):
    ouija_test.process_wrapped = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )
    await ouija_test.process(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.process_wrapped.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=ConnectionError)
async def test_process_connectionerror(ouija_test):
    ouija_test.process_wrapped = AsyncMock()
    ouija_test.process_wrapped.side_effect = ConnectionError()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )
    await ouija_test.process(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.process_wrapped.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=Exception)
async def test_process_exception(ouija_test):
    ouija_test.process_wrapped = AsyncMock()
    ouija_test.process_wrapped.side_effect = Exception()
    ouija_test.close = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )
    await ouija_test.process(data=packet.binary(fernet=ouija_test.tuning.fernet))
    ouija_test.process_wrapped.assert_awaited()
    ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_resend_wrapped(ouija_test, data_test):
    ouija_test.close = AsyncMock()
    ouija_test.send = AsyncMock()
    ouija_test.send_close = AsyncMock()
    await ouija_test.enqueue_send(data=data_test, drain=True)
    await ouija_test.resend_wrapped()
    ouija_test.close.assert_awaited()
    ouija_test.send.assert_awaited()
    ouija_test.send_close.assert_not_awaited()


@pytest.mark.asyncio
async def test_resend_wrapped_empty(ouija_test):
    ouija_test.send_close = AsyncMock()
    await ouija_test.resend_wrapped()
    ouija_test.send_close.assert_awaited()


@pytest.mark.asyncio
async def test_resend(ouija_test):
    ouija_test.resend_wrapped = AsyncMock()
    ouija_test.close = AsyncMock()
    await ouija_test.resend()
    ouija_test.resend_wrapped.assert_awaited()
    ouija_test.close.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=TimeoutError)
async def test_resend_timeouterror(ouija_test):
    ouija_test.resend_wrapped = AsyncMock()
    ouija_test.resend_wrapped.side_effect = TimeoutError()
    ouija_test.close = AsyncMock()
    await ouija_test.resend()
    ouija_test.resend_wrapped.assert_awaited()
    ouija_test.close.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=Exception)
async def test_resend_exception(ouija_test):
    ouija_test.resend_wrapped = AsyncMock()
    ouija_test.resend_wrapped.side_effect = Exception()
    await ouija_test.resend()
    ouija_test.resend_wrapped.assert_awaited()
    ouija_test.close.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=NotImplementedError)
async def test_on_serve(ouija_test):
    await ouija_test.on_serve()


@pytest.mark.asyncio
async def test_serve_wrapped(ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        ouija_test.opened.clear()
    ouija_test.on_serve = AsyncMock(return_value=True)
    ouija_test.resend = AsyncMock()
    ouija_test.read = AsyncMock(return_value=data_test)
    ouija_test.enqueue_send = AsyncMock()
    ouija_test.opened.set()
    asyncio.create_task(resetter())
    await ouija_test.serve_wrapped()
    ouija_test.on_serve.assert_awaited()
    ouija_test.resend.assert_awaited()
    ouija_test.read.assert_awaited()
    ouija_test.enqueue_send.assert_awaited()


@pytest.mark.asyncio
async def test_serve_wrapped_on_serve_false(ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        ouija_test.opened.clear()
    ouija_test.on_serve = AsyncMock(return_value=False)
    ouija_test.resend = AsyncMock()
    ouija_test.read = AsyncMock(return_value=data_test)
    ouija_test.enqueue_send = AsyncMock()
    ouija_test.opened.set()
    asyncio.create_task(resetter())
    await ouija_test.serve_wrapped()
    ouija_test.on_serve.assert_awaited()
    ouija_test.resend.assert_not_awaited()
    ouija_test.read.assert_not_awaited()
    ouija_test.enqueue_send.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=TimeoutError)
async def test_serve_wrapped_timeouterror(ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        ouija_test.opened.clear()
    ouija_test.on_serve = AsyncMock(return_value=True)
    ouija_test.resend = AsyncMock()
    ouija_test.read = AsyncMock(return_value=data_test)
    ouija_test.read.side_effect = TimeoutError()
    ouija_test.enqueue_send = AsyncMock()
    ouija_test.opened.set()
    asyncio.create_task(resetter())
    await ouija_test.serve_wrapped()
    ouija_test.on_serve.assert_awaited()
    ouija_test.resend.assert_awaited()
    ouija_test.read.assert_awaited()
    ouija_test.enqueue_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_serve_wrapped_empty(ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        ouija_test.opened.clear()
    ouija_test.on_serve = AsyncMock(return_value=True)
    ouija_test.resend = AsyncMock()
    ouija_test.read = AsyncMock(return_value=b'')
    ouija_test.enqueue_send = AsyncMock()
    ouija_test.opened.set()
    asyncio.create_task(resetter())
    await ouija_test.serve_wrapped()
    ouija_test.on_serve.assert_awaited()
    ouija_test.resend.assert_awaited()
    ouija_test.read.assert_awaited()
    ouija_test.enqueue_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_serve(ouija_test):
    ouija_test.serve_wrapped = AsyncMock()
    await ouija_test.serve()
    ouija_test.serve_wrapped.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=TimeoutError)
async def test_serve_timeouterror(ouija_test):
    ouija_test.serve_wrapped = AsyncMock()
    ouija_test.serve_wrapped.side_effect = TimeoutError()
    await ouija_test.serve()
    ouija_test.serve_wrapped.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=ConnectionError)
async def test_serve_connectionerror(ouija_test):
    ouija_test.serve_wrapped = AsyncMock()
    ouija_test.serve_wrapped.side_effect = ConnectionError()
    await ouija_test.serve()
    ouija_test.serve_wrapped.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=Exception)
async def test_serve_exception(ouija_test):
    ouija_test.serve_wrapped = AsyncMock()
    ouija_test.serve_wrapped.side_effect = Exception()
    await ouija_test.serve()
    ouija_test.serve_wrapped.assert_awaited()


@pytest.mark.asyncio
async def test_close(ouija_test):
    ouija_test.opened.set()
    ouija_test.writer = AsyncMock(spec=asyncio.StreamWriter)
    ouija_test.writer.is_closing = lambda: False
    ouija_test.on_close = AsyncMock()
    await ouija_test.close()
    assert not ouija_test.opened.is_set()
    assert ouija_test.read_closed.is_set()
    assert ouija_test.write_closed.is_set()
    ouija_test.writer.close.assert_called()
    ouija_test.writer.wait_closed.assert_awaited()
    ouija_test.on_close.assert_awaited()
