from pathlib import Path
import sys

import pytest

from marpelle.manifest import load_manifest
from marpelle.runtime import ServiceRuntime


def test_runtime_applies_daemon_lua_overrides(tmp_path: Path):
    pytest.importorskip("lupa")
    hooks_path = tmp_path / "marpelle_hooks.py"
    hooks_path.write_text("HOOKS = {'ping': lambda payload: payload}\n", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    manifest_path = tmp_path / "MARPELLE.json"
    manifest_path.write_text(
        '{"name":"svc","version":"1","socket":"/tmp/old.sock","commands":["ping"],"register":false,"daemon_lua_file":"DAEMON.lua"}',
        encoding="utf-8",
    )
    daemon_lua = tmp_path / "DAEMON.lua"
    daemon_lua.write_text("return { socket = '/tmp/new.sock', daemonize = false }\n", encoding="utf-8")

    try:
        runtime = ServiceRuntime(load_manifest(manifest_path), hooks_module="marpelle_hooks")
        runtime.apply_daemon_lua(str(daemon_lua))
        assert runtime.manifest.socket == "/tmp/new.sock"
    finally:
        sys.path.remove(str(tmp_path))
