from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from ouija import RawParser


@pytest.mark.asyncio
async def test_interface_https_handler(interface_test, relay_test, mocker: MockerFixture):
    mocked_relay = mocker.patch('ouija.interface.Relay')
    mocked_relay.return_value = relay_test
    relay_test.serve = AsyncMock()
    await interface_test.https_handler(
        reader=AsyncMock(),
        writer=AsyncMock(),
        remote_host='example.com',
        remote_port=443,
    )
    relay_test.serve.assert_awaited()


@pytest.mark.asyncio
async def test_interface_session_wrapped(interface_test):
    reader = AsyncMock()
    reader.readuntil = AsyncMock(return_value=b'CONNECT https://example.com:443 HTTP/1.1')
    interface_test.https_handler = AsyncMock()
    await interface_test.session_wrapped(reader=reader, writer=AsyncMock())
    interface_test.https_handler.assert_awaited()


@pytest.mark.asyncio
async def test_interface_session_wrapped_request_error(interface_test, mocker: MockerFixture):
    reader = AsyncMock()
    reader.readuntil = AsyncMock(return_value=b'CONNECT https://example.com:443 HTTP/1.1')
    interface_test.https_handler = AsyncMock()
    mocked_rawparser = mocker.patch('ouija.interface.RawParser')
    mocked_rawparser.return_value = RawParser(data=b'')
    await interface_test.session_wrapped(reader=reader, writer=AsyncMock())
    interface_test.https_handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_interface_session_wrapped_method_error(interface_test):
    reader = AsyncMock()
    reader.readuntil = AsyncMock(return_value=b'GET example.com HTTP/1.1')
    interface_test.https_handler = AsyncMock()
    await interface_test.session_wrapped(reader=reader, writer=AsyncMock())
    interface_test.https_handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_interface_session(interface_test):
    interface_test.session_wrapped = AsyncMock()
    await interface_test.session(index=0, reader=AsyncMock(), writer=AsyncMock())
    interface_test.session_wrapped.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=TimeoutError)
async def test_interface_session_timeouterror(interface_test):
    interface_test.session_wrapped = AsyncMock()
    interface_test.session_wrapped.side_effect = TimeoutError()
    await interface_test.session(index=0, reader=AsyncMock(), writer=AsyncMock())
    interface_test.session_wrapped.assert_awaited()


@pytest.mark.asyncio
@pytest.mark.xfail(raises=Exception)
async def test_interface_session_exception(interface_test):
    interface_test.session_wrapped = AsyncMock()
    interface_test.session_wrapped.side_effect = Exception()
    await interface_test.session(index=0, reader=AsyncMock(), writer=AsyncMock())
    interface_test.session_wrapped.assert_awaited()


@pytest.mark.asyncio
async def test_interface_serve(interface_test):
    interface_test.session = AsyncMock()
    await interface_test.serve(reader=AsyncMock(), writer=AsyncMock())
    interface_test.session.assert_called()
