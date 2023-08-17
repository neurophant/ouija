from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from ouija import Packet, Phase
from ouija.exception import OnOpenError


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
