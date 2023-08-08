Ouija
=====

Python library for building and accessing UDP-relayed TCP proxies

|pypi|

.. |pypi| image:: https://badge.fury.io/py/ouija.png
    :target: https://badge.fury.io/py/ouija
    :alt: pypi version

Features
--------

Hides TCP traffic in encrypted UDP traffic between relay and proxy servers

.. image:: https://raw.githubusercontent.com/neurophant/ouija/1.0.0/ouija.png
    :alt: Sliding from center to edge - searching for maximum entropy difference
    :width: 800

Key entities
------------

* Tuning - Relay-Proxy interaction settings
* Interface - HTTPS proxy server interface
* Relay - HTTPS proxy relay, which communicates with Proxy via encrypted UDP
* Proxy - UDP server, which gets requests from Relay and sends back responses from remote TCP servers
* Link - Relay link within Proxy

Tuning
------

* fernet - Fernet instance with provided secret key - use Fernet.generate_key()
* token - your secret token - UUID4 or anything else
* serving_timeout - total timeout per worker, seconds
* tcp_buffer - TCP buffer size, bytes
* tcp_timeout - TCP awaiting timeout, seconds
* udp_payload - UDP payload size, bytes
* udp_timeout - UDP awaiting timeout, seconds
* udp_retries - UDP max retry count per interaction
* udp_capacity - UDP send/receive buffer capacity - max packet count

Requirements
------------

* Python 3.11+
* pbjson 1.18.0+
* cryptography 41.0.2+

Setup
-----

.. code-block:: bash

    python -m venv .env
    source .env/bin/activate
    pip install ouija

Usage
-----

ouija-relay - HTTPS proxy server interface:

.. code-block:: python

    import asyncio

    from cryptography.fernet import Fernet

    from ouija import Interface, Tuning, Telemetry


    async def main() -> None:
        tuning = Tuning(
            fernet=Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
            token='secret',
            serving_timeout=30,
            tcp_buffer=2048,
            tcp_timeout=1,
            udp_payload=1024,
            udp_timeout=3,
            udp_retries=5,
            udp_capacity=1000,
        )
        interface = Interface(
            telemetry=Telemetry(),
            tuning=tuning,
            proxy_host='127.0.0.1',
            proxy_port=50000,
        )
        asyncio.create_task(interface.debug())
        server = await asyncio.start_server(
            interface.serve,
            '127.0.0.1',
            9000,
        )
        async with server:
            await server.serve_forever()


    if __name__ == '__main__':
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.run_forever()

ouija-proxy - UDP-relayed TCP proxy server:

.. code-block:: python

    import asyncio

    from cryptography.fernet import Fernet

    from ouija import Proxy, Telemetry, Tuning


    async def main() -> None:
        tuning = Tuning(
            fernet=Fernet('bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='),
            token='secret',
            serving_timeout=30,
            tcp_buffer=2048,
            tcp_timeout=1,
            udp_payload=1024,
            udp_timeout=3,
            udp_retries=5,
            udp_capacity=1000,
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
