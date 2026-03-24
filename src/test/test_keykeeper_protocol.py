import logging

from keykeeper_protocol import BaseProtocol
from server_pack.users import key_gen


def test_init():
    key = key_gen()
    protocol = BaseProtocol(key)
    logging.debug(f"aes key len: {len(protocol.aes_key)}")
    logging.debug(f"hmac key len: {len(protocol.hmac_key)}")


def test_transfer():
    key = key_gen()
    protocol = BaseProtocol(key)

    control_message = '{"get": "my_test_secret"}'

    transfer = protocol.code_msg(control_message)
    logging.debug(f"{transfer}")

    assert control_message == protocol.decode_msg(transfer)
