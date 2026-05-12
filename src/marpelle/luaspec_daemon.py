from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ManifestError


@dataclass(slots=True)
class DaemonLuaSpec:
    daemonize: bool = False
    working_directory: str | None = None
    umask: int | None = None
    pid_file: str | None = None
    ipc_backend: str | None = None
    socket: str | None = None


def _to_int_umask(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip().lower()
        base = 8 if stripped.startswith("0") else 10
        try:
            return int(stripped, base)
        except ValueError as exc:
            raise ManifestError(f"invalid DAEMON.lua umask value: {value}") from exc
    raise ManifestError("DAEMON.lua field 'umask' must be string or integer")


def _table_get(lua_table: Any, key: str) -> Any:
    try:
        return lua_table[key]
    except Exception:
        return None


def load_daemon_lua(path: str | Path) -> DaemonLuaSpec:
    lua_path = Path(path)
    if not lua_path.exists():
        raise ManifestError(f"DAEMON.lua not found: {lua_path}")

    try:
        from lupa import LuaRuntime
    except Exception as exc:  # pragma: no cover
        raise ManifestError("lupa is required to parse DAEMON.lua") from exc
    runtime = LuaRuntime(unpack_returned_tuples=True)
    with lua_path.open("r", encoding="utf-8") as f:
        script = f.read()

    runtime_globals = runtime.globals()
    runtime_globals.print = lambda *args: None
    runtime_globals.os = {"getenv": lambda key: None}
    runtime_globals.io = {}

    table = runtime.execute(script)
    if table is None:
        table = runtime_globals.DAEMON
    if table is None:
        raise ManifestError("DAEMON.lua must return a table or define global DAEMON")

    spec = DaemonLuaSpec(
        daemonize=bool(_table_get(table, "daemonize") or False),
        working_directory=_table_get(table, "working_directory"),
        umask=_to_int_umask(_table_get(table, "umask")),
        pid_file=_table_get(table, "pid_file"),
        ipc_backend=_table_get(table, "ipc_backend"),
        socket=_table_get(table, "socket"),
    )

    if spec.working_directory is not None and not isinstance(spec.working_directory, str):
        raise ManifestError("DAEMON.lua field 'working_directory' must be a string")
    if spec.pid_file is not None and not isinstance(spec.pid_file, str):
        raise ManifestError("DAEMON.lua field 'pid_file' must be a string")
    if spec.ipc_backend is not None and not isinstance(spec.ipc_backend, str):
        raise ManifestError("DAEMON.lua field 'ipc_backend' must be a string")
    if spec.socket is not None and not isinstance(spec.socket, str):
        raise ManifestError("DAEMON.lua field 'socket' must be a string")

    return spec
