#!/usr/bin/env python3
import click

from keykeeper.keykeeper_pack.backup import backup
from keykeeper.keykeeper_pack.secrets import secret
from keykeeper.keykeeper_pack.server import serverkey
from keykeeper.keykeeper_pack.users import user


@click.group()
def cli():
    """
    Main command group for the CLI application.

    This function serves as the entry point for the command line interface,
    grouping all subcommands under a single CLI group.
    """


cli.add_command(user)
cli.add_command(secret)
cli.add_command(serverkey)
cli.add_command(backup)

if __name__ == "__main__":
    cli()
