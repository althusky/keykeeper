import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from ..conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_ls(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    for num in range(2):
        await ipc_manager(
            db_store,
            {
                "user": "edit",
                "name": f"user_{num}",
                "descr": f"descr_{num}",
                "create": True,
                "active": False,
            },
        )
    for num in range(2, 4):
        await ipc_manager(
            db_store,
            {
                "user": "edit",
                "name": f"user_{num}",
                "descr": f"descr_{num}",
                "create": True,
                "active": True,
            },
        )

    response = await ipc_manager(db_store, {"user": "ls"})
    assert response == {
        "result": "ok",
        "lines": [
            ("user_2", 1, "descr_2"),
            ("user_3", 1, "descr_3"),
            ("user_0", 0, "descr_0"),
            ("user_1", 0, "descr_1"),
        ],
    }

    await db_store.close()
