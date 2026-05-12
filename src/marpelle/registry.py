from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import asdict, dataclass

try:
    import lmdb  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal environments
    lmdb = None

from .errors import RegistryError
from .paths import PathConfig, ensure_paths


@dataclass(slots=True)
class ServiceRecord:
    name: str
    pid: int
    socket: str
    version: str
    started_at: int
    updated_at: int
    state: str


class Registry:
    def __init__(self, paths: PathConfig):
        self.paths = paths
        ensure_paths(paths)
        self._use_lmdb = lmdb is not None
        if self._use_lmdb:
            self._env = lmdb.open(str(paths.registry_path), map_size=10 * 1024 * 1024, max_dbs=1)
            self._db = None
        else:
            self._env = None
            self._db = sqlite3.connect(paths.state_dir / "registry.sqlite3")
            self._db.execute("CREATE TABLE IF NOT EXISTS services (name TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self._db.commit()

    def close(self) -> None:
        if self._env is not None:
            self._env.close()
        if self._db is not None:
            self._db.close()

    def register(self, record: ServiceRecord) -> None:
        if self._env is not None:
            key = f"service:{record.name}".encode()
            with self._env.begin(write=True) as txn:
                txn.put(key, json.dumps(asdict(record)).encode())
        else:
            assert self._db is not None
            self._db.execute(
                "INSERT OR REPLACE INTO services(name, value) VALUES (?, ?)",
                (record.name, json.dumps(asdict(record))),
            )
            self._db.commit()

    def unregister(self, name: str) -> None:
        if self._env is not None:
            key = f"service:{name}".encode()
            with self._env.begin(write=True) as txn:
                txn.delete(key)
        else:
            assert self._db is not None
            self._db.execute("DELETE FROM services WHERE name = ?", (name,))
            self._db.commit()

    def get(self, name: str) -> ServiceRecord | None:
        if self._env is not None:
            key = f"service:{name}".encode()
            with self._env.begin() as txn:
                raw = txn.get(key)
            if raw is None:
                return None
            return ServiceRecord(**json.loads(raw.decode()))
        assert self._db is not None
        row = self._db.execute("SELECT value FROM services WHERE name = ?", (name,)).fetchone()
        if row is None:
            return None
        return ServiceRecord(**json.loads(row[0]))

    def list(self) -> list[ServiceRecord]:
        records: list[ServiceRecord] = []
        if self._env is not None:
            with self._env.begin() as txn:
                for key, value in txn.cursor():
                    if key.startswith(b"service:"):
                        records.append(ServiceRecord(**json.loads(value.decode())))
        else:
            assert self._db is not None
            for (value,) in self._db.execute("SELECT value FROM services"):
                records.append(ServiceRecord(**json.loads(value)))
        return sorted(records, key=lambda item: item.name)

    def cleanup_stale(self) -> list[str]:
        removed: list[str] = []
        for record in self.list():
            try:
                os.kill(record.pid, 0)
            except ProcessLookupError:
                self.unregister(record.name)
                removed.append(record.name)
            except PermissionError as exc:
                raise RegistryError(f"unable to inspect process {record.pid}: {exc}") from exc
        return removed


def running_record(name: str, pid: int, socket: str, version: str) -> ServiceRecord:
    now = int(time.time())
    return ServiceRecord(name=name, pid=pid, socket=socket, version=version, started_at=now, updated_at=now, state="running")
