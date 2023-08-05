from ouija import RawParser


def test_rawparser_connect():
    request = RawParser(data=b'CONNECT example.com:443 HTTP/1.1')
    assert request.method == 'CONNECT'
    assert request.uri == 'example.com:443'
    assert request.host == 'example.com'
    assert request.port == 443
    assert not request.error


def test_rawparser_get():
    request = RawParser(data=b'GET /index.html')
    assert request.error


def test_rawparser():
    request = RawParser(data=b'CONNECT example.com:443 HTTP/1.1')
    expected = dict(URI=request.uri, HOST=request.host, PORT=request.port, METHOD=request.method)
    assert str(request) == str(expected)
