from .conftest import DATABASE_KEY


def test_ipc_key_pass(docker_container):
    res = docker_container.exec_run(
        f"python3 keykeeper.py serverkey activate {DATABASE_KEY}", stream=True
    )
    output = ("\n".join(map(lambda x: x.decode(), res.output)))
    assert "The database is already activated" in output
