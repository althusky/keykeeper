import pytest

from keykeeper.server_pack import ipc_manager
from keykeeper.server_pack.db import DbStore

from .conftest import DATABASE_KEY


@pytest.fixture(scope="function")
async def prepare_db(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    # users
    for num in range(2):
        await ipc_manager(
            db_store,
            {
                "user": "edit",
                "name": f"user_{num}",
                "descr": "",
                "create": True,
                "active": True,
            },
        )
    # secrets
    for num in range(4):
        await ipc_manager(
            db_store,
            {
                "secret": "edit",
                "name": f"secret_{num}",
                "value": str(num),
                "descr": f"Description for {num}",
                "active": True,
                "readonly": True,
                "create": True,
            },
        )

    try:
        yield db_store
    finally:
        await db_store.close()


@pytest.mark.asyncio
async def test_add(prepare_db):

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_fake",
            "action": "add",
            "secret_name": "secret_1",
        },
    )
    assert response["result"] == "Unknown user name"

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "add",
            "secret_name": "secret_fake",
        },
    )
    assert response["result"] == "Unknown secret name"

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "add",
            "secret_name": "secret_1",
        },
    )
    assert response["result"] == "ok"

    curs = await prepare_db.conn.execute(
        "SELECT us.id_user, us.id_secret "
        "FROM user AS u, secret AS s, user_secret AS us "
        "WHERE u.id = us.id_user "
        "   AND s.id = us.id_secret "
        "   AND u.name = 'user_1' "
        "   AND s.name = 'secret_1';"
    )
    rows = await curs.fetchall()
    await curs.close()
    assert rows[0] == (2, 2)

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "add",
            "secret_name": "secret_1",
        },
    )
    assert response["result"] == "User secret already connected"


@pytest.mark.asyncio
async def test_list(prepare_db):

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "add",
            "secret_name": "secret_0",
        },
    )
    assert response["result"] == "ok"

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "add",
            "secret_name": "secret_1",
        },
    )
    assert response["result"] == "ok"

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "ls",
            "secret_name": None,
        },
    )
    assert response == {
        "result": "ok",
        "lines": [
            ("secret_0", 1, 1, "Description for 0"),
            ("secret_1", 1, 1, "Description for 1"),
        ],
    }


@pytest.mark.asyncio
async def test_remove(prepare_db):

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "add",
            "secret_name": "secret_0",
        },
    )
    assert response["result"] == "ok"

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "add",
            "secret_name": "secret_1",
        },
    )
    assert response["result"] == "ok"

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "remove",
            "secret_name": "secret_0",
        },
    )
    assert response["result"] == "ok"

    response = await ipc_manager(
        prepare_db,
        {
            "user": "secret",
            "name": "user_1",
            "action": "remove",
            "secret_name": "secret_0",
        },
    )
    assert response["result"] == "Can't find user-secret connection"
