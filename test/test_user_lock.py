import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from .conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_ls(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    await ipc_manager(
        db_store,
        {
            "user": "edit",
            "name": "active",
            "descr": "",
            "create": True,
            "active": True,
        },
    )
    await ipc_manager(
        db_store,
        {
            "user": "edit",
            "name": "lock",
            "descr": "",
            "create": True,
            "active": False,
        },
    )

    response = await ipc_manager(db_store, {"user": "lock", "name": "fake"})
    assert response == {"result": "Unknown user name: fake"}

    response = await ipc_manager(db_store, {"user": "lock", "name": "lock"})
    assert response == {"result": "The user: lock has already been locked"}

    response = await ipc_manager(db_store, {"user": "lock", "name": "active"})
    assert response == {"result": "ok", "msg": "User: active has been blocked."}

    await db_store.close()
