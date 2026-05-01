import pytest

from ..conftest import DATABASE_KEY


@pytest.mark.docker
def test_ipc_script(docker_container):

    res = docker_container.exec_run(
        f"keykeeper serverkey activate {DATABASE_KEY}", stream=True
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert output == "Db activated\n"

    # users
    res = docker_container.exec_run(
        'keykeeper user edit user_1 --descr="comment user 1" -ac',
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "User created:" in output

    res = docker_container.exec_run(
        'keykeeper user edit user_2 --descr="comment user 2" -ac',
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "User created:" in output

    # secrets
    res = docker_container.exec_run(
        'keykeeper secret edit secret_1 "value 1" --descr="Secret 1" --readonly -ac',
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "Secret created:" in output

    res = docker_container.exec_run(
        'keykeeper secret edit secret_2 "value 2" --descr="Secret 2" -ac',
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "Secret created:" in output

    res = docker_container.exec_run(
        'keykeeper secret edit secret_3 "value 3" --descr="Secret 3" -ac',
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "Secret created:" in output

    # add
    res = docker_container.exec_run(
        "keykeeper user secret user_1 add secret_1",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "Add secret: secret_1 to user: user_1" in output
    res = docker_container.exec_run(
        "keykeeper user secret user_1 add secret_2",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "Add secret: secret_2 to user: user_1" in output

    res = docker_container.exec_run(
        "keykeeper user secret user_2 add secret_1",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "Add secret: secret_1 to user: user_2" in output

    res = docker_container.exec_run(
        "keykeeper user secret user_2 add secret_3",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "Add secret: secret_3 to user: user_2" in output

    res = docker_container.exec_run(
        "keykeeper user secret user_2 add secret_3",
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "The user and secret are already linked" in output

    # ls
    res = docker_container.exec_run(
        "keykeeper user secret user_1 ls",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert output == (
        "secret_1 | active | ro | Secret 1\n"
        "secret_2 | active |    | Secret 2\n"
    )

    res = docker_container.exec_run(
        "keykeeper user secret user_2 ls",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert output == (
        "secret_1 | active | ro | Secret 1\n"
        "secret_3 | active |    | Secret 3\n"
    )

    # remove secret
    res = docker_container.exec_run(
        "keykeeper user secret user_1 remove secret_1",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "Delete secret: secret_1 from user: user_1" in output

    res = docker_container.exec_run(
        "keykeeper user secret user_1 remove secret_2",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "Delete secret: secret_2 from user: user_1" in output

    res = docker_container.exec_run(
        "keykeeper user secret user_1 ls",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "< empty >" in output
