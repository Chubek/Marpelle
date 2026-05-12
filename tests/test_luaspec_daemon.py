from pathlib import Path

import pytest

from marpelle.luaspec_daemon import load_daemon_lua


def test_load_daemon_lua_return_table(tmp_path: Path):
    pytest.importorskip("lupa")
    path = tmp_path / "DAEMON.lua"
    path.write_text(
        "return { daemonize = true, working_directory = '/tmp', umask = '022', pid_file = '/tmp/svc.pid', ipc_backend = 'unix', socket = '/tmp/svc.sock' }\n",
        encoding="utf-8",
    )
    spec = load_daemon_lua(path)
    assert spec.daemonize is True
    assert spec.working_directory == "/tmp"
    assert spec.umask == 0o22
    assert spec.pid_file == "/tmp/svc.pid"
    assert spec.socket == "/tmp/svc.sock"
