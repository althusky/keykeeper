import base64

import click
from Crypto.Random import get_random_bytes

from keykeeper.keykeeper_pack.common import ipc_request


@click.group()
def serverkey():
    """server commands"""


@serverkey.command("activate", short_help="Send database AES key to server")
@click.argument("key", type=str)
def activate(key: str):
    """
    Send the provided AES key to the server for activation.

    Args:
        key (str): Base64-encoded AES key string to activate on the server.
    """
    response = ipc_request({"serverkey": "activate", "key": key})
    if response["result"] == "ok":
        click.secho(response["msg"], fg="green")
    else:
        click.secho(response["result"], fg="red")


@serverkey.command("generate", short_help="Generate AES key for database")
def generate():
    """Generate a 16-byte AES key and display it base64-encoded."""
    aes_key = get_random_bytes(16)
    base64_key = base64.b64encode(aes_key).decode("utf-8")
    click.echo("AES key for database: ", nl=False)
    click.secho(str(base64_key), fg="green")
