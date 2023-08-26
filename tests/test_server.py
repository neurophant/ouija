import json
import sys
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from ouija.server import main_async


@pytest.mark.asyncio
async def test_stream_relay(tmp_path, config_stream_relay_dict_test, mocker: MockerFixture, stream_relay_test):
    mocked_stream_relay = mocker.patch('ouija.server.StreamRelay')
    mocked_stream_relay.return_value = stream_relay_test
    stream_relay_test.debug = AsyncMock()
    stream_relay_test.serve = AsyncMock()
    path = tmp_path / 'config.json'
    path.write_text(data=json.dumps(config_stream_relay_dict_test))
    sys.argv = [None, str(path)]

    await main_async()

    stream_relay_test.debug.assert_called()
    stream_relay_test.serve.assert_awaited()


@pytest.mark.asyncio
async def test_stream_proxy(tmp_path, config_stream_proxy_dict_test, mocker: MockerFixture, stream_proxy_test):
    mocked_stream_proxy = mocker.patch('ouija.server.StreamProxy')
    mocked_stream_proxy.return_value = stream_proxy_test
    stream_proxy_test.debug = AsyncMock()
    stream_proxy_test.serve = AsyncMock()
    path = tmp_path / 'config.json'
    path.write_text(data=json.dumps(config_stream_proxy_dict_test))
    sys.argv = [None, str(path)]

    await main_async()

    stream_proxy_test.debug.assert_called()
    stream_proxy_test.serve.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_relay(tmp_path, config_datagram_relay_dict_test, mocker: MockerFixture, datagram_relay_test):
    mocked_datagram_relay = mocker.patch('ouija.server.DatagramRelay')
    mocked_datagram_relay.return_value = datagram_relay_test
    datagram_relay_test.debug = AsyncMock()
    datagram_relay_test.serve = AsyncMock()
    path = tmp_path / 'config.json'
    path.write_text(data=json.dumps(config_datagram_relay_dict_test))
    sys.argv = [None, str(path)]

    await main_async()

    datagram_relay_test.debug.assert_called()
    datagram_relay_test.serve.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_proxy(tmp_path, config_datagram_proxy_dict_test, mocker: MockerFixture, datagram_proxy_test):
    mocked_datagram_proxy = mocker.patch('ouija.server.DatagramProxy')
    mocked_datagram_proxy.return_value = datagram_proxy_test
    datagram_proxy_test.debug = AsyncMock()
    datagram_proxy_test.serve = AsyncMock()
    path = tmp_path / 'config.json'
    path.write_text(data=json.dumps(config_datagram_proxy_dict_test))
    sys.argv = [None, str(path)]

    await main_async()

    datagram_proxy_test.debug.assert_called()
    datagram_proxy_test.serve.assert_awaited()
