
import pytest

from keykeeper.keykeeper_protocol import keykeeper
from keykeeper.server_pack.users import key_gen

from ..conftest import PORT, USER_2_KEY


@pytest.mark.docker
@pytest.mark.asyncio
async def test_get_secret(docker_container, prepare_data):

    with pytest.raises(ConnectionError) as exinfo:
        _ = keykeeper(
            f"http://127.0.0.1:{PORT}", USER_2_KEY, "web_secret_fake"
        )
    assert "unknown secret" in str(exinfo.value)

    with pytest.raises(ConnectionError) as exinfo:
        key = key_gen()
        _ = keykeeper(f"http://127.0.0.1:{PORT}", key, "web_secret_1")
    assert "did not find the user" in str(exinfo.value)

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", USER_2_KEY, "web_secret_1"
    )
    assert response == "value_1"


@pytest.mark.docker
@pytest.mark.asyncio
async def test_post_secret(docker_container, prepare_data):

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", USER_2_KEY, "web_secret_1"
    )
    assert response == "value_1"

    with pytest.raises(ConnectionError) as exinfo:
        _ = keykeeper(
            f"http://127.0.0.1:{PORT}",
            USER_2_KEY,
            "web_secret_1",
            "value_new",
        )
    assert "rewrite readonly secret" in str(exinfo.value)

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", USER_2_KEY, "web_secret_3"
    )
    assert response == "value_3"

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", USER_2_KEY, "web_secret_3", "value_new"
    )
    assert response == "value_new"

    response = keykeeper(
        f"http://127.0.0.1:{PORT}", USER_2_KEY, "web_secret_3"
    )
    assert response == "value_new"


@pytest.mark.docker
@pytest.mark.asyncio
async def test_lock_secret(docker_container, prepare_data):

    with pytest.raises(ConnectionError) as exinfo:
        _ = keykeeper(
            f"http://127.0.0.1:{PORT}",
            USER_2_KEY,
            "web_secret_4",
        )
    assert "unknown secret" in str(exinfo.value)
