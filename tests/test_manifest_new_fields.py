from pathlib import Path

from marpelle.manifest import load_manifest


def test_manifest_default_compiler_and_ipc_backend(tmp_path: Path):
    path = tmp_path / "MARPELLE.json"
    path.write_text(
        '{"name":"svc","version":"1","socket":"/tmp/s.sock","commands":["ping"],"register":true}',
        encoding="utf-8",
    )
    m = load_manifest(path)
    assert m.c_compiler == "gcc"
    assert m.ipc_backend == "unix"
