import asyncio
import json
import logging
import os
from functools import partial
from pathlib import Path

import aiohttp
import click
from aiohttp import web

from keykeeper.keykeeper_protocol import BaseProtocol
from keykeeper.server_pack import find_user, ipc_manager
from keykeeper.server_pack.db import DbStore

SOCKET_PATH = "/tmp/keykeeper.sock"
ACCESS_LOG = None

log_level = os.environ.get("LOGLEVEL", "INFO")
logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)-8s| %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def handler_ipc(reader, writer, db_store):
    """Handle IPC requests over a Unix socket asynchronously.
    Reads data from reader until a complete JSON request is received,
    processes it via ipc_manager with the database store, and sends back
    the JSON-encoded response through writer. Closes the connection after.

    Args:
        reader (asyncio.StreamReader): Stream reader for incoming data.
        writer (asyncio.StreamWriter): Stream writer for sending response.
        db_store (DbStore): Database store instance for request processing.
    """
    try:
        buffer = b""
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break
            buffer += chunk
            try:
                request = json.loads(buffer.decode())
                break
            except json.JSONDecodeError:
                continue

        response = await ipc_manager(db_store, request)

        writer.write(json.dumps(response).encode())
        await writer.drain()

    finally:
        writer.close()
        await writer.wait_closed()


async def post_secret(request):
    """Handle POST request to get or update a secret for an authenticated user.
    Reads request data, authenticates user, validates request keys, fetches
    secret from database, optionally updates secret value if not readonly, and
    returns the secret value encoded with the user's protocol key.

    Args:
        request (aiohttp.web.Request): Incoming HTTP request with JSON body.

    Raises:
        aiohttp.web.HTTPServerError: If database connection is not available.
        aiohttp.web.HTTPUnauthorized: If user authentication fails.
        aiohttp.web.HTTPBadRequest: If required keys are missing or unexpected keys present.
        aiohttp.web.HTTPNotFound: If requested secret is not found.
        aiohttp.web.HTTPUnprocessableEntity: If attempting to update a readonly secret.

    Returns:
        aiohttp.web.Response: HTTP response containing the secret value encoded by protocol.
    """
    request_byte = await request.read()
    db_store = request.app["db_store"]
    if not hasattr(db_store, "conn"):
        raise aiohttp.web.HTTPServerError()

    # find user
    user_name, key, request = await find_user(
        db_store, request_byte.decode("utf-8")
    )
    if user_name is None:
        raise aiohttp.web.HTTPUnauthorized()

    keys = set(request.keys())
    allowed = {"name", "value"}
    if not {"name"}.issubset(keys):
        raise aiohttp.web.HTTPBadRequest(reason="Missing 'name' in request")
    if not keys.issubset(allowed):
        raise aiohttp.web.HTTPBadRequest(reason="Unexpected keys in request")

    curs = await db_store.conn.execute(
        "SELECT s.value, s.readonly "
        "FROM user AS u, secret AS s, user_secret AS us "
        "WHERE u.id = us.id_user "
        "   AND s.id = us.id_secret "
        "   AND u.name = :user_name "
        "   AND s.name = :secret_name;",
        {"user_name": user_name, "secret_name": request["name"]},
    )
    secret_row = await curs.fetchone()

    await curs.close()
    if not secret_row:
        raise aiohttp.web.HTTPNotFound()

    response_value = secret_row[0]

    if "value" in request:
        # check readonly
        if secret_row[1]:
            raise aiohttp.web.HTTPUnprocessableEntity()
        curs = await db_store.conn.execute(
            "UPDATE secret " "SET value = :value " "WHERE name = :name;",
            {"value": request["value"], "name": request["name"]},
        )
        await curs.close()
        await db_store.commit()
        response_value = request["value"]

    protocol = BaseProtocol(key)
    return aiohttp.web.Response(
        body=protocol.code_msg({"value": response_value})
    )


async def server_init(db_file, db_key, app: web.Application):
    """Initialize server, database connection, and IPC Unix socket.

    Args:
        db_file (str): Path to the database file.
        db_key (str or None): Encryption key to load the database.
        app (aiohttp.web.Application): The aiohttp application instance.
    """
    logging.info("Server start")
    app["db_store"] = DbStore(Path(db_file))

    # The database can be loaded immediately with the --db_key parameter or
    # initiated later via $ keykeeper serverkey activate
    if db_key is not None:
        await app["db_store"].load(db_key)
        logging.info("Server start, database ready")
    else:
        logging.warning("Server start, but database not connected")

    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    handler_ipc_db = partial(handler_ipc, db_store=app["db_store"])
    ipc_server = await asyncio.start_unix_server(
        handler_ipc_db, path=SOCKET_PATH
    )
    os.chmod(SOCKET_PATH, 0o600)

    ipc_task = asyncio.create_task(ipc_server.serve_forever())
    try:
        yield
    finally:
        ipc_task.cancel()
        ipc_server.close()
        await ipc_server.wait_closed()
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
        logging.info("Server stop")

    if hasattr(app["db_store"], "conn"):
        await app["db_store"].close()


def make_app(db_file: str, db_key: str):
    """Create and configure aiohttp web application.

    Args:
        db_file (str): Path to the database file.
        db_key (str): Key used for database access.

    Returns:
        aiohttp.web.Application: Configured aiohttp application instance.
    """
    app = web.Application()
    app.add_routes([aiohttp.web.post("/", post_secret)])
    app.cleanup_ctx.append(partial(server_init, db_file, db_key))
    return app


@click.command()
@click.option(
    "-h",
    "--host",
    type=str,
    default="0.0.0.0",
    show_default=True,
    help="Interface on which the service will run",
)
@click.option(
    "-p",
    "--port",
    type=int,
    show_default=True,
    default=7012,
    help="Port on which the service will run (default: 7001).",
)
@click.option(
    "--db_file",
    type=str,
    show_default=True,
    default="sqlite.bin",
    help="Database filename or file name with path.",
)
@click.option(
    "--db_key",
    type=str,
    show_default=True,
    default=None,
    help="Encryption key for database dump",
)
def main(host: str, port: int, db_file: str, db_key: str):
    """
    Run the KeyKeeper service with specified host, port, database file and key.
    \f
    Args:
        host (str): Network interface to bind the service to.
        port (int): Port number to run the service on.
        db_file (str): Path to the database file.
        db_key (str): Encryption key for the database dump.
    """
    app = make_app(db_file, db_key)
    web.run_app(app, host=host, port=port, access_log=ACCESS_LOG)


if __name__ == "__main__":
    main()
