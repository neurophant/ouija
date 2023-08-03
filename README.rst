Ouija
=====

Python library for building and accessing UDP-relayed TCP proxies

Features
--------

Objects:

* Interface - basic HTTPS proxy server
* Tuning - Relay-Proxy settings
* Relay - HTTPS proxy interface, which communicates with Proxy via encrypted UDP
* Proxy - UDP server, which gets requests from Relay and sends back responses from target TCP servers

Tuning:

* fernet - Fernet instance with provided secret key - use Fernet.generate_key()
* token - your secret token - UUID4 or anything else
* serving_timeout - total timeout per worker in seconds
* tcp_buffer - TCP buffer size in bytes
* tcp_timeout - TCP awaiting timeout in seconds
* udp_payload - UDP payload size in bytes
* udp_timeout - UDP awaiting timeout in seconds
* udp_retries - UDP max retry count per interaction
* udp_capacity - UDP send/receive buffer capacity in packets

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

examples:
    * ouija-relay - simple HTTPS proxy server interface
    * ouija-proxy - UDP-relayed TCP proxy server

Tests
-----

TBD
