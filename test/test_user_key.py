import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from .conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_ls(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    response = await ipc_manager(
        db_store,
        {
            "user": "edit",
            "name": "active",
            "descr": "",
            "create": True,
            "active": True,
        },
    )

    key = response["key"]

    response = await ipc_manager(db_store, {"user": "lock", "name": "fake"})
    assert response == {"result": "Unknown user name: fake"}

    response = await ipc_manager(
        db_store, {"user": "key", "name": "active", "change": False}
    )
    assert response == {"result": "ok", "key": key, "msg": "Key"}

    response = await ipc_manager(
        db_store, {"user": "key", "name": "active", "change": True}
    )
    curs = await db_store.conn.execute(
        "SELECT key FROM user WHERE name = 'active';"
    )
    row = await curs.fetchone()
    await curs.close()

    assert response["key"] == row[0]

    await db_store.close()
