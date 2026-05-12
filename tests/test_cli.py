from marpelle.cli import cmd_register, make_parser
from marpelle.paths import default_paths
from marpelle.registry import Registry


def test_cli_parser_has_send():
    parser = make_parser()
    args = parser.parse_args(["send", "svc", "ping", "--payload", "{}"])
    assert args.service == "svc"
    assert args.command == "ping"


def test_cli_register_writes_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("MARPELLE_RUNTIME_DIR", str(tmp_path / "run"))
    monkeypatch.setenv("MARPELLE_STATE_DIR", str(tmp_path / "state"))
    parser = make_parser()
    args = parser.parse_args(["register", "--name", "svc", "--socket", "/tmp/svc.sock", "--pid", "1234", "--version", "1.2.3"])
    rc = cmd_register(args)
    assert rc == 0

    reg = Registry(default_paths())
    try:
        item = reg.get("svc")
        assert item is not None
        assert item.pid == 1234
        assert item.version == "1.2.3"
    finally:
        reg.close()


def test_cli_parser_has_manifest_subcommand():
    parser = make_parser()
    args = parser.parse_args(["manifest", "validate"])
    assert args.cmd == "manifest"
    assert args.manifest_cmd == "validate"
