from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PathConfig:
    runtime_dir: Path
    state_dir: Path

    @property
    def registry_path(self) -> Path:
        return self.state_dir / "registry.lmdb"


def default_paths() -> PathConfig:
    runtime_env = os.environ.get("MARPELLE_RUNTIME_DIR")
    state_env = os.environ.get("MARPELLE_STATE_DIR")

    if runtime_env:
        runtime_dir = Path(runtime_env)
    else:
        runtime_dir = Path("/run/marpelle") if os.geteuid() == 0 else Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "marpelle"

    if state_env:
        state_dir = Path(state_env)
    else:
        state_dir = Path("/var/lib/marpelle") if os.geteuid() == 0 else Path.home() / ".local" / "state" / "marpelle"

    return PathConfig(runtime_dir=runtime_dir, state_dir=state_dir)


def ensure_paths(config: PathConfig) -> None:
    try:
        config.runtime_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        config.runtime_dir = Path("/tmp/marpelle-runtime")
        config.runtime_dir.mkdir(parents=True, exist_ok=True)
    try:
        config.state_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        config.state_dir = Path("/tmp/marpelle-state")
        config.state_dir.mkdir(parents=True, exist_ok=True)
