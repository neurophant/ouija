import datetime

from pytest_mock import MockerFixture

from ouija import Telemetry


def test_telemetry_link():
    telemetry = Telemetry()
    telemetry.link(links=10)
    assert telemetry.links == 10


def test_telemetry_open():
    telemetry = Telemetry()
    telemetry.open()
    assert telemetry.opened == 1


def test_telemetry_close():
    telemetry = Telemetry()
    telemetry.close()
    assert telemetry.closed == 1


def test_telemetry_send():
    telemetry = Telemetry()
    telemetry.send(data=b'test data')
    assert telemetry.packets_sent == 1
    assert telemetry.bytes_sent == 9
    assert telemetry.min_packet_size == 9
    assert telemetry.max_packet_size == 9


def test_telemetry_recv():
    telemetry = Telemetry()
    telemetry.recv(data=b'test data')
    assert telemetry.packets_recv == 1
    assert telemetry.bytes_recv == 9
    assert telemetry.min_packet_size == 9
    assert telemetry.max_packet_size == 9


def test_telemetry_processing_error():
    telemetry = Telemetry()
    telemetry.processing_error()
    assert telemetry.processing_errors == 1


def test_telemetry_token_error():
    telemetry = Telemetry()
    telemetry.token_error()
    assert telemetry.token_errors == 1


def test_telemetry_type_error():
    telemetry = Telemetry()
    telemetry.type_error()
    assert telemetry.type_errors == 1


def test_telemetry_timeout_error():
    telemetry = Telemetry()
    telemetry.timeout_error()
    assert telemetry.timeout_errors == 1


def test_telemetry_connection_error():
    telemetry = Telemetry()
    telemetry.connection_error()
    assert telemetry.connection_errors == 1


def test_telemetry_serving_error():
    telemetry = Telemetry()
    telemetry.serving_error()
    assert telemetry.serving_errors == 1


def test_telemetry_resending_error():
    telemetry = Telemetry()
    telemetry.resending_error()
    assert telemetry.resending_errors == 1


def test_telemetry_send_buf_overload():
    telemetry = Telemetry()
    telemetry.send_buf_overload()
    assert telemetry.send_buf_overloads == 1


def test_telemetry_recv_buf_overload():
    telemetry = Telemetry()
    telemetry.recv_buf_overload()
    assert telemetry.recv_buf_overloads == 1


def test_telemetry(mocker: MockerFixture):
    timestamp = datetime.datetime.now()
    mocked_datetime = mocker.patch('ouija.telemetry.datetime')
    mocked_datetime.datetime.now.return_value = timestamp
    telemetry = Telemetry()
    expected = \
        f'{timestamp}\n' \
        f'\tlinks: 0\n' \
        f'\topened|closed: 0|0\n' \
        f'\tpackets sent|received: 0|0\n' \
        f'\tbytes sent|received: 0|0\n' \
        f'\tmin|max packet size: 0|0\n' \
        f'\tprocessing|token|type errors: 0|0' \
        f'|0\n' \
        f'\ttimeout|connection|serving|resending errors: 0|0' \
        f'|0|0\n' \
        f'\tsend|recv buf overloads: 0|0'
    assert str(telemetry) == expected
