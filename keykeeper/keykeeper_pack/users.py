import click

from keykeeper.keykeeper_pack.common import ipc_request


@click.group()
def user():
    """Commands for users control"""
    pass


@user.command("edit", short_help="Edit or append user")
@click.argument("name", type=str)
@click.option("-d", "--descr", type=str, default="", help="User description")
@click.option(
    "-c",
    "--create",
    is_flag=True,
    default=False,
    show_default=True,
    help="Create new user with 'name'",
)
@click.option(
    "-a",
    "--active",
    is_flag=True,
    default=False,
    show_default=True,
    help="Create active user just after create",
)
def edit(name: str, descr: str, create: bool, active: bool):
    """
    NAME -  user name.
    \f
    descr - user description

    """

    response = ipc_request(
        {
            "user": "edit",
            "name": name,
            "descr": descr,
            "create": create,
            "active": active,
        }
    )
    if response["result"] == "ok":
        click.secho(response["msg"], fg="green")
        click.secho(f"User key: {response['key']}", fg="red")
    else:
        click.secho(response["result"], fg="red")


@user.command("secret", short_help="Manage key attached to user")
@click.argument("name", type=str)
@click.argument("action", type=click.Choice(["ls", "add", "remove"]))
@click.argument("secret_name", type=str, required=False)
def secret(name: str, action: str, secret_name: None | str = None):
    """
    NAME - user name
    ACTION - [ls|add|remove] - command
    SECRET_NAME - secret name
    \f
    """

    response = ipc_request(
        {
            "user": "secret",
            "name": name,
            "action": action,
            "secret_name": secret_name,
        }
    )
    if response["result"] == "ok" and action == "ls" and "lines" in response:
        if not response["lines"]:
            click.secho("< empty >", fg="green")
            return
        name_max = max(map(lambda x: len(x[0]), response["lines"]))
        for line in response["lines"]:
            click.echo(f"{line[0]:<{name_max}} |", nl=False)
            if line[1]:
                click.secho(" active ", fg="green", nl=False)
            else:
                click.secho(" lock   ", fg="red", nl=False)
            if line[2]:
                click.secho("| ro |", fg="green", nl=False)
            else:
                click.secho("|    |", fg="red", nl=False)
            click.echo(f" {line[3]}")

    elif response["result"] == "ok":
        click.secho(response["msg"], fg="green")
    else:
        click.secho(response["result"], fg="red")


@user.command("ls", short_help="Shows a list of users")
def ls():
    """Show a list of users and their status."""

    response = ipc_request({"user": "ls"})

    if response["result"] == "ok" and "lines" in response:
        if not response["lines"]:
            click.secho("< empty >", fg="green")
            return
        name_max = max(map(lambda x: len(x[0]), response["lines"]))
        for line in response["lines"]:
            click.echo(f"{line[0]:<{name_max}} |", nl=False)
            if line[1]:
                click.secho(" active ", fg="green", nl=False)
            else:
                click.secho(" lock   ", fg="red", nl=False)
            click.echo(f"| {line[2]}")
    else:
        click.secho(response["result"], fg="red")
