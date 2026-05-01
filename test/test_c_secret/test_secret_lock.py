import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from ..conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_secret_lock(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    await ipc_manager(
        db_store,
        {
            "secret": "edit",
            "name": "active",
            "value": "active",
            "descr": "",
            "readonly": False,
            "create": True,
            "active": True,
        },
    )
    await ipc_manager(
        db_store,
        {
            "secret": "edit",
            "name": "lock",
            "value": "lock",
            "descr": "",
            "readonly": False,
            "create": True,
            "active": False,
        },
    )

    response = await ipc_manager(db_store, {"secret": "lock", "name": "fake"})
    assert response == {"result": "Unknown secret name: fake"}

    response = await ipc_manager(db_store, {"secret": "lock", "name": "lock"})
    assert response == {"result": "The secret: lock has already been locked"}

    response = await ipc_manager(db_store, {"secret": "lock", "name": "active"})
    assert response == {"result": "ok", "msg": "Secret: active has been locked."}

    await db_store.close()
