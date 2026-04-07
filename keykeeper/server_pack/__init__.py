import logging
from typing import Any, Tuple

import keykeeper.server_pack.secrets as secrets
import keykeeper.server_pack.users as users
from keykeeper.keykeeper_protocol import BaseProtocol, ProtocolBrokenError

from .db import DbStore


async def ipc_manager(
    db_store: DbStore, request: dict[str, Any]
) -> dict[str, Any]:

    if "serverkey" in request and request["serverkey"] == "activate":
        if hasattr(db_store, "conn"):
            return {"result": "The database is already activated"}
        try:
            await db_store.load(request["key"])
        except:
            logging.exception("Can't activate db.")
            return {"result": "Error hapend ! Db not activated."}
        return {"msg": "Db activated", "result": "ok"}

    if not hasattr(db_store, "conn"):
        return {"result": "Db not connected"}

    match request:
        case {"user": value} if value == "edit":
            return await users.edit_user(
                db_store,
                request["name"],
                request["descr"],
                request["create"],
                request["active"],
            )
        case {"user": value} if value == "ls":
            return await users.ls(db_store)
        case {"user": value} if value == "secret":
            return await users.secret_user(
                db_store,
                request["name"],
                request["action"],
                request["secret_name"]
            )
        case {"secret": value} if value == "edit":
            return await secrets.edit_secret(
                db_store,
                request["name"],
                request["value"],
                request["descr"],
                request["active"],
                request["readonly"],
                request["create"],
            )
        case {"secret": value} if value == "ls":
            return await secrets.ls(db_store)

    return {"result": "Unknown command"}


async def find_user(
    db_store: DbStore, request: str
) -> Tuple[None | str, None | str, None | dict]:
    """
    Return:
        user_name, key, request_dict
    """

    cur = await db_store.conn.execute(
        "SELECT name, key FROM user WHERE active=1;"
    )
    for name_key in await cur.fetchall():
        try:
            protocol = BaseProtocol(name_key[1])
            request_dict = protocol.decode_msg(request)
        except ProtocolBrokenError:
            continue
        if "name" in request_dict:
            return (name_key[0], name_key[1], request_dict)

    return (None, None, None)
