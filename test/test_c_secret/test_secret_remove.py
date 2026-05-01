import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from ..conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_secret_remove(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    await ipc_manager(
        db_store,
        {
            "user": "edit",
            "name": "user",
            "descr": "",
            "create": True,
            "active": True,
        },
    )
    await ipc_manager(
        db_store,
        {
            "secret": "edit",
            "name": "secret",
            "value": "password",
            "descr": "Description for secret",
            "active": True,
            "readonly": True,
            "create": True,
        },
    )

    response = await ipc_manager(
        db_store,
        {
            "user": "secret",
            "name": "user",
            "action": "add",
            "secret_name": "secret",
        },
    )

    response = await ipc_manager(
        db_store, {"secret": "remove", "name": "fake"}
    )
    assert response == {"result": "Unknown secret name: fake"}

    response = await ipc_manager(
        db_store, {"secret": "remove", "name": "secret"}
    )
    assert response == {"result": "ok", "msg": "Secret: secret deleted"}

    curs = await db_store.conn.execute("SELECT COUNT(*) FROM user_secret;")
    assert 0 == (await curs.fetchone())[0]
    await curs.close()

    curs = await db_store.conn.execute("SELECT COUNT(*) FROM secret;")
    assert 0 == (await curs.fetchone())[0]
    await curs.close()

    await db_store.close()
