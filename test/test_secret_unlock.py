import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from .conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_secert_unlock(tmp_path):

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

    response = await ipc_manager(
        db_store, {"secret": "unlock", "name": "fake"}
    )
    assert response == {"result": "Unknown secret name: fake"}

    response = await ipc_manager(
        db_store, {"secret": "unlock", "name": "active"}
    )
    assert response == {
        "result": "The secret: active has already been activated"
    }

    response = await ipc_manager(
        db_store, {"secret": "unlock", "name": "lock"}
    )
    assert response == {
        "result": "ok",
        "msg": "Secret: lock has been activated.",
    }

    await db_store.close()
