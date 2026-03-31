import logging

import pytest

from keykeeper.server_pack.db import DbStore

DB_FILE_NAME = "test.bin"
KEY = "EVSCx9fyxfL+PD4K+nbN9g=="


@pytest.mark.asyncio
async def test_new(tmp_path):

    db_store = DbStore(tmp_path / DB_FILE_NAME)
    await db_store.load(KEY)

    curs = await db_store.conn.execute(
        "SELECT COUNT(*) "
        "FROM sqlite_master "
        "WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%';"
    )
    table_count = (await curs.fetchone())[0]
    logging.debug(f"New db, table count {table_count}")
    assert table_count != 0

    await db_store.close()


@pytest.mark.asyncio
async def test_save_load(tmp_path):
    bin_path = tmp_path / DB_FILE_NAME
    db_store = DbStore(bin_path)
    await db_store.load(KEY)

    db_bin_size = bin_path.stat().st_size

    # append table and test row
    await db_store.conn.execute(
        "CREATE TABLE IF NOT EXISTS test_table( "
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT );"
    )
    curs = await db_store.conn.execute(
        "INSERT INTO test_table (name)" "VALUES ('new name');"
    )
    await db_store.conn.commit()
    assert curs.rowcount == 1

    await db_store.close()
    logging.debug("CLOSE DB ")

    assert db_bin_size < bin_path.stat().st_size

    # reopen and check data

    db_new_store = DbStore(bin_path)
    await db_new_store.load(KEY)
    logging.debug("LOAD DB ")

    curs = await db_new_store.conn.execute(
        "SELECT id, name FROM test_table WHERE name = 'new name';"
    )
    rows = await curs.fetchall()
    assert len(rows) == 1

    logging.debug(f"Check row after reload {rows[0]}")
    assert rows[0][0] == 1
    assert rows[0][1] == 'new name'

    await db_new_store.close()
