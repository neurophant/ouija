import asyncio
from unittest.mock import AsyncMock

import pytest

from ouija import Packet, Phase
from ouija.exception import SendRetryError, TokenError, OnOpenError, OnServeError, BufOverloadError
from ouija.data import Sent, Message


@pytest.mark.asyncio
@pytest.mark.xfail(raises=NotImplementedError)
async def test_datagram_ouija_on_send(datagram_ouija_test, data_test):
    await datagram_ouija_test.on_send(data=data_test)


@pytest.mark.asyncio
async def test_datagram_ouija_send(datagram_ouija_test, data_test):
    datagram_ouija_test.on_send = AsyncMock()

    await datagram_ouija_test.send(data=data_test)

    datagram_ouija_test.on_send.assert_awaited_with(data=data_test)


@pytest.mark.asyncio
async def test_datagram_ouija_send_packet(datagram_ouija_test, data_test):
    datagram_ouija_test.send = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=data_test, drain=True)

    await datagram_ouija_test.send_packet(packet=packet)

    datagram_ouija_test.send.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_send_retry(datagram_ouija_test, data_test):
    datagram_ouija_test.send_packet = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=data_test, drain=True)
    event = asyncio.Event()
    event.set()

    await datagram_ouija_test.send_retry(packet=packet, event=event)

    datagram_ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=SendRetryError)
async def test_datagram_ouija_send_retry_sendretryerror(datagram_ouija_test, data_test):
    datagram_ouija_test.send_packet = AsyncMock()
    packet = Packet(phase=Phase.DATA, ack=False, seq=0, data=data_test, drain=True)
    event = asyncio.Event()

    result = await datagram_ouija_test.send_retry(packet=packet, event=event)

    datagram_ouija_test.send_packet.assert_awaited()
    assert not result


@pytest.mark.asyncio
@pytest.mark.xfail(raises=NotImplementedError)
async def test_datagram_ouija_on_open(datagram_ouija_test, token_test):
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )

    await datagram_ouija_test.on_open(packet=packet)


@pytest.mark.asyncio
async def test_datagram_ouija_process_wrapped_open(datagram_ouija_test, token_test):
    datagram_ouija_test.on_open = AsyncMock(return_value=True)
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.on_open.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=TokenError)
async def test_datagram_ouija_process_wrapped_open_tokenerror(datagram_ouija_test):
    datagram_ouija_test.check_token = AsyncMock(return_value=False)
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token='toktok',
        host='example.com',
        port=443,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnOpenError)
async def test_datagram_ouija_process_wrapped_open_onopenerror(datagram_ouija_test, token_test):
    datagram_ouija_test.on_open = AsyncMock()
    datagram_ouija_test.on_open.side_effect = OnOpenError()
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.on_open.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_wrapped_data_ack(datagram_ouija_test):
    datagram_ouija_test.opened.set()
    datagram_ouija_test.sent_buf = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=True,
        seq=0,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.sent_buf.pop.assert_called()


@pytest.mark.asyncio
async def test_datagram_ouija_process_wrapped_data(datagram_ouija_test, data_test):
    datagram_ouija_test.opened.set()
    datagram_ouija_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=0,
        data=data_test,
        drain=True,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.send_packet.assert_awaited()
    datagram_ouija_test.writer.write.assert_called()
    datagram_ouija_test.writer.drain.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_wrapped_data_not_opened(datagram_ouija_test, data_test):
    datagram_ouija_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=0,
        data=data_test,
        drain=False,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.send_packet.assert_not_awaited()
    datagram_ouija_test.writer.write.assert_not_called()
    datagram_ouija_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_wrapped_data_write_closed(datagram_ouija_test, data_test):
    datagram_ouija_test.opened.set()
    datagram_ouija_test.write_closed.set()
    datagram_ouija_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=0,
        data=data_test,
        drain=True,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.send_packet.assert_awaited()
    datagram_ouija_test.writer.write.assert_not_called()
    datagram_ouija_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_wrapped_seq(datagram_ouija_test, data_test):
    datagram_ouija_test.opened.set()
    datagram_ouija_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=1,
        data=data_test,
        drain=True,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.send_packet.assert_awaited()
    datagram_ouija_test.writer.write.assert_not_called()
    datagram_ouija_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=BufOverloadError)
async def test_datagram_ouija_process_wrapped_bufoverloaderror(datagram_ouija_test, data_test):
    datagram_ouija_test.opened.set()
    datagram_ouija_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
        seq=1,
        data=data_test,
        drain=True,
    )

    for _ in range(datagram_ouija_test.tuning.udp_capacity):
        await datagram_ouija_test.process_wrapped(data=packet.binary(
            cipher=datagram_ouija_test.tuning.cipher,
            entropy=datagram_ouija_test.tuning.entropy,
        ))
        packet.seq += 1


@pytest.mark.asyncio
async def test_datagram_ouija_process_wrapped_close_ack(datagram_ouija_test):
    datagram_ouija_test.opened.set()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=True,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    assert datagram_ouija_test.read_closed.is_set()


@pytest.mark.asyncio
async def test_datagram_ouija_process_wrapped_close(datagram_ouija_test):
    datagram_ouija_test.opened.set()
    datagram_ouija_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    assert datagram_ouija_test.write_closed.is_set()
    datagram_ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_wrapped_close_not_opened(datagram_ouija_test):
    datagram_ouija_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )

    await datagram_ouija_test.process_wrapped(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    assert not datagram_ouija_test.read_closed.is_set()
    assert not datagram_ouija_test.write_closed.is_set()
    datagram_ouija_test.send_packet.assert_not_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process(datagram_ouija_test):
    datagram_ouija_test.process_wrapped = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )

    await datagram_ouija_test.process(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.process_wrapped.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_tokenerror(datagram_ouija_test):
    datagram_ouija_test.process_wrapped = AsyncMock()
    datagram_ouija_test.process_wrapped.side_effect = TokenError()
    datagram_ouija_test.close = AsyncMock()
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
    )

    await datagram_ouija_test.process(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.process_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_onopenerror(datagram_ouija_test):
    datagram_ouija_test.process_wrapped = AsyncMock()
    datagram_ouija_test.process_wrapped.side_effect = OnOpenError()
    datagram_ouija_test.close = AsyncMock()
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
    )

    await datagram_ouija_test.process(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.process_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_bufoverloaderror(datagram_ouija_test):
    datagram_ouija_test.process_wrapped = AsyncMock()
    datagram_ouija_test.process_wrapped.side_effect = BufOverloadError()
    datagram_ouija_test.close = AsyncMock()
    packet = Packet(
        phase=Phase.DATA,
        ack=False,
    )

    await datagram_ouija_test.process(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.process_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_connectionerror(datagram_ouija_test):
    datagram_ouija_test.process_wrapped = AsyncMock()
    datagram_ouija_test.process_wrapped.side_effect = ConnectionError()
    datagram_ouija_test.close = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )

    await datagram_ouija_test.process(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.process_wrapped.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_process_exception(datagram_ouija_test):
    datagram_ouija_test.process_wrapped = AsyncMock()
    datagram_ouija_test.process_wrapped.side_effect = Exception()
    datagram_ouija_test.close = AsyncMock()
    packet = Packet(
        phase=Phase.CLOSE,
        ack=False,
    )

    await datagram_ouija_test.process(data=packet.binary(
        cipher=datagram_ouija_test.tuning.cipher,
        entropy=datagram_ouija_test.tuning.entropy,
    ))

    datagram_ouija_test.process_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_resend_wrapped(datagram_ouija_test, data_test):
    datagram_ouija_test.send = AsyncMock()
    datagram_ouija_test.sent_buf[0] = Sent(data=data_test)

    await datagram_ouija_test.resend_wrapped()

    datagram_ouija_test.send.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_resend(datagram_ouija_test):
    datagram_ouija_test.resend_wrapped = AsyncMock()
    datagram_ouija_test.close = AsyncMock()

    await datagram_ouija_test.resend()

    datagram_ouija_test.resend_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_resend_timeouterror(datagram_ouija_test):
    datagram_ouija_test.resend_wrapped = AsyncMock()
    datagram_ouija_test.resend_wrapped.side_effect = TimeoutError()
    datagram_ouija_test.close = AsyncMock()

    await datagram_ouija_test.resend()

    datagram_ouija_test.resend_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=Exception)
async def test_datagram_ouija_resend_exception(datagram_ouija_test):
    datagram_ouija_test.resend_wrapped = AsyncMock()
    datagram_ouija_test.resend_wrapped.side_effect = Exception()

    await datagram_ouija_test.resend()

    datagram_ouija_test.resend_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=NotImplementedError)
async def test_datagram_ouija_on_serve(datagram_ouija_test):
    await datagram_ouija_test.on_serve()


@pytest.mark.asyncio
async def test_datagram_ouija_serve_wrapped(datagram_ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        datagram_ouija_test.sync.clear()

    async def read(*args, **kwargs):
        await asyncio.sleep(0.5)
        return data_test

    datagram_ouija_test.on_serve = AsyncMock()
    datagram_ouija_test.resend = AsyncMock()
    datagram_ouija_test.reader.read = read
    datagram_ouija_test.send_packet = AsyncMock()
    datagram_ouija_test.sync.set()
    asyncio.create_task(resetter())

    await datagram_ouija_test.serve_wrapped()

    datagram_ouija_test.on_serve.assert_awaited()
    datagram_ouija_test.resend.assert_awaited()
    datagram_ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnServeError)
async def test_datagram_ouija_serve_wrapped_onserveerror(datagram_ouija_test, data_test):
    datagram_ouija_test.on_serve = AsyncMock()
    datagram_ouija_test.on_serve.side_effect = OnServeError()

    await datagram_ouija_test.serve_wrapped()

    datagram_ouija_test.on_serve.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_serve_wrapped_timeouterror(datagram_ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        datagram_ouija_test.sync.clear()

    datagram_ouija_test.on_serve = AsyncMock()
    datagram_ouija_test.resend = AsyncMock()
    datagram_ouija_test.reader.read = AsyncMock(return_value=data_test)
    datagram_ouija_test.reader.read.side_effect = TimeoutError()
    datagram_ouija_test.send_packet = AsyncMock()
    datagram_ouija_test.sync.set()
    asyncio.create_task(resetter())

    await datagram_ouija_test.serve_wrapped()

    datagram_ouija_test.on_serve.assert_awaited()
    datagram_ouija_test.resend.assert_awaited()
    datagram_ouija_test.reader.read.assert_awaited()
    datagram_ouija_test.send_packet.assert_not_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_serve_wrapped_empty(datagram_ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        datagram_ouija_test.sync.clear()

    datagram_ouija_test.on_serve = AsyncMock()
    datagram_ouija_test.resend = AsyncMock()
    datagram_ouija_test.reader.read = AsyncMock(return_value=b'')
    datagram_ouija_test.send_packet = AsyncMock()
    datagram_ouija_test.sync.set()
    asyncio.create_task(resetter())

    await datagram_ouija_test.serve_wrapped()

    datagram_ouija_test.on_serve.assert_awaited()
    datagram_ouija_test.resend.assert_awaited()
    datagram_ouija_test.reader.read.assert_awaited()
    datagram_ouija_test.send_packet.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=BufOverloadError)
async def test_datagram_ouija_serve_wrapped_bufoverloaderror(datagram_ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(2)
        datagram_ouija_test.sync.clear()

    async def read(*args, **kwargs):
        await asyncio.sleep(0.5)
        return data_test

    datagram_ouija_test.on_serve = AsyncMock()
    datagram_ouija_test.resend = AsyncMock()
    datagram_ouija_test.reader.read = read
    datagram_ouija_test.send_packet = AsyncMock()
    datagram_ouija_test.sync.set()
    for i in range(datagram_ouija_test.tuning.udp_capacity):
        datagram_ouija_test.sent_buf[i] = Sent(data=data_test)
    asyncio.create_task(resetter())

    await datagram_ouija_test.serve_wrapped()

    datagram_ouija_test.on_serve.assert_awaited()
    datagram_ouija_test.resend.assert_awaited()
    datagram_ouija_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_serve(datagram_ouija_test):
    datagram_ouija_test.serve_wrapped = AsyncMock()

    await datagram_ouija_test.serve()

    datagram_ouija_test.serve_wrapped.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_serve_onserveerror(datagram_ouija_test):
    datagram_ouija_test.serve_wrapped = AsyncMock()
    datagram_ouija_test.serve_wrapped.side_effect = OnServeError()
    datagram_ouija_test.close = AsyncMock()

    await datagram_ouija_test.serve()

    datagram_ouija_test.serve_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_serve_bufoverloaderror(datagram_ouija_test):
    datagram_ouija_test.serve_wrapped = AsyncMock()
    datagram_ouija_test.serve_wrapped.side_effect = BufOverloadError()
    datagram_ouija_test.close = AsyncMock()

    await datagram_ouija_test.serve()

    datagram_ouija_test.serve_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_serve_timeouterror(datagram_ouija_test):
    datagram_ouija_test.serve_wrapped = AsyncMock()
    datagram_ouija_test.serve_wrapped.side_effect = TimeoutError()
    datagram_ouija_test.close = AsyncMock()

    await datagram_ouija_test.serve()

    datagram_ouija_test.serve_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_serve_connectionerror(datagram_ouija_test):
    datagram_ouija_test.serve_wrapped = AsyncMock()
    datagram_ouija_test.serve_wrapped.side_effect = ConnectionError()
    datagram_ouija_test.close = AsyncMock()

    await datagram_ouija_test.serve()

    datagram_ouija_test.serve_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_serve_exception(datagram_ouija_test):
    datagram_ouija_test.serve_wrapped = AsyncMock()
    datagram_ouija_test.serve_wrapped.side_effect = Exception()
    datagram_ouija_test.close = AsyncMock()

    await datagram_ouija_test.serve()

    datagram_ouija_test.serve_wrapped.assert_awaited()
    datagram_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_close(datagram_ouija_test):
    datagram_ouija_test.opened.set()
    datagram_ouija_test.sync.set()
    datagram_ouija_test.writer = AsyncMock(spec=asyncio.StreamWriter)
    datagram_ouija_test.writer.is_closing = lambda: False
    datagram_ouija_test.on_close = AsyncMock()

    await datagram_ouija_test.close()

    assert not datagram_ouija_test.opened.is_set()
    assert datagram_ouija_test.read_closed.is_set()
    assert datagram_ouija_test.write_closed.is_set()
    datagram_ouija_test.writer.close.assert_called()
    datagram_ouija_test.writer.wait_closed.assert_awaited()
    datagram_ouija_test.on_close.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_ouija_close_writer_exception(datagram_ouija_test):
    datagram_ouija_test.opened.set()
    datagram_ouija_test.sync.set()
    datagram_ouija_test.writer = AsyncMock(spec=asyncio.StreamWriter)
    datagram_ouija_test.writer.is_closing = lambda: False
    datagram_ouija_test.writer.close.side_effect = Exception()
    datagram_ouija_test.on_close = AsyncMock()

    await datagram_ouija_test.close()

    assert not datagram_ouija_test.opened.is_set()
    assert datagram_ouija_test.read_closed.is_set()
    assert datagram_ouija_test.write_closed.is_set()
    datagram_ouija_test.writer.close.assert_called()
    datagram_ouija_test.writer.wait_closed.assert_not_awaited()
    datagram_ouija_test.on_close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_forward_wrapped(stream_ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        stream_ouija_test.sync.clear()

    async def readuntil(*args, **kwargs):
        await asyncio.sleep(0.5)
        return Message.encrypt(
            data=data_test,
            cipher=stream_ouija_test.tuning.cipher,
            entropy=stream_ouija_test.tuning.entropy,
        )

    stream_ouija_test.target_reader.readuntil = readuntil
    stream_ouija_test.sync.set()
    asyncio.create_task(resetter())

    await stream_ouija_test.forward_wrapped(
        reader=stream_ouija_test.target_reader,
        writer=stream_ouija_test.writer,
        crypt=False,
    )

    stream_ouija_test.target_reader.read.assert_not_called()
    stream_ouija_test.writer.write.assert_called()
    stream_ouija_test.writer.drain.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_forward_wrapped_crypt(stream_ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        stream_ouija_test.sync.clear()

    async def read(*args, **kwargs):
        await asyncio.sleep(0.5)
        return data_test

    stream_ouija_test.reader.read = read
    stream_ouija_test.sync.set()
    asyncio.create_task(resetter())

    await stream_ouija_test.forward_wrapped(
        reader=stream_ouija_test.reader,
        writer=stream_ouija_test.target_writer,
        crypt=True,
    )

    stream_ouija_test.reader.readuntil.assert_not_called()
    stream_ouija_test.target_writer.write.assert_called()
    stream_ouija_test.target_writer.drain.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_forward_wrapped_timeouterror(stream_ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(2)
        stream_ouija_test.sync.clear()

    stream_ouija_test.target_reader.readuntil.side_effect = TimeoutError()
    stream_ouija_test.sync.set()
    asyncio.create_task(resetter())

    await stream_ouija_test.forward_wrapped(
        reader=stream_ouija_test.target_reader,
        writer=stream_ouija_test.writer,
        crypt=False,
    )

    stream_ouija_test.target_reader.read.assert_not_called()
    stream_ouija_test.writer.write.assert_not_called()
    stream_ouija_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_forward_wrapped_incompletereaderror(stream_ouija_test, data_test):
    stream_ouija_test.target_reader.readuntil.side_effect = asyncio.IncompleteReadError(partial=b'', expected=10)
    stream_ouija_test.sync.set()

    await stream_ouija_test.forward_wrapped(
        reader=stream_ouija_test.target_reader,
        writer=stream_ouija_test.writer,
        crypt=False,
    )

    stream_ouija_test.target_reader.read.assert_not_called()
    stream_ouija_test.writer.write.assert_not_called()
    stream_ouija_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_forward_wrapped_empty(stream_ouija_test, data_test):
    async def resetter():
        await asyncio.sleep(3)
        stream_ouija_test.sync.clear()

    async def readuntil(*args, **kwargs):
        await asyncio.sleep(0.5)
        return b''

    stream_ouija_test.target_reader.readuntil = readuntil
    stream_ouija_test.sync.set()
    asyncio.create_task(resetter())

    await stream_ouija_test.forward_wrapped(
        reader=stream_ouija_test.target_reader,
        writer=stream_ouija_test.writer,
        crypt=False,
    )

    stream_ouija_test.target_reader.read.assert_not_called()
    stream_ouija_test.writer.write.assert_not_called()
    stream_ouija_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_forward(stream_ouija_test):
    stream_ouija_test.forward_wrapped = AsyncMock()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.forward(reader=stream_ouija_test.reader, writer=stream_ouija_test.target_writer, crypt=True)

    stream_ouija_test.forward_wrapped.assert_awaited()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_forward_timeouterror(stream_ouija_test):
    stream_ouija_test.forward_wrapped = AsyncMock()
    stream_ouija_test.forward_wrapped.side_effect = TimeoutError()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.forward(reader=stream_ouija_test.reader, writer=stream_ouija_test.target_writer, crypt=True)

    stream_ouija_test.forward_wrapped.assert_called()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_forward_connectionerror(stream_ouija_test):
    stream_ouija_test.forward_wrapped = AsyncMock()
    stream_ouija_test.forward_wrapped.side_effect = ConnectionError()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.forward(reader=stream_ouija_test.reader, writer=stream_ouija_test.target_writer, crypt=True)

    stream_ouija_test.forward_wrapped.assert_called()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_forward_exception(stream_ouija_test):
    stream_ouija_test.forward_wrapped = AsyncMock()
    stream_ouija_test.forward_wrapped.side_effect = Exception()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.forward(reader=stream_ouija_test.reader, writer=stream_ouija_test.target_writer, crypt=True)

    stream_ouija_test.forward_wrapped.assert_called()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=NotImplementedError)
async def test_stream_ouija_on_serve(stream_ouija_test):
    await stream_ouija_test.on_serve()


@pytest.mark.asyncio
async def test_stream_ouija_serve_wrapped(stream_ouija_test, data_test):
    stream_ouija_test.on_serve = AsyncMock()
    stream_ouija_test.forward = AsyncMock()

    await stream_ouija_test.serve_wrapped()

    stream_ouija_test.on_serve.assert_awaited()
    assert stream_ouija_test.opened.is_set()
    assert stream_ouija_test.sync.is_set()


@pytest.mark.asyncio
async def test_stream_ouija_serve(stream_ouija_test):
    stream_ouija_test.serve_wrapped = AsyncMock()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.serve()

    stream_ouija_test.serve_wrapped.assert_awaited()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_serve_tokenerror(stream_ouija_test):
    stream_ouija_test.serve_wrapped = AsyncMock()
    stream_ouija_test.serve_wrapped.side_effect = TokenError()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.serve()

    stream_ouija_test.serve_wrapped.assert_awaited()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_serve_onserveerror(stream_ouija_test):
    stream_ouija_test.serve_wrapped = AsyncMock()
    stream_ouija_test.serve_wrapped.side_effect = OnServeError()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.serve()

    stream_ouija_test.serve_wrapped.assert_awaited()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_serve_timeouterror(stream_ouija_test):
    stream_ouija_test.serve_wrapped = AsyncMock()
    stream_ouija_test.serve_wrapped.side_effect = TimeoutError()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.serve()

    stream_ouija_test.serve_wrapped.assert_awaited()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_serve_connectionerror(stream_ouija_test):
    stream_ouija_test.serve_wrapped = AsyncMock()
    stream_ouija_test.serve_wrapped.side_effect = ConnectionError()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.serve()

    stream_ouija_test.serve_wrapped.assert_awaited()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_serve_exception(stream_ouija_test):
    stream_ouija_test.serve_wrapped = AsyncMock()
    stream_ouija_test.serve_wrapped.side_effect = Exception()
    stream_ouija_test.close = AsyncMock()

    await stream_ouija_test.serve()

    stream_ouija_test.serve_wrapped.assert_awaited()
    stream_ouija_test.close.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=NotImplementedError)
async def test_stream_ouija_on_close(stream_ouija_test):
    await stream_ouija_test.on_close()


@pytest.mark.asyncio
async def test_stream_ouija_close(stream_ouija_test):
    stream_ouija_test.opened.set()
    stream_ouija_test.sync.set()
    stream_ouija_test.writer = AsyncMock(spec=asyncio.StreamWriter)
    stream_ouija_test.writer.is_closing = lambda: False
    stream_ouija_test.target_writer = AsyncMock(spec=asyncio.StreamWriter)
    stream_ouija_test.target_writer.is_closing = lambda: False
    stream_ouija_test.on_close = AsyncMock()

    await stream_ouija_test.close()

    assert not stream_ouija_test.opened.is_set()
    assert not stream_ouija_test.sync.is_set()
    stream_ouija_test.writer.close.assert_called()
    stream_ouija_test.writer.wait_closed.assert_awaited()
    stream_ouija_test.target_writer.close.assert_called()
    stream_ouija_test.target_writer.wait_closed.assert_awaited()
    stream_ouija_test.on_close.assert_awaited()


@pytest.mark.asyncio
async def test_stream_ouija_close_writer_exception(stream_ouija_test):
    stream_ouija_test.opened.set()
    stream_ouija_test.sync.set()
    stream_ouija_test.writer = AsyncMock(spec=asyncio.StreamWriter)
    stream_ouija_test.writer.is_closing = lambda: False
    stream_ouija_test.writer.close.side_effect = Exception()
    stream_ouija_test.target_writer = AsyncMock(spec=asyncio.StreamWriter)
    stream_ouija_test.target_writer.is_closing = lambda: False
    stream_ouija_test.on_close = AsyncMock()

    await stream_ouija_test.close()

    assert not stream_ouija_test.opened.is_set()
    assert not stream_ouija_test.sync.is_set()
    stream_ouija_test.writer.close.assert_called()
    stream_ouija_test.writer.wait_closed.assert_not_awaited()
    stream_ouija_test.target_writer.close.assert_called()
    stream_ouija_test.target_writer.wait_closed.assert_awaited()
    stream_ouija_test.on_close.assert_awaited()
