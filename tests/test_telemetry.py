import datetime

from pytest_mock import MockerFixture


def test_telemetry_link(telemetry_test):
    telemetry_test.collect(active=10)

    assert telemetry_test.active == 10


def test_telemetry_open(telemetry_test):
    telemetry_test.open()

    assert telemetry_test.opened == 1


def test_telemetry_close(telemetry_test):
    telemetry_test.close()

    assert telemetry_test.closed == 1


def test_telemetry_send(telemetry_test, data_test, entropy_test):
    telemetry_test.send(data=data_test, entropy=entropy_test)

    assert telemetry_test.payloads_sent == 1
    assert telemetry_test.bytes_sent == 9
    assert telemetry_test.min_payload_size == 9
    assert telemetry_test.max_payload_size == 9


def test_telemetry_recv(telemetry_test, data_test, entropy_test):
    telemetry_test.recv(data=data_test, entropy=entropy_test)

    assert telemetry_test.payloads_recv == 1
    assert telemetry_test.bytes_recv == 9
    assert telemetry_test.min_payload_size == 9
    assert telemetry_test.max_payload_size == 9


def test_telemetry_processing_error(telemetry_test):
    telemetry_test.processing_error()

    assert telemetry_test.processing_errors == 1


def test_telemetry_token_error(telemetry_test):
    telemetry_test.token_error()

    assert telemetry_test.token_errors == 1


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
        f'\tactive: 0\n' \
        f'\topened|closed: 0|0\n' \
        f'\tpayloads sent|received: 0|0\n' \
        f'\tbytes sent|received: 0|0\n' \
        f'\tmin|avg|max payload size: ' \
        f'0|0|0\n' \
        f'\tmin|avg|max entropy: 0.0000|0.0000|0.0000\n' \
        f'\ttoken errors: 0\n' \
        f'\tprocessing|resending errors: 0|0\n' \
        f'\ttimeout|connection|serving errors: ' \
        f'0|0|0\n' \
        f'\tsend|recv buf overloads: 0|0'

    assert str(telemetry_test) == expected
