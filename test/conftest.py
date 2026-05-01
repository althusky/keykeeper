import http.client
import io
import time
import logging
import tarfile
import time
from pathlib import Path

import docker
import pytest

DOCKER_IMAGE = "keykeeper_image_test"
DOCKER_CONTAINER = "keykeeper_container_test"

DATABASE_KEY = "4NHH7D3+0AoSPXb2I6byPg=="
USER_1_KEY = "4tXQmR1poRmJiiGZTVwBbeFy3vQ7gTiw967I4ixcJ6Y="
USER_2_KEY = "VbO3ekumi2oQpLIGi36wzmHLvy27gG6D+zBUoZJkHoE="


PATH = Path.cwd()

PORT = 7012

# logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("aiosqlite").setLevel(logging.WARNING)


@pytest.fixture(scope="module")
def docker_container():

    logging.info(f"Start build docker image: {DOCKER_IMAGE}")
    client = docker.from_env()

    try:
        container = client.containers.get(DOCKER_CONTAINER)
        container.stop()
        container.remove()
    except docker.errors.NotFound:
        pass

    client.images.prune()
    logging.info("Build container(long operation)")
    _, logs = client.images.build(path=str(PATH), tag=DOCKER_IMAGE)

    logging.debug("\n".join(map(str, logs)))
    logging.info(f"Start container {DOCKER_CONTAINER}")

    container = client.containers.run(
        DOCKER_IMAGE,
        name=DOCKER_CONTAINER,
        detach=True,
        ports={"7012/tcp": PORT},
        entrypoint=[
            "keykeeperd",
            "--host=0.0.0.0",
            "--port=7012",
            "--db_file=/data/sqlite.bin",
        ],
        environment=dict(),
    )

    logging.info("Server start")
    while True:
        time.sleep(0.5)
        try:
            conn = http.client.HTTPConnection("localhost", PORT, timeout=1)
            conn.request("GET", "/")
            resp = conn.getresponse()
            status = resp.status
            conn.close()
            # server support only POST but it show what server response
            if status == 405:
                break
        except (ConnectionResetError, ConnectionRefusedError):
            logging.warning("Waiting server ...")

    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w") as tar:
        tar.add("test/dump.json", arcname="dump.json")
    data.seek(0)

    container.put_archive(path="/app", data=data)

    yield container

    logging.info(f"Stop container {DOCKER_CONTAINER}")
    container.stop()
    container.remove()


@pytest.fixture(scope="module")
def prepare_data(docker_container):

    docker_container.exec_run(
        f"keykeeper serverkey activate {DATABASE_KEY}", stream=True
    )
    docker_container.exec_run(
        ["sh", "-c", "cat /app/dump.json | keykeeper backup load"], stream=True
    )

    step = 10
    output = ""

    # Waiting for asynchronous data loading
    while USER_2_KEY not in output and step:
        res = docker_container.exec_run(
            "keykeeper user key web_user_2", stream=True
        )
        output = "\n".join(map(lambda x: x.decode(), res.output))
        if USER_2_KEY in output:
            break
        time.sleep(0.01)
        step -= 1
        if not step:
            raise ConnectionError()


@pytest.fixture(scope="module")
def server_data(docker_container):

    # part of the keykeeper serverkey activate <key>
    docker_container.exec_run(
        f"keykeeper serverkey activate {DATABASE_KEY}", stream=True
    )

    # users
    response = docker_container.exec_run(
        "keykeeper user edit web_user_1 -ac",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), response.output))
    assert "User created:" in output

    response = docker_container.exec_run(
        "keykeeper user edit web_user_2 -ac",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), response.output))
    assert "User created:" in output

    user_key = output.split()[-1]

    # secrets
    response = docker_container.exec_run(
        "keykeeper secret edit web_secret_1 value_1 --readonly -ac",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), response.output))
    assert "Secret created:" in output
    response = docker_container.exec_run(
        "keykeeper user secret web_user_2 add web_secret_1",
        stream=True,
    )

    response = docker_container.exec_run(
        "keykeeper secret edit web_secret_2 value_2 --readonly -ac",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), response.output))
    response = docker_container.exec_run(
        "keykeeper user secret web_user_1 add web_secret_2",
        stream=True,
    )

    response = docker_container.exec_run(
        "keykeeper secret edit web_secret_3 value_3 --no-readonly -ac",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), response.output))
    response = docker_container.exec_run(
        "keykeeper user secret web_user_2 add web_secret_3",
        stream=True,
    )

    response = docker_container.exec_run(
        "keykeeper secret edit web_secret_4 value_4 --no-readonly -c",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), response.output))
    response = docker_container.exec_run(
        "keykeeper user secret web_user_2 add web_secret_4",
        stream=True,
    )

    yield user_key
