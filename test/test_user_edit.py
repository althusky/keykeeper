import logging

import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from .conftest import DATABASE_KEY


@pytest.mark.asyncio
async def test_user_edit(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    # unknown user and not create
    request = {
        "user": "edit",
        "name": "my_user",
        "descr": "Description",
        "active": True,
        "create": False,
    }
    response = await ipc_manager(db_store, request)
    assert response["result"] == "Couldn't find the username to edit"

    # create user
    request = {
        "user": "edit",
        "name": "my_user",
        "descr": "Description",
        "active": True,
        "create": True,
    }
    response = await ipc_manager(db_store, request)
    assert response["result"] == "ok"
    assert "key" in response
    logging.debug(response["key"])

    cur = await db_store.conn.execute(
        "SELECT key, descr, active FROM user WHERE name = 'my_user';"
    )
    row = await cur.fetchone()
    await cur.close()

    assert row[0]
    assert row[1] == "Description"
    assert row[2]

    # creae exist user
    request = {
        "user": "edit",
        "name": "my_user",
        "descr": "Description",
        "active": True,
        "create": True,
    }
    response = await ipc_manager(db_store, request)
    assert "I can't create a user:" in response["result"]

    # update user
    request = {
        "user": "edit",
        "name": "my_user",
        "descr": "New",
        "active": False,
        "create": False,
    }
    response = await ipc_manager(db_store, request)
    assert response["result"] == "ok"

    cur = await db_store.conn.execute(
        "SELECT descr, active FROM user WHERE name = 'my_user';"
    )
    row = await cur.fetchone()
    await cur.close()

    assert row[0] == "New"
    assert not row[1]

    await db_store.close()
