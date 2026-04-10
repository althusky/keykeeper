import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from .conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_secret_value(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    await ipc_manager(
        db_store,
        {
            "secret": "edit",
            "name": "test",
            "value": "old_value",
            "descr": "",
            "readonly": False,
            "create": True,
            "active": True,
        },
    )

    response = await ipc_manager(db_store, {"secret": "value", "name": "fake"})
    assert response == {"result": "Unknown secret name: fake"}

    response = await ipc_manager(db_store, {"secret": "value", "name": "test"})
    assert response == {
        "result": "ok",
        "msg": "Get secret value",
        "value": "old_value",
    }

    response = await ipc_manager(
        db_store, {"secret": "value", "name": "test", "value": "new_value"}
    )
    assert response == {
        "result": "ok",
        "msg": "Set secret value",
        "value": "new_value",
    }

    curs = await db_store.conn.execute(
        "SELECT value FROM secret WHERE name='test'"
    )
    assert "new_value" == (await curs.fetchone())[0]

    await db_store.close()
