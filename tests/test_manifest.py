from pathlib import Path

import pytest

from marpelle.errors import ManifestError
from marpelle.manifest import load_manifest


def test_load_json_manifest(tmp_path: Path):
    path = tmp_path / "MARPELLE.json"
    path.write_text('{"name":"svc","version":"1","socket":"/tmp/s.sock","commands":["ping"],"register":true}', encoding="utf-8")
    manifest = load_manifest(path)
    assert manifest.name == "svc"
    assert manifest.commands == ["ping"]


def test_manifest_requires_commands(tmp_path: Path):
    path = tmp_path / "MARPELLE.json"
    path.write_text('{"name":"svc","version":"1","socket":"/tmp/s.sock","commands":[],"register":true}', encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(path)
