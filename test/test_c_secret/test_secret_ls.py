import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from ..conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_secret_ls(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    for num in range(2):
        await ipc_manager(
            db_store,
            {
                "secret": "edit",
                "name": f"secret_{num}",
                "value": f"value_{num}",
                "descr": f"descr_{num}",
                "readonly": False,
                "active": False,
                "create": True,
            },
        )
    for num in range(2, 4):
        await ipc_manager(
            db_store,
            {
                "secret": "edit",
                "name": f"secret_{num}",
                "value": f"value_{num}",
                "descr": f"descr_{num}",
                "readonly": True,
                "active": True,
                "create": True,
            },
        )

    response = await ipc_manager(db_store, {"secret": "ls"})
    assert response == {
        "result": "ok",
        "lines": [
            ("secret_2", 1, 1, "descr_2"),
            ("secret_3", 1, 1, "descr_3"),
            ("secret_0", 0, 0, "descr_0"),
            ("secret_1", 0, 0, "descr_1"),
        ],
    }

    await db_store.close()
