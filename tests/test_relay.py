from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from ouija import Parser
from ouija.relay import Relay


@pytest.mark.asyncio
@pytest.mark.xfail(raises=NotImplementedError)
async def test_relay_https_handler(stream_telemetry_test, stream_tuning_test):
    relay = Relay(
        telemetry=stream_telemetry_test,
        tuning=stream_tuning_test,
        relay_host='127.0.0.1',
        relay_port=9000,
        proxy_host='127.0.0.1',
        proxy_port=50000,
    )

    await relay.https_handler(reader=AsyncMock(), writer=AsyncMock(), remote_host='example.com', remote_port=443)


@pytest.mark.asyncio
async def test_stream_relay_https_handler(stream_relay_test, stream_connector_test, mocker: MockerFixture):
    mocked_stream_connector = mocker.patch('ouija.relay.StreamConnector')
    mocked_stream_connector.return_value = stream_connector_test
    stream_connector_test.serve = AsyncMock()

    await stream_relay_test.https_handler(
        reader=AsyncMock(),
        writer=AsyncMock(),
        remote_host='example.com',
        remote_port=443,
    )

    stream_connector_test.serve.assert_awaited()


@pytest.mark.asyncio
async def test_datagram_relay_https_handler(datagram_relay_test, datagram_connector_test, mocker: MockerFixture):
    mocked_datagram_connector = mocker.patch('ouija.relay.DatagramConnector')
    mocked_datagram_connector.return_value = datagram_connector_test
    datagram_connector_test.serve = AsyncMock()

    await datagram_relay_test.https_handler(
        reader=AsyncMock(),
        writer=AsyncMock(),
        remote_host='example.com',
        remote_port=443,
    )

    datagram_connector_test.serve.assert_awaited()


@pytest.mark.asyncio
async def test_relay_connect_wrapped(datagram_relay_test):
    reader = AsyncMock()
    reader.readuntil = AsyncMock(return_value=b'CONNECT https://example.com:443 HTTP/1.1')
    datagram_relay_test.https_handler = AsyncMock()

    await datagram_relay_test.connect_wrapped(reader=reader, writer=AsyncMock())

    datagram_relay_test.https_handler.assert_awaited()


@pytest.mark.asyncio
async def test_relay_connect_wrapped_request_error(datagram_relay_test, mocker: MockerFixture):
    reader = AsyncMock()
    reader.readuntil = AsyncMock(return_value=b'CONNECT https://example.com:443 HTTP/1.1')
    datagram_relay_test.https_handler = AsyncMock()
    mocked_rawparser = mocker.patch('ouija.relay.Parser')
    mocked_rawparser.return_value = Parser(data=b'')

    await datagram_relay_test.connect_wrapped(reader=reader, writer=AsyncMock())

    datagram_relay_test.https_handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_relay_connect_wrapped_method_error(datagram_relay_test):
    reader = AsyncMock()
    reader.readuntil = AsyncMock(return_value=b'GET example.com HTTP/1.1')
    datagram_relay_test.https_handler = AsyncMock()

    await datagram_relay_test.connect_wrapped(reader=reader, writer=AsyncMock())

    datagram_relay_test.https_handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_relay_connect(datagram_relay_test):
    datagram_relay_test.connect_wrapped = AsyncMock()

    await datagram_relay_test.connect(reader=AsyncMock(), writer=AsyncMock())

    datagram_relay_test.connect_wrapped.assert_awaited()


@pytest.mark.asyncio
async def test_relay_connect_timeouterror(datagram_relay_test):
    datagram_relay_test.connect_wrapped = AsyncMock()
    datagram_relay_test.connect_wrapped.side_effect = TimeoutError()

    await datagram_relay_test.connect(reader=AsyncMock(), writer=AsyncMock())

    datagram_relay_test.connect_wrapped.assert_awaited()


@pytest.mark.asyncio
async def test_relay_session_exception(datagram_relay_test):
    datagram_relay_test.connect_wrapped = AsyncMock()
    datagram_relay_test.connect_wrapped.side_effect = Exception()

    await datagram_relay_test.connect(reader=AsyncMock(), writer=AsyncMock())

    datagram_relay_test.connect_wrapped.assert_awaited()


@pytest.mark.asyncio
async def test_relay_handle(datagram_relay_test):
    datagram_relay_test.connect = AsyncMock()

    await datagram_relay_test.handle(reader=AsyncMock(), writer=AsyncMock())

    datagram_relay_test.connect.assert_called()


@pytest.mark.asyncio
async def test_relay_serve(datagram_relay_test, mocker: MockerFixture):
    mocked_asyncio = mocker.patch('ouija.relay.asyncio')
    mocked_asyncio.start_server = AsyncMock()

    await datagram_relay_test.serve()

    mocked_asyncio.start_server.assert_awaited()
