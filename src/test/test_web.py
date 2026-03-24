import logging

import pytest

from keykeeper_protocol import keykeeper
from server_pack.users import key_gen

from .conftest import PORT


@pytest.mark.asyncio
async def test_get_secret(server_data, docker_container):

    with pytest.raises(ConnectionError) as exinfo:
        response = keykeeper(
            f"http://127.0.0.1:{PORT}", server_data, "web_secret_fake"
        )
    assert "unknown secret" in str(exinfo.value)

    with pytest.raises(ConnectionError) as exinfo:
        key = key_gen()
        response = keykeeper(f"http://127.0.0.1:{PORT}", key, "web_secret_1")
    assert "did not find the user" in str(exinfo.value)

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", server_data, "web_secret_1"
    )
    assert response == "value_1"


@pytest.mark.asyncio
async def test_post_secret(server_data, docker_container):

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", server_data, "web_secret_1"
    )
    assert response == "value_1"

    with pytest.raises(ConnectionError) as exinfo:
        response = keykeeper(
            f"http://127.0.0.1:{PORT}",
            server_data,
            "web_secret_1",
            "value_new",
        )
    assert "rewrite readonly secret" in str(exinfo.value)

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", server_data, "web_secret_3"
    )
    assert response == "value_3"

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", server_data, "web_secret_3", "value_new"
    )
    assert response == "value_new"

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", server_data, "web_secret_3"
    )
    assert response == "value_new"
