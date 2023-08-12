from unittest.mock import Mock, AsyncMock

import pytest
from pytest_mock import MockerFixture


def test_proxy_connection_made(proxy_test):
    mock = Mock()
    proxy_test.connection_made(mock)

    assert proxy_test.transport == mock


@pytest.mark.asyncio
async def test_proxy_datagram_received_async(proxy_test, link_test, data_test):
    proxy_test.links = {('127.0.0.1', 60000): link_test}
    link_test.process = AsyncMock()

    await proxy_test.datagram_received_async(data=data_test, addr=('127.0.0.1', 60000))

    link_test.process.assert_awaited()


@pytest.mark.asyncio
async def test_proxy_datagram_received(proxy_test, data_test):
    proxy_test.datagram_received_async = AsyncMock()

    proxy_test.datagram_received(data_test, ('127.0.0.1', 60000))

    proxy_test.datagram_received_async.assert_called()


@pytest.mark.asyncio
async def test_proxy_connection_lost(proxy_test):
    proxy_test.transport = AsyncMock()

    proxy_test.connection_lost(Exception())

    proxy_test.transport.close.assert_called()


@pytest.mark.asyncio
async def test_proxy_serve(proxy_test, mocker: MockerFixture):
    mocked_asyncio = mocker.patch('ouija.proxy.asyncio')
    mocked_loop = AsyncMock()
    mocked_asyncio.get_event_loop = lambda: mocked_loop

    await proxy_test.serve()

    mocked_loop.create_datagram_endpoint.assert_awaited()
