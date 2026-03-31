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
        "secret": "edit",
        "name": "my_secret",
        "value": "my_value",
        "descr": "Description",
        "readonly": False,
        "active": True,
        "create": False,
    }
    response = await ipc_manager(db_store, request)
    assert response["result"] == "Couldn't find the secret to edit"

    # create user
    request = {
        "secret": "edit",
        "name": "my_secret",
        "value": "my_value",
        "descr": "Description",
        "active": True,
        "readonly": True,
        "create": True,
    }
    response = await ipc_manager(db_store, request)
    assert response["result"] == "ok"

    cur = await db_store.conn.execute(
        "SELECT value, descr, active, readonly "
        "FROM secret WHERE name = 'my_secret';"
    )
    row = await cur.fetchone()
    await cur.close()

    assert row[0] == "my_value"
    assert row[1] == "Description"
    assert row[2]
    assert row[3]

    # creae exist user
    request = {
        "secret": "edit",
        "name": "my_secret",
        "value": "my_value",
        "descr": "Description",
        "active": True,
        "readonly": True,
        "create": True,
    }
    response = await ipc_manager(db_store, request)
    assert "I can't create a secret:" in response["result"]

    # update user
    request = {
        "secret": "edit",
        "name": "my_secret",
        "value": "new_value",
        "descr": "New",
        "active": False,
        "readonly": False,
        "create": False,
    }
    response = await ipc_manager(db_store, request)
    assert response["result"] == "ok"

    cur = await db_store.conn.execute(
        "SELECT value, descr, active, readonly "
        "FROM secret WHERE name = 'my_secret';"
    )
    row = await cur.fetchone()
    await cur.close()

    assert row[0] == "new_value"
    assert row[1] == "New"
    assert not row[2]
    assert not row[3]

    await db_store.close()
