import asyncio
from unittest.mock import Mock, AsyncMock

import pytest
from pytest_mock import MockerFixture

from ouija import Packet, Phase, Message
from ouija.exception import OnOpenError, SendRetryError, OnServeError, TokenError


def test_datagram_connector_connection_made(datagram_connector_test):
    mock = Mock()
    datagram_connector_test.connection_made(mock)

    assert datagram_connector_test.transport == mock


@pytest.mark.asyncio
async def test_datagram_connector_datagram_received_async(datagram_connector_test, data_test):
    datagram_connector_test.process = AsyncMock()

    await datagram_connector_test.datagram_received_async(data=data_test, addr='127.0.0.1')

    datagram_connector_test.process.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_connector_datagram_received(datagram_connector_test, data_test):
    datagram_connector_test.datagram_received_async = AsyncMock()

    datagram_connector_test.datagram_received(data_test, '127.0.0.1')

    datagram_connector_test.datagram_received_async.assert_called()


@pytest.mark.asyncio
async def test_datagram_connector_connection_lost(datagram_connector_test):
    datagram_connector_test.close = AsyncMock()

    datagram_connector_test.connection_lost(Exception())

    datagram_connector_test.close.assert_called()


@pytest.mark.asyncio
async def test_datagram_connector_on_send(datagram_connector_test, data_test):
    datagram_connector_test.transport = Mock()

    await datagram_connector_test.on_send(data=data_test)

    datagram_connector_test.transport.sendto.assert_called()


@pytest.mark.asyncio
async def test_datagram_connector_on_open(datagram_connector_test, token_test):
    packet = Packet(
        phase=Phase.OPEN,
        ack=True,
        token=token_test,
    )

    await datagram_connector_test.on_open(packet=packet)

    datagram_connector_test.writer.write.assert_called()
    datagram_connector_test.writer.drain.assert_awaited()
    assert datagram_connector_test.opened.is_set()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnOpenError)
async def test_datagram_connector_on_open_not_ack(datagram_connector_test, token_test):
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
    )

    await datagram_connector_test.on_open(packet=packet)

    assert not datagram_connector_test.opened.is_set()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnOpenError)
async def test_datagram_connector_on_open_opened(datagram_connector_test, token_test):
    datagram_connector_test.opened.set()
    packet = Packet(
        phase=Phase.OPEN,
        ack=True,
        token=token_test,
    )

    await datagram_connector_test.on_open(packet=packet)


@pytest.mark.asyncio
async def test_datagram_connector_on_serve(datagram_connector_test, token_test):
    datagram_connector_test.send_retry = AsyncMock()

    await datagram_connector_test.on_serve()

    datagram_connector_test.send_retry.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnServeError)
async def test_datagram_connector_on_serve_sendretryerror(datagram_connector_test, token_test):
    datagram_connector_test.send_retry = AsyncMock()
    datagram_connector_test.send_retry.side_effect = SendRetryError()

    await datagram_connector_test.on_serve()

    datagram_connector_test.send_retry.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_connector_on_close(datagram_connector_test, token_test):
    datagram_connector_test.transport = AsyncMock(spec=asyncio.DatagramTransport)
    datagram_connector_test.transport.is_closing = lambda: False

    await datagram_connector_test.on_close()

    datagram_connector_test.transport.close.assert_called()


@pytest.mark.asyncio
async def test_datagram_connector_on_close_closing(datagram_connector_test, token_test):
    datagram_connector_test.transport = AsyncMock(spec=asyncio.DatagramTransport)
    datagram_connector_test.transport.is_closing = lambda: True

    await datagram_connector_test.on_close()

    datagram_connector_test.transport.close.assert_not_called()


@pytest.mark.asyncio
async def test_stream_connector_on_serve(
        stream_connector_test,
        token_test,
        fernet_test,
        data_test,
        mocker: MockerFixture,
):
    mocked_open_connection = mocker.patch('ouija.connector.asyncio.open_connection')
    mocked_open_connection.return_value = (AsyncMock(), AsyncMock())
    mocked_wait_for = mocker.patch('ouija.connector.asyncio.wait_for')
    mocked_wait_for.return_value = Message(token=token_test).binary(fernet=fernet_test)

    await stream_connector_test.on_serve()

    stream_connector_test.target_writer.write.assert_called()
    stream_connector_test.target_writer.drain.assert_awaited()
    stream_connector_test.writer.write.assert_called()
    stream_connector_test.writer.drain.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnServeError)
async def test_stream_connector_on_serve_timeouterror(
        stream_connector_test,
        token_test,
        fernet_test,
        data_test,
        mocker: MockerFixture,
):
    mocked_open_connection = mocker.patch('ouija.connector.asyncio.open_connection')
    mocked_open_connection.return_value = (AsyncMock(), AsyncMock())
    mocked_wait_for = mocker.patch('ouija.connector.asyncio.wait_for')
    mocked_wait_for.side_effect = TimeoutError

    await stream_connector_test.on_serve()

    stream_connector_test.target_writer.write.assert_called()
    stream_connector_test.target_writer.drain.assert_awaited()
    stream_connector_test.target_reader.readuntil.assert_called()
    stream_connector_test.writer.write.assert_not_called()
    stream_connector_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=TokenError)
async def test_stream_connector_on_serve_tokenerror(
        stream_connector_test,
        fernet_test,
        data_test,
        mocker: MockerFixture,
):
    mocked_open_connection = mocker.patch('ouija.connector.asyncio.open_connection')
    mocked_open_connection.return_value = (AsyncMock(), AsyncMock())
    mocked_wait_for = mocker.patch('ouija.connector.asyncio.wait_for')
    mocked_wait_for.return_value = Message(token='invalid').binary(fernet=fernet_test)

    await stream_connector_test.on_serve()

    stream_connector_test.target_writer.write.assert_called()
    stream_connector_test.target_writer.drain.assert_awaited()
    stream_connector_test.target_reader.readuntil.assert_called()
    stream_connector_test.writer.write.assert_not_called()
    stream_connector_test.writer.drain.assert_not_awaited()


@pytest.mark.asyncio
async def test_stream_connector_on_close(stream_connector_test):
    stream_connector_test.relay.connectors[stream_connector_test.uid] = stream_connector_test

    await stream_connector_test.on_close()

    assert stream_connector_test.uid not in stream_connector_test.relay.connectors
