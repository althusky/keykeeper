def test_ipc_edit(docker_container):
    res = docker_container.exec_run(
        'keykeeper user edit icp_user --descr="comment user" -ac',
        stream=True,
    )
    output = "\n".join(map(lambda x: x.decode(), res.output))
    assert "User created:" in output
