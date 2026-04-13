import logging
import time

import pytest

from keykeeper.keykeeper_protocol import BaseProtocol
from keykeeper.server_pack import find_user, ipc_manager
from keykeeper.server_pack.db import DbStore

from .conftest import DATABASE_KEY

USER_COUNT = 500


@pytest.mark.skip(reason="Long test, use for performance testing only")
@pytest.mark.asyncio
async def test_performance_search(tmp_path):

    db_store = DbStore(tmp_path / "test.bin")
    await db_store.load(DATABASE_KEY)

    # add users for check search speed
    start = time.perf_counter()

    for i in range(USER_COUNT):
        request = {
            "user": "edit",
            "name": f"user_{i}",
            "descr": "Description",
            "active": True,
            "create": True,
        }
        _ = await ipc_manager(db_store, request)
    end = time.perf_counter()
    execution_time = end - start
    logging.info(
        f"First {USER_COUNT} users insertion takes {execution_time} seconds"
    )

    request = {
        "user": "edit",
        "name": f"user_{USER_COUNT + 1}",
        "descr": "Description",
        "active": True,
        "create": True,
    }
    start = time.perf_counter()
    response = await ipc_manager(db_store, request)
    end = time.perf_counter()
    execution_time = end - start
    logging.info(f"Time for insert {USER_COUNT + 1} user: {execution_time}")

    base_protocol = BaseProtocol(response["key"])
    msg_request = base_protocol.code_msg({"name": "secret_name"})

    start = time.perf_counter()
    name, quest, request = await find_user(db_store, msg_request)
    end = time.perf_counter()
    execution_time = end - start
    assert request == {"name": "secret_name"}
    logging.info(f"time to search for a user: {execution_time}")

    await db_store.close()
