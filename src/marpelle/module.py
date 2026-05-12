from __future__ import annotations

from ctypes import CDLL
from pathlib import Path


class SharedLibraryHandle:
    """Thin wrapper around ctypes CDLL with path metadata."""

    def __init__(self, path: str | Path):
        lib_path = Path(path).expanduser()
        self.path = lib_path
        self._cdll = CDLL(str(lib_path))

    @property
    def cdll(self) -> CDLL:
        return self._cdll


def load_shared_library(path: str | Path) -> SharedLibraryHandle:
    return SharedLibraryHandle(path)
