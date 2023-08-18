import datetime

from pytest_mock import MockerFixture


def test_stream_telemetry_link(stream_telemetry_test):
    stream_telemetry_test.collect(active=10)

    assert stream_telemetry_test.active == 10


def test_stream_telemetry_open(stream_telemetry_test):
    stream_telemetry_test.open()

    assert stream_telemetry_test.opened == 1


def test_stream_telemetry_close(stream_telemetry_test):
    stream_telemetry_test.close()

    assert stream_telemetry_test.closed == 1


def test_stream_telemetry_send(stream_telemetry_test, data_test):
    stream_telemetry_test.send(data=data_test)

    assert stream_telemetry_test.bytes_sent == 9


def test_stream_telemetry_recv(stream_telemetry_test, data_test):
    stream_telemetry_test.recv(data=data_test)

    assert stream_telemetry_test.bytes_recv == 9


def test_stream_telemetry_token_error(stream_telemetry_test):
    stream_telemetry_test.token_error()

    assert stream_telemetry_test.token_errors == 1


def test_stream_telemetry_timeout_error(stream_telemetry_test):
    stream_telemetry_test.timeout_error()

    assert stream_telemetry_test.timeout_errors == 1


def test_stream_telemetry_connection_error(stream_telemetry_test):
    stream_telemetry_test.connection_error()

    assert stream_telemetry_test.connection_errors == 1


def test_stream_telemetry_serving_error(stream_telemetry_test):
    stream_telemetry_test.serving_error()

    assert stream_telemetry_test.serving_errors == 1


def test_stream_telemetry(stream_telemetry_test, mocker: MockerFixture):
    timestamp = datetime.datetime.now()
    mocked_datetime = mocker.patch('ouija.telemetry.datetime')
    mocked_datetime.datetime.now.return_value = timestamp
    expected = \
        f'{timestamp}\n' \
        f'\tactive: 0\n' \
        f'\topened|closed: 0|0\n' \
        f'\tbytes sent|received: 0|0\n' \
        f'\ttoken|timeout|connection|serving errors: 0|0|0|0'

    assert str(stream_telemetry_test) == expected


def test_datagram_telemetry_link(datagram_telemetry_test):
    datagram_telemetry_test.collect(active=10)

    assert datagram_telemetry_test.active == 10


def test_datagram_telemetry_open(datagram_telemetry_test):
    datagram_telemetry_test.open()

    assert datagram_telemetry_test.opened == 1


def test_datagram_telemetry_close(datagram_telemetry_test):
    datagram_telemetry_test.close()

    assert datagram_telemetry_test.closed == 1


def test_datagram_telemetry_send(datagram_telemetry_test, data_test):
    datagram_telemetry_test.send(data=data_test)

    assert datagram_telemetry_test.packets_sent == 1
    assert datagram_telemetry_test.bytes_sent == 9
    assert datagram_telemetry_test.min_packet_size == 9
    assert datagram_telemetry_test.max_packet_size == 9


def test_datagram_telemetry_recv(datagram_telemetry_test, data_test):
    datagram_telemetry_test.recv(data=data_test)

    assert datagram_telemetry_test.packets_recv == 1
    assert datagram_telemetry_test.bytes_recv == 9
    assert datagram_telemetry_test.min_packet_size == 9
    assert datagram_telemetry_test.max_packet_size == 9


def test_datagram_telemetry_processing_error(datagram_telemetry_test):
    datagram_telemetry_test.processing_error()

    assert datagram_telemetry_test.processing_errors == 1


def test_datagram_telemetry_token_error(datagram_telemetry_test):
    datagram_telemetry_test.token_error()

    assert datagram_telemetry_test.token_errors == 1


def test_datagram_telemetry_type_error(datagram_telemetry_test):
    datagram_telemetry_test.type_error()

    assert datagram_telemetry_test.type_errors == 1


def test_datagram_telemetry_timeout_error(datagram_telemetry_test):
    datagram_telemetry_test.timeout_error()

    assert datagram_telemetry_test.timeout_errors == 1


def test_datagram_telemetry_connection_error(datagram_telemetry_test):
    datagram_telemetry_test.connection_error()

    assert datagram_telemetry_test.connection_errors == 1


def test_datagram_telemetry_serving_error(datagram_telemetry_test):
    datagram_telemetry_test.serving_error()

    assert datagram_telemetry_test.serving_errors == 1


def test_datagram_telemetry_resending_error(datagram_telemetry_test):
    datagram_telemetry_test.resending_error()

    assert datagram_telemetry_test.resending_errors == 1


def test_datagram_telemetry_send_buf_overload(datagram_telemetry_test):
    datagram_telemetry_test.send_buf_overload()

    assert datagram_telemetry_test.send_buf_overloads == 1


def test_datagram_telemetry_recv_buf_overload(datagram_telemetry_test):
    datagram_telemetry_test.recv_buf_overload()

    assert datagram_telemetry_test.recv_buf_overloads == 1


def test_datagram_telemetry(datagram_telemetry_test, mocker: MockerFixture):
    timestamp = datetime.datetime.now()
    mocked_datetime = mocker.patch('ouija.telemetry.datetime')
    mocked_datetime.datetime.now.return_value = timestamp
    expected = \
        f'{timestamp}\n' \
        f'\tactive: 0\n' \
        f'\topened|closed: 0|0\n' \
        f'\tpackets sent|received: 0|0\n' \
        f'\tbytes sent|received: 0|0\n' \
        f'\tmin|max packet size: 0|0\n' \
        f'\tprocessing|token|type errors: 0|0' \
        f'|0\n' \
        f'\ttimeout|connection|serving|resending errors: 0|0' \
        f'|0|0\n' \
        f'\tsend|recv buf overloads: 0|0'

    assert str(datagram_telemetry_test) == expected
