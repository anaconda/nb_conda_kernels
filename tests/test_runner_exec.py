import nb_conda_kernels.runner as runner


def test_exec_in_current_env_preserves_raw_argv(monkeypatch):
    prefix = "/synthetic env/prefix"
    command = (
        "/synthetic env/prefix/bin/python",
        "-c",
        "print('argument with spaces')",
    )
    calls = []

    monkeypatch.setattr(runner.sys, "platform", "linux")
    monkeypatch.setattr(runner.sys, "prefix", prefix)
    monkeypatch.setattr(
        runner.os,
        "execvp",
        lambda executable, args: calls.append((executable, args)),
    )

    runner.exec_in_env("/synthetic conda", prefix, *command)

    assert calls == [(command[0], list(command))]
