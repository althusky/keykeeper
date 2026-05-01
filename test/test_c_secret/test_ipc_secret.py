import pytest

from ..conftest import DATABASE_KEY


@pytest.mark.docker
def test_ipc_script(docker_container):

    res = docker_container.exec_run(
        f"keykeeper serverkey activate {DATABASE_KEY}", stream=True
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert output == "Db activated\n"

    # edit -c
    res = docker_container.exec_run(
        'keykeeper secret edit secret_1 "value 1" --descr="Secret 1 description" --readonly -a -c',
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "Secret created:" in output

    res = docker_container.exec_run(
        'keykeeper secret edit secret_2 "value 2" --descr="Secret 2 description" -c',
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "Secret created:" in output

    # ls
    res = docker_container.exec_run(
        "keykeeper secret ls",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))

    assert output == (
        "secret_1 | active | ro | Secret 1 description\n"
        "secret_2 | lock   |    | Secret 2 description\n"
    )

    # value, value [set]
    res = docker_container.exec_run(
        "keykeeper secret value secret_1",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "value 1" in output

    res = docker_container.exec_run(
        'keykeeper secret value secret_1 "value new for test"',
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "Set secret value:"
    assert "value new for test" in output

    # lock unlock
    res = docker_container.exec_run(
        "keykeeper secret lock secret_1",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "has been locked" in output

    res = docker_container.exec_run(
        "keykeeper secret unlock secret_2",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "secret_2 has been activated." in output

    # ls
    res = docker_container.exec_run(
        "keykeeper secret ls",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert output == (
        "secret_2 | active |    | Secret 2 description\n"
        "secret_1 | lock   | ro | Secret 1 description\n"
    )

    # remove
    res = docker_container.exec_run(
        "keykeeper secret remove secret_1 --yes",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "secret_1 deleted" in output
    res = docker_container.exec_run(
        "keykeeper secret remove secret_2 --yes",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "secret_2 deleted" in output

    res = docker_container.exec_run(
        "keykeeper secret ls",
        stream=True,
    )
    output = "".join(map(lambda x: x.decode(), res.output))
    assert "< empty >" in output
