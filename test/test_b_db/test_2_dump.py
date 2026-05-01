import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from ..conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_dump(tmp_path):

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

    response = await ipc_manager(db_store, {"backup": "dump"})

    db_new = DbStore(tmp_path / "test_new.bin")
    await db_new.load(DATABASE_KEY)

    response_new = await ipc_manager(
        db_new, {"backup": "load", "dump": response["dump"]}
    )

    response_new = await ipc_manager(db_new, {"backup": "dump"})

    assert response == response_new

    await db_store.close()
    await db_new.close()
