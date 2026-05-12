import os

from marpelle.paths import PathConfig
from marpelle.registry import Registry, running_record


def test_registry_crud(tmp_path):
    paths = PathConfig(runtime_dir=tmp_path / "run", state_dir=tmp_path / "state")
    reg = Registry(paths)
    try:
        rec = running_record("svc", os.getpid(), "/tmp/s.sock", "1")
        reg.register(rec)
        got = reg.get("svc")
        assert got is not None
        assert got.name == "svc"
        assert len(reg.list()) == 1
        reg.unregister("svc")
        assert reg.get("svc") is None
    finally:
        reg.close()
