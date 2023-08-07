import datetime

from pytest_mock import MockerFixture


def test_telemetry_link(telemetry_test):
    telemetry_test.link(links=10)
    assert telemetry_test.links == 10


def test_telemetry_open(telemetry_test):
    telemetry_test.open()
    assert telemetry_test.opened == 1


def test_telemetry_close(telemetry_test):
    telemetry_test.close()
    assert telemetry_test.closed == 1


def test_telemetry_send(telemetry_test, data_test):
    telemetry_test.send(data=data_test)
    assert telemetry_test.packets_sent == 1
    assert telemetry_test.bytes_sent == 9
    assert telemetry_test.min_packet_size == 9
    assert telemetry_test.max_packet_size == 9


def test_telemetry_recv(telemetry_test, data_test):
    telemetry_test.recv(data=data_test)
    assert telemetry_test.packets_recv == 1
    assert telemetry_test.bytes_recv == 9
    assert telemetry_test.min_packet_size == 9
    assert telemetry_test.max_packet_size == 9


def test_telemetry_processing_error(telemetry_test):
    telemetry_test.processing_error()
    assert telemetry_test.processing_errors == 1


def test_telemetry_token_error(telemetry_test):
    telemetry_test.token_error()
    assert telemetry_test.token_errors == 1


def test_telemetry_type_error(telemetry_test):
    telemetry_test.type_error()
    assert telemetry_test.type_errors == 1


def test_telemetry_timeout_error(telemetry_test):
    telemetry_test.timeout_error()
    assert telemetry_test.timeout_errors == 1


def test_telemetry_connection_error(telemetry_test):
    telemetry_test.connection_error()
    assert telemetry_test.connection_errors == 1


def test_telemetry_serving_error(telemetry_test):
    telemetry_test.serving_error()
    assert telemetry_test.serving_errors == 1


def test_telemetry_resending_error(telemetry_test):
    telemetry_test.resending_error()
    assert telemetry_test.resending_errors == 1


def test_telemetry_send_buf_overload(telemetry_test):
    telemetry_test.send_buf_overload()
    assert telemetry_test.send_buf_overloads == 1


def test_telemetry_recv_buf_overload(telemetry_test):
    telemetry_test.recv_buf_overload()
    assert telemetry_test.recv_buf_overloads == 1


def test_telemetry(telemetry_test, mocker: MockerFixture):
    timestamp = datetime.datetime.now()
    mocked_datetime = mocker.patch('ouija.telemetry.datetime')
    mocked_datetime.datetime.now.return_value = timestamp
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
    assert str(telemetry_test) == expected
