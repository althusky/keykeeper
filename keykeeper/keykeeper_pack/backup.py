import json
import sys

import click

from keykeeper.keykeeper_pack.common import ipc_request


@click.group()
def backup():
    """backup commands"""


@backup.command(
    "dump", short_help="Returns a database backup via stdout in JSON format."
)
def dump():
    response = ipc_request({"backup": "dump"})
    if response["result"] == "ok":
        sys.stdout.write(json.dumps(response["dump"], indent=2))
    else:
        click.secho(response["result"], fg="red")


@backup.command(
    "load",
    short_help="Loads data into the database. Transfer via pipeline. cat dump.json | keykeeper backup load",
)
def load():
    if not sys.stdin.isatty():
        pipe_input = sys.stdin.read()
        try:
            dump = json.loads(pipe_input)
        except ValueError:
            click.echo("Error in JSON data")
            sys.exit(1)
        response = ipc_request({"backup": "load", "dump": dump})

        if response["result"] == "ok":
            click.secho(response["msg"], fg="green")
        else:
            click.secho(response["result"], fg="red")
        return
    click.echo("stdin is empty, could not receive data")
