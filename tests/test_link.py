from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from ouija import Packet, Phase
from ouija.exception import OnOpenError


@pytest.mark.asyncio
async def test_link_on_send(link_test, data_test):
    await link_test.on_send(data=data_test)

    link_test.proxy.transport.sendto.assert_called()


@pytest.mark.asyncio
async def test_link_on_open(link_test, token_test, mocker: MockerFixture):
    async def open_connection(*args, **kwargs):
        return AsyncMock(), AsyncMock()

    mocked_asyncio = mocker.patch('ouija.link.asyncio')
    mocked_asyncio.open_connection = open_connection
    link_test.serve = AsyncMock()
    link_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )

    await link_test.on_open(packet=packet)

    assert link_test.opened.is_set()
    link_test.serve.assert_called()
    link_test.send_packet.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnOpenError)
async def test_link_on_open_empty_remote(link_test, token_test):
    link_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
    )

    await link_test.on_open(packet=packet)

    link_test.send_packet.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=OnOpenError)
async def test_link_on_open_opened(link_test, token_test):
    link_test.opened.set()
    link_test.send_packet = AsyncMock()
    packet = Packet(
        phase=Phase.OPEN,
        ack=False,
        token=token_test,
        host='example.com',
        port=443,
    )

    await link_test.on_open(packet=packet)

    link_test.send_packet.assert_awaited()


@pytest.mark.asyncio
async def test_link_on_close(link_test, token_test):
    link_test.proxy.links = {link_test.addr: link_test}

    await link_test.on_close()

    assert not link_test.proxy.links
