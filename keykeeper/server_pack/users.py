import base64
from typing import Any

from Crypto.Random import get_random_bytes

from .db import DbStore


def key_gen() -> str:
    """
    Generate a base64-encoded secret key pair.
    The returned value contains a 16-byte AES key and a 16-byte HMAC
    key concatenated together and encoded as UTF-8 text.
    """
    aes_key = get_random_bytes(16)
    hmac_key = get_random_bytes(16)
    return base64.b64encode(aes_key + hmac_key).decode("utf-8")


async def edit_user(
    db_store: DbStore, name: str, descr: str, create: bool, active: bool
) -> dict[str, Any]:
    """Create or update a user record.

    The function looks up a user by name and then either creates a new
    record or updates the existing one, depending on the value of
    ``create``.

    Args:
        db_store: Database store
        name: User name to search for, create, or update.
        descr: User description to store in the database.
        create: If ``True``, create a new user when the name does not
            exist. If ``False``, update an existing user.
        active: Active status to store for the user.

    Returns:
        A dictionary with the operation result.
    """
    curs = await db_store.conn.execute(
        "SELECT id FROM user WHERE name = :name", {"name": name}
    )
    find_rows = await curs.fetchall()
    await curs.close()

    if not (find_rows or create):
        return {"result": "Couldn't find the username to edit"}

    if find_rows and create:
        return {
            "result": f"I can't create a user: {name} because it already exists."
        }

    if not find_rows and create:
        key = key_gen()
        curs = await db_store.conn.execute(
            "INSERT INTO user (name, key, descr, active) "
            "VALUES(:name, :key, :descr, :active);",
            {"name": name, "key": key, "descr": descr, "active": active},
        )
        await curs.close()
        await db_store.commit()
        return {"key": key, "msg": f"User created: {name}", "result": "ok"}

    if find_rows and not create:
        id = find_rows[0][0]
        curs = await db_store.conn.execute(
            "UPDATE user "
            "SET descr=:descr, active=:active "
            "WHERE id=:id AND name=:name;",
            {"descr": descr, "active": active, "name": name, "id": id},
        )
        await curs.close()
        await db_store.commit()
        return {"result": "ok", "msg": f"User: {name} record update"}

    return {"result": "Unknown error"}


async def secret_user(
    db_store: DbStore, name: str, action: str, secret_name: str
) -> dict[str, Any]:
    """Manage a user's secret links in the database.

    Args:
        db_store: Database store instance used to access the
            connection and commit changes.
        name: User name to search for.
        action: Operation to perform. Supported values are
            "ls" - list linked secret
            "add" - add link to the secret
            "remove" - remove link to the secret
        secret_name: Secret name

    Returns:
        A dictionary with the operation result.
    """

    curs = await db_store.conn.execute(
        "SELECT id FROM user WHERE name=:name;", {"name": name}
    )
    row_user_id = await curs.fetchone()
    await curs.close()
    if not row_user_id:
        return {"result": "Unknown user name"}
    # ls
    if action == "ls":
        curs = await db_store.conn.execute(
            "SELECT s.name, s.active, s.readonly, s.descr "
            "FROM secret as s, user_secret as us "
            "WHERE s.id = us.id_secret "
            "   AND us.id_user = :id_user;",
            {"id_user": row_user_id[0]},
        )
        rows = await curs.fetchall()
        await curs.close()
        return {"result": "ok", "lines": rows}

    curs = await db_store.conn.execute(
        "SELECT id FROM secret WHERE name=:name;", {"name": secret_name}
    )
    row_secret_id = await curs.fetchone()
    await curs.close()
    if not row_secret_id:
        return {"result": "Unknown secret name"}

    curs = await db_store.conn.execute(
        "SELECT COUNT(*) FROM user_secret "
        "WHERE id_user=:id_user AND id_secret=:id_secret",
        {"id_user": row_user_id[0], "id_secret": row_secret_id[0]},
    )
    keys_enable = (await curs.fetchone())[0]
    await curs.close()

    # add check unique
    if action == "add":
        if keys_enable:
            return {"result": "The user and secret are already linked"}
        curs = await db_store.conn.execute(
            "INSERT INTO user_secret "
            "(id_user, id_secret) VALUES (:id_user, :id_secret);",
            {"id_user": row_user_id[0], "id_secret": row_secret_id[0]},
        )
        await curs.close()
        await db_store.commit()
        return {
            "result": "ok",
            "msg": f"Add secret: {secret_name} to user: {name}",
        }

    # remove check exists
    if action == "remove":
        if not keys_enable:
            return {"result": "Can't find user-secret connection"}
        curs = await db_store.conn.execute(
            "DELETE FROM user_secret "
            "WHERE id_user = :id_user AND id_secret = :id_secret;",
            {"id_user": row_user_id[0], "id_secret": row_secret_id[0]},
        )
        await curs.close()
        await db_store.commit()
        return {
            "result": "ok",
            "msg": f"Delete secret: {secret_name} from user: {name}",
        }

    return {"result": "Unknown action"}


async def remove(db_store, name: str):
    """Remove a user and it relations to secrets from the database.

    Args:
        db_store: Database store object with an active connection.
        name: User name to remove.

    Returns:
        A dictionary with the operation result.
    """
    curs = await db_store.conn.execute(
        "SELECT id FROM user WHERE name = :name", {"name": name}
    )
    row_user = await curs.fetchone()
    await curs.close()

    if not row_user:
        return {"result": f"Unknown user name: {name}"}
    id_user = row_user[0]

    curs = await db_store.conn.execute(
        "DELETE FROM user_secret WHERE id_user = :id_user",
        {"id_user": id_user},
    )
    await curs.close()
    curs = await db_store.conn.execute(
        "DELETE FROM user WHERE id = :id_user", {"id_user": id_user}
    )
    await curs.close()
    await db_store.commit()

    return {"result": "ok", "msg": f"User: {name} deleted"}


async def lock(db_store: DbStore, name: str) -> dict[str, Any]:
    """Block a user account by name.

    Query the database for the user with the given name and, if the
    user exists and is active, mark the account as inactive.

    Args:
        db_store: Database store instance used to access the
            connection.
        name: User name to block.

    Returns:
        A dictionary with the operation result.
    """

    curs = await db_store.conn.execute(
        "SELECT active FROM user WHERE name = :name", {"name": name}
    )
    row_user = await curs.fetchone()
    await curs.close()

    if not row_user:
        return {"result": f"Unknown user name: {name}"}

    if not row_user[0]:
        return {"result": f"The user: {name} has already been locked"}

    curs = await db_store.conn.execute(
        "UPDATE user SET active = 0 WHERE name = :name", {"name": name}
    )
    await curs.close()
    await db_store.commit()

    return {"result": "ok", "msg": f"User: {name} has been blocked."}


async def unlock(db_store: DbStore, name: str) -> dict[str, Any]:
    """Unlock a user account by name.

    Query the database for the user with the given name and, if the
    user exists and is active, mark the account as inactive.

    Args:
        db_store: Database store instance used to access the
            connection.
        name: User name to unlock.

    Returns:
        A dictionary with the operation result.
    """

    curs = await db_store.conn.execute(
        "SELECT active FROM user WHERE name = :name", {"name": name}
    )
    row_user = await curs.fetchone()
    await curs.close()

    if not row_user:
        return {"result": f"Unknown user name: {name}"}

    if row_user[0]:
        return {"result": f"The user: {name} has already been activated"}

    curs = await db_store.conn.execute(
        "UPDATE user SET active = 1 WHERE name = :name", {"name": name}
    )
    await curs.close()
    await db_store.commit()

    return {"result": "ok", "msg": f"User: {name} has been activated."}


async def key(
    db_store: DbStore, name: str, change: bool = False
) -> dict[str, Any]:
    """Get or rotate a user's API key.
    Args:
        db_store: Database store used to access the user table.
        name: User name whose key should be retrieved or changed.
        change: If True, generate and store a new key for the user.
    Returns:
        A dictionary with the operation result.
    """
    curs = await db_store.conn.execute(
        "SELECT key FROM user WHERE name = :name", {"name": name}
    )
    row_user = await curs.fetchone()
    await curs.close()

    if not row_user:
        return {"result": f"Unknown user name: {name}"}

    if change:
        key = key_gen()
        curs = await db_store.conn.execute(
            "UPDATE user SET key = :key WHERE name = :name",
            {"key": key, "name": name},
        )
        await curs.close()
        await db_store.commit()
        return {"result": "ok", "key": key, "msg": "New key"}

    return {"result": "ok", "key": row_user[0], "msg": "Key"}


async def ls(db_store: DbStore) -> dict[str, Any]:
    """Return users ordered by active status and name.

    Args:
        db_store: Database store with an open connection.

    Returns:
        A dictionary with the operation result and rows with users.
    """
    curs = await db_store.conn.execute(
        "SELECT name, active, descr FROM user ORDER BY active DESC, name;"
    )
    rows = await curs.fetchall()
    await curs.close()
    return {"result": "ok", "lines": rows}
