import json
from pathlib import Path

import pytest

from ..conftest import DATABASE_KEY


@pytest.mark.docker
@pytest.mark.asyncio
async def test_backup(docker_container):
    res = docker_container.exec_run(
        f"keykeeper serverkey activate {DATABASE_KEY}", stream=True
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert output == "Db activated\n"

    res = docker_container.exec_run(
        ["sh", "-c", "cat /app/dump.json | keykeeper backup load"], stream=True
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "was restored from json" in output

    res = docker_container.exec_run("keykeeper backup dump", stream=True)
    output = "\n".join(map(lambda x: x.decode(), res.output))

    dump_path = Path.cwd() / "test" / "dump.json"
    with open(dump_path, "rt") as fo:
        test_dump = fo.read()

    assert json.loads(output) == json.loads(test_dump)
