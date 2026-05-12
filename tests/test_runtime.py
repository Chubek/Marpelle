from marpelle.manifest import Manifest
from marpelle.runtime import ServiceRuntime


def test_runtime_filters_hooks(monkeypatch, tmp_path):
    manifest = Manifest(
        name="svc",
        version="1",
        socket=str(tmp_path / "svc.sock"),
        commands=["ping"],
        register=False,
    )

    monkeypatch.setattr("marpelle.runtime.load_hooks", lambda _module: {"ping": lambda _p: {"a": 1}, "x": lambda _p: {}})
    rt = ServiceRuntime(manifest)
    assert set(rt.handlers.keys()) == {"ping"}
    rt.registry.close()
