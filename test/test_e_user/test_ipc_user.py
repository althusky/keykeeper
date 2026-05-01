import pytest

from ..conftest import DATABASE_KEY


@pytest.mark.docker
def test_ipc_script(docker_container):

    res = docker_container.exec_run(
        f"keykeeper serverkey activate {DATABASE_KEY}", stream=True
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert output == "Db activated\n"

    # edit -c
    res = docker_container.exec_run(
        'keykeeper user edit user_1 --descr="comment user 1" -ac',
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "User created:" in output
    user_1_key = output.split()[-1]

    res = docker_container.exec_run(
        'keykeeper user edit user_2 --descr="comment user 2" -c',
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "User created:" in output
    user_2_key = output.split()[-1]

    # check over ls
    res = docker_container.exec_run(
        "keykeeper user ls",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert output == (
        "user_1 | active | comment user 1\n"
        "user_2 | lock   | comment user 2\n"
    )

    # edit descript
    res = docker_container.exec_run(
        'keykeeper user edit user_1 --descr="comment user new" -a',
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "User: user_1 record update" in output

    # lock unlock
    res = docker_container.exec_run(
        "keykeeper user unlock user_1",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "user_1 has already been activated" in output

    res = docker_container.exec_run(
        "keykeeper user lock user_1",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "user_1 has been blocked" in output

    res = docker_container.exec_run(
        "keykeeper user unlock user_2",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "user_2 has been activated" in output

    # check over ls
    res = docker_container.exec_run(
        "keykeeper user ls",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert output == (
        "user_2 | active | comment user 2\n"
        "user_1 | lock   | comment user new\n"
    )

    # key get set get
    res = docker_container.exec_run(
        "keykeeper user key user_1",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert user_1_key in output

    res = docker_container.exec_run(
        "keykeeper user key user_2",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert user_2_key in output

    res = docker_container.exec_run(
        "keykeeper user key user_2 --change",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "New key :" in output

    # remove
    res = docker_container.exec_run(
        "keykeeper user remove user_1 --yes",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "User: user_1 deleted" in output
    res = docker_container.exec_run(
        "keykeeper user remove user_2 --yes",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "User: user_2 deleted" in output

    # check ls
    res = docker_container.exec_run(
        "keykeeper user ls",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "< empty >" in output
