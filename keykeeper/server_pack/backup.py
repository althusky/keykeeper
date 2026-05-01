from dataclasses import asdict, dataclass
from typing import Any

from .db import DbStore


@dataclass
class User:
    id: int
    name: str
    key: str
    descr: str
    active: int


@dataclass
class Secret:
    id: int
    name: str
    value: str
    descr: str
    active: int
    readonly: int


@dataclass
class UserSecret:
    id_user: int
    id_secret: int


async def dump(db_store: DbStore) -> dict:
    dump = dict()

    curs = await db_store.conn.execute(
        "SELECT id, name, key, descr, active FROM user ORDER BY id;"
    )
    dump["user"] = list(map(lambda x: asdict(User(*x)), await curs.fetchall()))
    await curs.close()

    curs = await db_store.conn.execute(
        "SELECT id, name, value, descr, active, readonly FROM secret "
        "ORDER BY id;"
    )
    dump["secret"] = list(
        map(lambda x: asdict(Secret(*x)), await curs.fetchall())
    )
    await curs.close()

    curs = await db_store.conn.execute(
        "SELECT id_user, id_secret FROM user_secret "
        "ORDER BY id_user, id_secret;"
    )
    dump["user_secret"] = list(
        map(lambda x: asdict(UserSecret(*x)), await curs.fetchall())
    )
    await curs.close()

    return {"result": "ok", "dump": dump}


async def load(db_store: DbStore, dump: dict) -> dict[str, Any]:

    curs = await db_store.conn.execute("SELECT COUNT(*) FROM user;")
    user_count = (await curs.fetchone())[0]
    await curs.close()
    if user_count:
        return {
            "result": "Unable to restore from backup; table 'user' is not empty."
        }

    curs = await db_store.conn.execute("SELECT COUNT(*) FROM secret;")
    secret_count = (await curs.fetchone())[0]
    await curs.close()
    if secret_count:
        return {
            "result": "Unable to restore from backup; table 'secret' is not empty."
        }

    curs = await db_store.conn.execute("SELECT COUNT(*) FROM user_secret;")
    user_secret_count = (await curs.fetchone())[0]
    await curs.close()
    if user_secret_count:
        return {
            "result": "Unable to restore from backup; table 'user_secret' is not empty."
        }

    # upload
    curs = await db_store.conn.executemany(
        "INSERT INTO user (id, name, key, descr, active) "
        "VALUES (:id, :name, :key, :descr, :active)",
        dump["user"],
    )
    curs = await db_store.conn.executemany(
        "INSERT INTO secret (id, name, value, descr, active, readonly) "
        "VALUES (:id, :name, :value, :descr, :active,  :readonly)",
        dump["secret"],
    )
    curs = await db_store.conn.executemany(
        "INSERT INTO user_secret (id_user, id_secret) "
        "VALUES (:id_user, :id_secret)",
        dump["user_secret"],
    )

    return {"result": "ok", "msg": "The database was restored from json data."}
