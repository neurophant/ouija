import asyncio
from unittest.mock import Mock, AsyncMock

import pytest

from ouija import Packet, Phase
from ouija.exception import OnOpenError, SendRetryError, OnServeError


def test_relay_connection_made(relay_test):
    mock = Mock()
    relay_test.connection_made(mock)

    assert relay_test.transport == mock


@pytest.mark.asyncio
async def test_relay_datagram_received_async(relay_test, data_test):
    relay_test.process = AsyncMock()

    await relay_test.datagram_received_async(data=data_test, addr='127.0.0.1')

    relay_test.process.assert_awaited()


@pytest.mark.asyncio
async def test_relay_datagram_received(relay_test, data_test):
    relay_test.datagram_received_async = AsyncMock()

    relay_test.datagram_received(data_test, '127.0.0.1')

    relay_test.datagram_received_async.assert_called()


@pytest.mark.asyncio
async def test_relay_connection_lost(relay_test):
    relay_test.close = AsyncMock()

    relay_test.connection_lost(Exception())

    relay_test.close.assert_called()


@pytest.mark.asyncio
async def test_relay_on_send(relay_test, data_test):
    relay_test.transport = Mock()

    await relay_test.on_send(data=data_test)

    relay_test.transport.sendto.assert_called()


@pytest.mark.asyncio
async def test_relay_on_open(relay_test, token_test):
    packet = Packet(
        phase=Phase.OPEN,
        ack=True,
        token=token_test,
    )

    await relay_test.on_open(packet=packet)

    relay_test.writer.write.assert_called()
    relay_test.writer.drain.assert_awaited()
    assert relay_test.opened.is_set()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnOpenError)
async def test_relay_on_open_not_ack(relay_test, token_test):
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
    )

    await relay_test.on_open(packet=packet)

    assert not relay_test.opened.is_set()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnOpenError)
async def test_relay_on_open_opened(relay_test, token_test):
    relay_test.opened.set()
    packet = Packet(
        phase=Phase.OPEN,
        ack=True,
        token=token_test,
    )

    await relay_test.on_open(packet=packet)


@pytest.mark.asyncio
async def test_relay_on_serve(relay_test, token_test):
    relay_test.send_retry = AsyncMock()

    await relay_test.on_serve()

    relay_test.send_retry.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnServeError)
async def test_relay_on_serve_sendretryerror(relay_test, token_test):
    relay_test.send_retry = AsyncMock()
    relay_test.send_retry.side_effect = SendRetryError()

    await relay_test.on_serve()

    relay_test.send_retry.assert_awaited()


@pytest.mark.asyncio
async def test_relay_on_close(relay_test, token_test):
    relay_test.transport = AsyncMock(spec=asyncio.DatagramTransport)
    relay_test.transport.is_closing = lambda: False

    await relay_test.on_close()

    relay_test.transport.close.assert_called()


@pytest.mark.asyncio
async def test_relay_on_close_closing(relay_test, token_test):
    relay_test.transport = AsyncMock(spec=asyncio.DatagramTransport)
    relay_test.transport.is_closing = lambda: True

    await relay_test.on_close()

    relay_test.transport.close.assert_not_called()
