import base64
import binascii
import json
import urllib.error
import urllib.request

from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256


class ProtocolBrokenError(Exception):
    """Exception raised when message integrity verification fails."""


class BaseProtocol:
    """
    Provides encryption and HMAC signing for secure message exchange.

    Attributes:
        aes_key (bytes): AES encryption key (16 bytes).
        hmac_key (bytes): HMAC key for message authentication.
    """

    def __init__(self, key: str):
        """
        Initialize the protocol with a base64-encoded key.

        The key is decoded and split into AES and HMAC keys.

        Args:
            key (str): Base64-encoded key string ( AES(16bit) + HMAC(16bit) ).
        """
        full_key = base64.b64decode(key.encode("utf-8"))
        self.aes_key = full_key[:16]
        self.hmac_key = full_key[16:]

    def code_msg(self, dict_msg: dict) -> str:
        """
        Encrypt and sign a dictionary message.

        The message is serialized to JSON, encrypted with AES-CTR,
        and signed with HMAC-SHA256. The result is base64-encoded.

        Args:
            dict_msg (dict): The message to encrypt.

        Returns:
            str: Base64-encoded encrypted and signed message.
        """
        cipher = AES.new(self.aes_key, AES.MODE_CTR)
        ciphertext = cipher.encrypt(json.dumps(dict_msg).encode("utf-8"))

        hmac = HMAC.new(self.hmac_key, digestmod=SHA256)
        hmac.update(cipher.nonce + ciphertext)
        tag = hmac.digest()

        packet = b"".join([tag, cipher.nonce, ciphertext])

        b64 = base64.b64encode(packet)
        return b64.decode("utf-8")

    def decode_msg(self, send_msg: str) -> dict:
        """
        Verify and decrypt a base64-encoded message string.

        The message is base64-decoded, HMAC-verified, and decrypted.
        Raises ProtocolBrokenError if verification fails.

        Args:
            send_msg (str): Base64-encoded encrypted message.

        Returns:
            dict: The decrypted message as a dictionary.

        Raises:
            ProtocolBrokenError: If message integrity verification fails.
        """
        byte_msg = base64.b64decode(send_msg.encode("utf-8"))
        tag = byte_msg[:32]
        nonce = byte_msg[32:40]
        ciphertext = byte_msg[40:]

        try:
            hmac = HMAC.new(self.hmac_key, digestmod=SHA256)
            hmac.update(nonce + ciphertext)
            hmac.verify(tag)
        except ValueError:
            raise ProtocolBrokenError("The message was modified!")

        cipher = AES.new(self.aes_key, AES.MODE_CTR, nonce=nonce)
        msg_str = cipher.decrypt(ciphertext).decode("utf-8")
        return json.loads(msg_str)


def keykeeper(url: str, key: str, name: str, value: None | str = None) -> str:
    """
    Send encrypted request to keykeeper server and return secret value.
    Encrypts a message with the given name and optional value using BaseProtocol,
    sends it via HTTP POST to the specified URL, and decrypts the response.
    Raises ConnectionError on HTTP or decoding errors.
    Args:
        url (str): Server URL, e.g. "http://127.0.0.1:PORT".
        key (str): Base64-encoded AES+HMAC key for encryption.
        name (str): Name of the secret to get or set.
        value (None | str): Optional value to set for the secret.
    Returns:
        str: The secret value returned by the server or empty string on failure.
    """

    protocol = BaseProtocol(key)

    if value is None:
        send_str = protocol.code_msg({"name": name})
    else:
        send_str = protocol.code_msg({"name": name, "value": value})

    send_byte = send_str.encode("utf-8")
    req = urllib.request.Request(url, data=send_byte, method="POST")
    req.add_header("Content-Type", "application/octet-stream")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            response_body = response.read().decode("utf-8")
            response_data = protocol.decode_msg(response_body)
            return response_data["value"]
    except urllib.error.HTTPError as ex:
        match ex.code:
            case 500:
                raise ConnectionError("The server is not ready")
            case 422:
                raise ConnectionError("Can't rewrite readonly secret")
            case 401:
                raise ConnectionError("The server did not find the user.")
            case 404:
                raise ConnectionError("The unknown secret.")
            case 400:
                raise ConnectionError("Invalid request format.")

    except (binascii.Error, ValueError):
        raise ConnectionError("Can't process the response")

    return ""
