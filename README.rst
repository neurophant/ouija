Ouija
=====

Python relay-proxy server and library to build reliable TCP and UDP tunnels for TCP traffic

|pypi|

.. |pypi| image:: https://badge.fury.io/py/ouija.svg
    :target: https://badge.fury.io/py/ouija
    :alt: pypi version

Features
--------

Hides TCP traffic in encrypted TCP/UDP traffic between relay and proxy servers

.. image:: https://raw.githubusercontent.com/neurophant/ouija/main/ouija.png
    :alt: TCP/UDP tunneling
    :width: 800

Requirements
------------

* Python 3.11
* pbjson 1.18.0
* cryptography 41.0.2

Install
-------

.. code-block:: bash

    python3.11 -m venv .env
    source .env/bin/activate
    pip install ouija

Usage
-----

.. code-block:: bash

    ouija <config.json>

tcp-relay.json - HTTPS proxy server interface with TCP connectors:

.. code-block:: json

    {
      "protocol": "TCP",
      "mode": "RELAY",
      "debug": true,
      "monitor": true,
      "relay_host": "127.0.0.1",
      "relay_port": 9000,
      "proxy_host": "127.0.0.1",
      "proxy_port": 50000,
      "key": "bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=",
      "token": "secret",
      "serving_timeout": 20.0,
      "tcp_buffer": 1024,
      "tcp_timeout": 1.0,
      "message_timeout": 5.0
    }

tcp-proxy.json - TCP-relayed proxy server:

.. code-block:: json

    {
      "protocol": "TCP",
      "mode": "PROXY",
      "debug": true,
      "monitor": true,
      "proxy_host": "0.0.0.0",
      "proxy_port": 50000,
      "key": "bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=",
      "token": "secret",
      "serving_timeout": 20.0,
      "tcp_buffer": 1024,
      "tcp_timeout": 1.0,
      "message_timeout": 5.0
    }

udp-relay.json - HTTPS proxy server interface with UDP connectors:

.. code-block:: json

    {
      "protocol": "UDP",
      "mode": "RELAY",
      "debug": true,
      "monitor": true,
      "relay_host": "127.0.0.1",
      "relay_port": 9000,
      "proxy_host": "127.0.0.1",
      "proxy_port": 50000,
      "key": "bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=",
      "token": "secret",
      "serving_timeout": 20.0,
      "tcp_buffer": 1024,
      "tcp_timeout": 1.0,
      "udp_payload": 1024,
      "udp_timeout": 2.0,
      "udp_retries": 5,
      "udp_capacity": 10000,
      "udp_resend_sleep": 0.25
    }

udp-proxy.json - UDP-relayed proxy server:

.. code-block:: json

    {
      "protocol": "UDP",
      "mode": "PROXY",
      "debug": true,
      "monitor": true,
      "proxy_host": "0.0.0.0",
      "proxy_port": 50000,
      "key": "bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI=",
      "token": "secret",
      "serving_timeout": 20.0,
      "tcp_buffer": 1024,
      "tcp_timeout": 1.0,
      "udp_payload": 1024,
      "udp_timeout": 2.0,
      "udp_retries": 5,
      "udp_capacity": 10000,
      "udp_resend_sleep": 0.25
    }

Relay and proxy setup configuration with supervisord - `ouija-config <https://github.com/neurophant/ouija-config>`_

Protocols
---------

* Stream - TCP
* Datagram - UDP

Entities
--------

* Tuning - relay-proxy interaction settings
* Relay - HTTPS proxy server interface
* Connector - relay connector, which communicates with proxy link
* Proxy - proxy server, which gets requests from relay and sends back responses from remote servers
* Link - proxy link with relay connector

Tuning - TCP
------------

* fernet - Fernet instance with provided secret key - use Fernet.generate_key()
* token - your secret token - UUID4 or anything else
* serving_timeout - timeout for serve/resend workers, 2X for handlers, seconds
* tcp_buffer - TCP buffer size, bytes
* tcp_timeout - TCP awaiting timeout, seconds
* message_timeout - TCP service message timeout, seconds

Tuning - UDP
------------

* fernet - Fernet instance with provided secret key - use Fernet.generate_key()
* token - your secret token - UUID4 or anything else
* serving_timeout - timeout for serve/resend workers, 2X for handlers, seconds
* tcp_buffer - TCP buffer size, bytes
* tcp_timeout - TCP awaiting timeout, seconds
* udp_payload - UDP payload size, bytes
* udp_timeout - UDP awaiting timeout, seconds
* udp_retries - UDP max retry count per interaction
* udp_capacity - UDP send/receive buffer capacity - max packet count
* udp_resend_sleep - UDP resend sleep between retries, seconds

Library usage
-------------

stream-relay.py - HTTPS proxy server interface with TCP connectors:

.. code-block:: python

    import asyncio

    from cryptography.fernet import Fernet

    from ouija import StreamRelay as Relay, StreamTuning as Tuning, StreamTelemetry as Telemetry


    async def main() -> None:
        tuning = Tuning(
            fernet=Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
            token='secret',
            serving_timeout=20.0,
            tcp_buffer=1024,
            tcp_timeout=1.0,
            message_timeout=5.0,
        )
        relay = Relay(
            telemetry=Telemetry(),
            tuning=tuning,
            relay_host='127.0.0.1',
            relay_port=9000,
            proxy_host='127.0.0.1',
            proxy_port=50000,
        )
        asyncio.create_task(relay.debug())
        await relay.serve()


    if __name__ == '__main__':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()

stream-proxy.py - TCP-relayed proxy server:

.. code-block:: python

    import asyncio

    from cryptography.fernet import Fernet

    from ouija import StreamProxy as Proxy, StreamTelemetry as Telemetry, StreamTuning as Tuning


    async def main() -> None:
        tuning = Tuning(
            fernet=Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
            token='secret',
            serving_timeout=20.0,
            tcp_buffer=1024,
            tcp_timeout=1.0,
            message_timeout=5.0,
        )
        proxy = Proxy(
            telemetry=Telemetry(),
            tuning=tuning,
            proxy_host='0.0.0.0',
            proxy_port=50000,
        )
        asyncio.create_task(proxy.debug())
        await proxy.serve()


    if __name__ == '__main__':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()

datagram-relay.py - HTTPS proxy server interface with UDP connectors:

.. code-block:: python

    import asyncio

    from cryptography.fernet import Fernet

    from ouija import DatagramRelay as Relay, DatagramTuning as Tuning, DatagramTelemetry as Telemetry


    async def main() -> None:
        tuning = Tuning(
            fernet=Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
            token='secret',
            serving_timeout=20.0,
            tcp_buffer=1024,
            tcp_timeout=1.0,
            udp_payload=1024,
            udp_timeout=2.0,
            udp_retries=5,
            udp_capacity=10000,
            udp_resend_sleep=0.1,
        )
        relay = Relay(
            telemetry=Telemetry(),
            tuning=tuning,
            relay_host='127.0.0.1',
            relay_port=9000,
            proxy_host='127.0.0.1',
            proxy_port=50000,
        )
        asyncio.create_task(relay.debug())
        await relay.serve()


    if __name__ == '__main__':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()

datagram-proxy.py - UDP-relayed proxy server:

.. code-block:: python

    import asyncio

    from cryptography.fernet import Fernet

    from ouija import DatagramProxy as Proxy, DatagramTelemetry as Telemetry, DatagramTuning as Tuning


    async def main() -> None:
        tuning = Tuning(
            fernet=Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
            token='secret',
            serving_timeout=20.0,
            tcp_buffer=1024,
            tcp_timeout=1.0,
            udp_payload=1024,
            udp_timeout=2.0,
            udp_retries=5,
            udp_capacity=10000,
            udp_resend_sleep=0.1,
        )
        proxy = Proxy(
            telemetry=Telemetry(),
            tuning=tuning,
            proxy_host='0.0.0.0',
            proxy_port=50000,
        )
        asyncio.create_task(proxy.debug())
        await proxy.serve()


    if __name__ == '__main__':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()

Tests
-----

.. code-block:: bash

    pytest --cov-report html:htmlcov --cov=ouija tests/
