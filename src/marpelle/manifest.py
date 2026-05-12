from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .errors import ManifestError


@dataclass(slots=True)
class Manifest:
    name: str
    version: str
    socket: str
    commands: list[str]
    register: bool
    pid_file: str | None = None
    daemonize: bool = False
    working_directory: str | None = None
    umask: str | None = None
    user: str | None = None
    group: str | None = None


def _load_raw(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    else:
        raise ManifestError(f"unsupported manifest extension: {suffix}")
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be a mapping")
    return data


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"manifest field '{key}' must be a non-empty string")
    return value


def load_manifest(path: str | Path) -> Manifest:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise ManifestError(f"manifest not found: {manifest_path}")
    data = _load_raw(manifest_path)

    name = _require_str(data, "name")
    version = _require_str(data, "version")
    socket = _require_str(data, "socket")

    commands = data.get("commands")
    if not isinstance(commands, list) or not commands or not all(isinstance(c, str) and c for c in commands):
        raise ManifestError("manifest field 'commands' must be a non-empty list of strings")

    register = data.get("register")
    if not isinstance(register, bool):
        raise ManifestError("manifest field 'register' must be boolean")

    pid_file = data.get("pid_file")
    daemonize = data.get("daemonize", False)
    working_directory = data.get("working_directory")
    umask = data.get("umask")
    user = data.get("user")
    group = data.get("group")

    for key, value in {
        "pid_file": pid_file,
        "working_directory": working_directory,
        "umask": umask,
        "user": user,
        "group": group,
    }.items():
        if value is not None and not isinstance(value, str):
            raise ManifestError(f"manifest field '{key}' must be a string when provided")

    if not isinstance(daemonize, bool):
        raise ManifestError("manifest field 'daemonize' must be boolean")

    return Manifest(
        name=name,
        version=version,
        socket=socket,
        commands=commands,
        register=register,
        pid_file=pid_file,
        daemonize=daemonize,
        working_directory=working_directory,
        umask=umask,
        user=user,
        group=group,
    )


def discover_manifest(start: Path | None = None) -> Path:
    base = start or Path.cwd()
    for filename in ("MARPELLE.json", "MARPELLE.yaml", "MARPELLE.yml"):
        path = base / filename
        if path.exists():
            return path
    raise ManifestError(f"no MARPELLE manifest found in {base}")
