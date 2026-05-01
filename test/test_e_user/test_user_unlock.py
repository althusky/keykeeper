import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from ..conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_user_unlock(tmp_path):

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

    response = await ipc_manager(db_store, {"user": "unlock", "name": "fake"})
    assert response == {"result": "Unknown user name: fake"}

    response = await ipc_manager(
        db_store, {"user": "unlock", "name": "active"}
    )
    assert response == {"result": "The user: active has already been activated"}

    response = await ipc_manager(db_store, {"user": "unlock", "name": "lock"})
    assert response == {
        "result": "ok",
        "msg": "User: lock has been activated.",
    }

    await db_store.close()
