import asyncio
import base64
import logging
from pathlib import Path

import aiosqlite
from Crypto.Cipher import AES

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    key TEXT,
    descr TEXT,
    active INT CHECK (active IN (0,1))
);

CREATE TABLE IF NOT EXISTS secret (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    value TEXT,
    descr TEXT,
    active INT CHECK (active IN (0,1)),
    readonly INT CHECK (active IN (0,1))
);

CREATE TABLE IF NOT EXISTS user_secret(
    id_user INT,
    id_secret INT,
    PRIMARY KEY (id_user, id_secret),
    FOREIGN KEY (id_user) REFERENCES user(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_secret) REFERENCES secret(id) ON DELETE RESTRICT
)
"""

DEFAULT_FILE_PATH = Path("sqlite.bin")


class DbStore:
    """
    Async encrypted SQLite DB handler using AES CTR mode and file storage.
    """

    def __init__(self, file_path: Path = DEFAULT_FILE_PATH):
        """
        Initialize DbStore with optional file path for DB storage.

        Args:
            file_path (Path): Path to the database file. Defaults to
            DEFAULT_FILE_PATH.
        """
        self.file_path = file_path
        self.conn: aiosqlite.Connection

    async def load(self, key: str):
        """
        Load and decrypt DB from file into in-memory SQLite using base64 key.

        Args:
            key (str): Base64-encoded encryption key.

        Returns:
            None
        """
        self.conn = await aiosqlite.connect(":memory:")
        self.key = base64.b64decode(key)

        if not self.file_path.exists():
            cur = await self.conn.executescript(DB_SCHEMA)
            await cur.close()
            await self.commit()
            logging.debug("Create new database")
            return

        parts_line = self.file_path.stat().st_size - 8

        with open(self.file_path, "rb") as file_obj:
            load_dump = file_obj.read(parts_line)
            nonce = file_obj.read()
            cipher = AES.new(self.key, AES.MODE_CTR, nonce=nonce)
            dump_sql = cipher.decrypt(load_dump).decode("utf-8")

        await self.conn.executescript(dump_sql)
        logging.debug("Load database to memory")

    async def commit(self):
        """
        Commit in-memory DB changes and encrypt dump back to file.

        Returns:
            None
        """
        await self.conn.commit()

        dump = list()
        async for line in self.conn.iterdump():
            dump.append(line)

        cipher = AES.new(self.key, AES.MODE_CTR)
        dump_byte = ("\n".join(dump)).encode("utf-8")
        with open(self.file_path, "wb") as file_obj:
            cipher_dump = cipher.encrypt(dump_byte)
            file_obj.write(cipher_dump)
            file_obj.write(cipher.nonce)
        logging.debug("Commit and save database in file ")

    async def close(self):
        """
        Commit changes and close the DB connection asynchronously.

        Returns:
            None
        """
        await self.commit()
        await self.conn.close()
