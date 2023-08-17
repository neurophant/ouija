from unittest.mock import Mock, AsyncMock

import pytest
from pytest_mock import MockerFixture


def test_datagram_proxy_connection_made(datagram_proxy_test):
    mock = Mock()
    datagram_proxy_test.connection_made(mock)

    assert datagram_proxy_test.transport == mock


@pytest.mark.asyncio
async def test_datagram_proxy_datagram_received_async(datagram_proxy_test, datagram_link_test, data_test):
    datagram_proxy_test.links = {('127.0.0.1', 60000): datagram_link_test}
    datagram_link_test.process = AsyncMock()

    await datagram_proxy_test.datagram_received_async(data=data_test, addr=('127.0.0.1', 60000))

    datagram_link_test.process.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_proxy_datagram_received(datagram_proxy_test, data_test):
    datagram_proxy_test.datagram_received_async = AsyncMock()

    datagram_proxy_test.datagram_received(data_test, ('127.0.0.1', 60000))

    datagram_proxy_test.datagram_received_async.assert_called()


@pytest.mark.asyncio
async def test_datagram_proxy_connection_lost(datagram_proxy_test):
    datagram_proxy_test.transport = AsyncMock()

    datagram_proxy_test.connection_lost(Exception())

    datagram_proxy_test.transport.close.assert_called()


@pytest.mark.asyncio
async def test_datagram_proxy_serve(datagram_proxy_test, mocker: MockerFixture):
    mocked_asyncio = mocker.patch('ouija.proxy.asyncio')
    mocked_loop = AsyncMock()
    mocked_asyncio.get_event_loop = lambda: mocked_loop

    await datagram_proxy_test.serve()

    mocked_loop.create_datagram_endpoint.assert_awaited()
