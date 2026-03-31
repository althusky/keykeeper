def test_ipc_edit(docker_container):
    res = docker_container.exec_run(
        'keykeeper secret edit my_secret "value" --readonly -ac',
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "Secret created:" in output
