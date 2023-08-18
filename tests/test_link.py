from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from ouija import Packet, Phase, Message
from ouija.exception import OnOpenError, OnServeError, TokenError


@pytest.mark.asyncio
async def test_datagram_link_on_send(datagram_link_test, data_test):
    await datagram_link_test.on_send(data=data_test)

    datagram_link_test.proxy.transport.sendto.assert_called()


@pytest.mark.asyncio
async def test_datagram_link_on_open(datagram_link_test, token_test, mocker: MockerFixture):
    async def open_connection(*args, **kwargs):
        return AsyncMock(), AsyncMock()

    mocked_asyncio = mocker.patch('ouija.link.asyncio')
    mocked_asyncio.open_connection = open_connection
    datagram_link_test.serve = AsyncMock()
    datagram_link_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )

    await datagram_link_test.on_open(packet=packet)

    assert datagram_link_test.opened.is_set()
    datagram_link_test.serve.assert_called()
    datagram_link_test.send_packet.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnOpenError)
async def test_datagram_link_on_open_empty_remote(datagram_link_test, token_test):
    datagram_link_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
    )

    await datagram_link_test.on_open(packet=packet)

    datagram_link_test.send_packet.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnOpenError)
async def test_datagram_link_on_open_opened(datagram_link_test, token_test):
    datagram_link_test.opened.set()
    datagram_link_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )

    await datagram_link_test.on_open(packet=packet)

    datagram_link_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_link_on_close(datagram_link_test, token_test):
    datagram_link_test.proxy.links = {datagram_link_test.addr: datagram_link_test}

    await datagram_link_test.on_close()

    assert not datagram_link_test.proxy.links


@pytest.mark.asyncio
async def test_stream_link_on_serve(
        stream_link_test,
        token_test,
        fernet_test,
        data_test,
        mocker: MockerFixture,
):
    mocked_wait_for = mocker.patch('ouija.link.asyncio.wait_for')
    mocked_wait_for.return_value = Message(token=token_test, host='example.com', port=443).binary(fernet=fernet_test)
    mocked_open_connection = mocker.patch('ouija.link.asyncio.open_connection')
    mocked_open_connection.return_value = (AsyncMock(), AsyncMock())

    await stream_link_test.on_serve()

    stream_link_test.reader.readuntil.assert_called()
    mocked_open_connection.assert_awaited()
    stream_link_test.writer.write.assert_called()
    stream_link_test.writer.drain.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnServeError)
async def test_stream_link_on_serve_timeouterror(stream_link_test, mocker: MockerFixture):
    mocked_wait_for = mocker.patch('ouija.link.asyncio.wait_for')
    mocked_wait_for.side_effect = TimeoutError
    mocked_open_connection = mocker.patch('ouija.link.asyncio.open_connection')
    mocked_open_connection.return_value = (AsyncMock(), AsyncMock())

    await stream_link_test.on_serve()

    stream_link_test.reader.readuntil.assert_called()
    mocked_open_connection.assert_not_awaited()
    stream_link_test.writer.write.assert_not_called()
    stream_link_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=TokenError)
async def test_stream_link_on_serve_tokenerror(stream_link_test, fernet_test, mocker: MockerFixture):
    mocked_wait_for = mocker.patch('ouija.link.asyncio.wait_for')
    mocked_wait_for.return_value = Message(token='invalid', host='example.com', port=443).binary(fernet=fernet_test)
    mocked_open_connection = mocker.patch('ouija.link.asyncio.open_connection')
    mocked_open_connection.return_value = (AsyncMock(), AsyncMock())

    await stream_link_test.on_serve()

    stream_link_test.reader.readuntil.assert_called()
    mocked_open_connection.assert_not_awaited()
    stream_link_test.writer.write.assert_not_called()
    stream_link_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
async def test_stream_link_on_close(stream_link_test):
    stream_link_test.proxy.links[stream_link_test.uid] = stream_link_test

    await stream_link_test.on_close()

    assert stream_link_test.uid not in stream_link_test.proxy.links
