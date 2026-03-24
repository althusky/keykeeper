import json
import socket

import click

SOCKET_PATH = "/tmp/keykeeper.sock"


def ipc_request(request: dict) -> dict:
    """
    Send a JSON-encoded request to a UNIX socket server and receive a JSON
    response.

    Args:
        request (dict): The request data to send to the server.

    Returns:
        dict: The JSON-decoded response from the server.

    Raises:
        SystemExit: If the response is not valid JSON or the server socket is
        not found.
    """

    send_json = json.dumps(request)
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.sendall(send_json.encode("utf-8"))
            chunks = []
            while True:
                data = client.recv(1024)
                if not data:
                    break
                chunks.append(data)
            data = b"".join(chunks)
        return json.loads(data.decode("utf-8"))

    except json.JSONDecodeError as e:
        click.secho(f"Invalid JSON response: {e}", fg="red", color=True)
        raise SystemExit(1)
    except FileNotFoundError:
        click.secho("Can't connect to server!", fg="red", color=True)
        click.echo("Maybe it's not turned on")
        raise SystemExit(1)
