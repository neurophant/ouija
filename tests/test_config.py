import json

from ouija import Config, Protocol, Mode


def test_config(tmp_path, config_dict_test):
    path = tmp_path / 'config.json'
    path.write_text(data=json.dumps(config_dict_test))

    config = Config(path=str(path))

    assert config.protocol == Protocol.UDP
    assert config.mode == Mode.RELAY
    assert config.debug == True
    assert config.monitor == True
    assert config.relay_host == '127.0.0.1'
    assert config.relay_port == 9000
    assert config.proxy_host == '127.0.0.1'
    assert config.proxy_port == 50000
    assert config.cipher_key == 'bdDmN4VexpDvTrs6gw8xTzaFvIBobFg1Cx2McFB1RmI='
    assert config.entropy_rate == 5
    assert config.token == '395f249c-343a-4f92-9129-68c6d83b5f55'
    assert config.serving_timeout == 20.0
    assert config.tcp_buffer == 1024
    assert config.tcp_timeout == 1.0
    assert config.message_timeout == 5.0
    assert config.udp_min_payload == 512
    assert config.udp_max_payload == 1024
    assert config.udp_timeout == 2.0
    assert config.udp_retries == 5
    assert config.udp_capacity == 1000
    assert config.udp_resend_sleep == 0.25
