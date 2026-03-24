import pytest

from keykeeper_protocol import BaseProtocol
from server_pack import find_user, ipc_manager
from server_pack.db import DbStore

from .conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_icp_manager_base_msg(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")

    response = await ipc_manager(db_store, {"test": "fake"})
    assert response["result"] == "Db not connected"

    # after db load and up connection
    await db_store.load(DATABASE_KEY)

    response = await ipc_manager(db_store, {"test": "fake"})
    assert response["result"] == "Unknown command"

    await db_store.close()


@pytest.mark.asyncio
async def test_icp_manager_database_load(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")

    response = await ipc_manager(db_store, {"test": "fake"})
    assert response["result"] == "Db not connected"

    response = await ipc_manager(
        db_store, {"serverkey": "activate", "key": DATABASE_KEY}
    )

    assert response["result"] == "ok"
    assert hasattr(db_store, "conn")

    response = await ipc_manager(
        db_store, {"serverkey": "activate", "key": DATABASE_KEY}
    )
    assert response["result"] == "The database is already activated"

    await db_store.close()


@pytest.mark.asyncio
async def test_find_user(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    # create users
    request = {
        "user": "edit",
        "name": "my_user_1",
        "descr": "Description",
        "active": True,
        "create": True,
    }
    await ipc_manager(db_store, request)
    request = {
        "user": "edit",
        "name": "my_user_2",
        "descr": "Description",
        "active": True,
        "create": True,
    }
    await ipc_manager(db_store, request)
    request = {
        "user": "edit",
        "name": "my_user_3",
        "descr": "Description",
        "active": True,
        "create": True,
    }
    response = await ipc_manager(db_store, request)

    protocol = BaseProtocol(response["key"])
    request = protocol.code_msg({"name": "db_passwd"})

    user, key, request_dict = await find_user(db_store, request)

    assert user == "my_user_3"
    assert key == response["key"]
    assert request_dict == {"name": "db_passwd"}

    await db_store.close()
