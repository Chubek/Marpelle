from marpelle.paths import default_paths


def test_default_paths_env(monkeypatch):
    monkeypatch.setenv("MARPELLE_RUNTIME_DIR", "/tmp/run-a")
    monkeypatch.setenv("MARPELLE_STATE_DIR", "/tmp/state-a")
    paths = default_paths()
    assert str(paths.runtime_dir) == "/tmp/run-a"
    assert str(paths.state_dir) == "/tmp/state-a"
