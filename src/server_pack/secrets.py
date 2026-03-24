from .db import DbStore


async def edit_secret(
    db_store: DbStore,
    name: str,
    value: str,
    descr: str,
    active: bool,
    readonly: bool,
    create: bool,
):
    """Create or update a secret record in the database.

    The function first checks whether a secret with the given name
    already exists. If `create` is `True`, it inserts a new record
    only when no matching secret is found. If `create` is `False`,
    it updates the existing record. The database transaction is
    committed after a successful insert or update.

    Args:
        db_store: Database store with an active connection.
        name: Secret name.
        value: Secret value.
        descr: Secret description.
        active: Secret active flag.
        readonly: Secret read-only flag.
        create: If `True`, create a new secret; otherwise update it.

    Returns:
        A dictionary with the operation result and a message.

    """

    cur = await db_store.conn.execute(
        "SELECT id FROM secret WHERE name = :name", {"name": name}
    )
    find_rows = await cur.fetchall()
    await cur.close()

    if not (find_rows or create):
        return {"result": "Couldn't find the secret to edit"}

    if find_rows and create:
        return {
            "result": f"I can't create a secret: {name} because it already exists."
        }

    if not find_rows and create:
        cur = await db_store.conn.execute(
            "INSERT INTO secret (name, value, descr, active, readonly) "
            "VALUES (:name, :value, :descr, :active, :readonly);",
            {
                "name": name,
                "value": value,
                "descr": descr,
                "active": active,
                "readonly": readonly,
            },
        )
        await cur.close()
        await db_store.commit()
        return {"msg": f"Secret created: {name}", "result": "ok"}

    if find_rows and not create:
        id = find_rows[0][0]
        cur = await db_store.conn.execute(
            "UPDATE secret "
            "SET value=:value, descr=:descr, active=:active, readonly=:readonly "
            "WHERE id=:id AND name=:name;",
            {
                "value": value,
                "descr": descr,
                "active": active,
                "readonly": readonly,
                "name": name,
                "id": id,
            },
        )
        await cur.close()
        await db_store.commit()
        return {"result": "ok", "msg": f"Secret: {name} record updated"}

    return {"result": "Unknown error"}
