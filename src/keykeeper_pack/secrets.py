import click

from keykeeper_pack.common import ipc_request


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
