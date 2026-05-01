import click

from keykeeper.keykeeper_pack.common import ipc_request


@click.group()
def secret():
    """user commands"""
    pass


@secret.command("edit", short_help="Edit or append secret")
@click.argument("name", type=str)
@click.argument("value", type=str)
@click.option("-d", "--descr", type=str, default="", help="User description")
@click.option(
    "--readonly/--no-readonly",
    default=False,
    show_default=True,
    help="Readonly allow only read from web interface",
)
@click.option(
    "-c",
    "--create",
    is_flag=True,
    default=False,
    show_default=True,
    help="Create new secret with 'name'",
)
@click.option(
    "-a",
    "--active",
    is_flag=True,
    default=False,
    show_default=True,
    help="Create active secret just after create",
)
def edit(
    name: str,
    value: str,
    descr: str,
    readonly: bool,
    active: bool,
    create: bool,
):
    """
    NAME - secret name
    VALUE - secret value
    """
    response = ipc_request(
        {
            "secret": "edit",
            "name": name,
            "value": value,
            "descr": descr,
            "active": active,
            "readonly": readonly,
            "create": create,
        }
    )
    if response["result"] == "ok":
        click.secho(response["msg"], fg="green")
    else:
        click.secho(response["result"], fg="red")


@secret.command("remove", short_help="Delete secret")
@click.argument("name", type=str)
@click.option("--yes", is_flag=True, help="Delete without confirmation")
def remove(name: str, yes: bool = False):
    """
    NAME - secret name
    \f
    """
    if not yes:
        click.secho(f"Secret: {name} will be deleted!!", fg="red")
        if not click.confirm("Continue ?", abort=False, show_default=False):
            click.secho(f"Deletion of secret: {name} canceled.", fg="green")
            return
    response = ipc_request(
        {
            "secret": "remove",
            "name": name,
        }
    )
    if response["result"] == "ok":
        click.secho(response["msg"], fg="green")
    else:
        click.secho(response["result"], fg="red")


@secret.command("value", short_help="Blocks the user")
@click.argument("name", type=str)
@click.argument("value", type=str, default=None, required=False)
def value(name: str, value: None | str = None):
    """
    NAME - secret name
    [VALUE] - secret value
    \f
    """
    request = {"secret": "value", "name": name}
    if value is not None:
        request["value"] = value

    response = ipc_request(request)

    if response["result"] == "ok":
        click.secho(response["msg"], fg="green", nl=False)
        click.secho(f": `{response['value']}`", fg="yellow")
    else:
        click.secho(response["result"], fg="red")


@secret.command("lock", short_help="Blocks the secret")
@click.argument("name", type=str)
def lock(name: str):
    """
    NAME - secret name
    \f
    """
    response = ipc_request({"secret": "lock", "name": name})
    if response["result"] == "ok":
        click.secho(response["msg"], fg="green")
    else:
        click.secho(response["result"], fg="red")


@secret.command("unlock", short_help="Unlocks the secret")
@click.argument("name", type=str)
def unlock(name: str):
    """
    NAME - secret name
    \f
    """
    response = ipc_request({"secret": "unlock", "name": name})
    if response["result"] == "ok":
        click.secho(response["msg"], fg="green")
    else:
        click.secho(response["result"], fg="red")


@secret.command("ls", short_help="Show a list of secrets")
def ls():
    """Show a list of secrets and their status."""

    response = ipc_request({"secret": "ls"})

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
            if line[2]:
                click.secho("| ro |", fg="green", nl=False)
            else:
                click.secho("|    |", fg="red", nl=False)
            click.echo(f" {line[3]}")
    else:
        click.secho(response["result"], fg="red")
