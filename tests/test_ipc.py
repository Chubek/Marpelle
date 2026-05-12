from marpelle.ipc import IPCServer


def test_ipc_dispatch_allowed():
    server = IPCServer("/tmp/unused.sock", {"ping"}, {"ping": lambda p: {"ok": p.get("x")}})
    resp = server._dispatch(b'{"command":"ping","payload":{"x":1}}')
    assert resp["ok"] is True
    assert resp["result"]["ok"] == 1


def test_ipc_dispatch_reject_unknown():
    server = IPCServer("/tmp/unused.sock", {"ping"}, {})
    resp = server._dispatch(b'{"command":"boom","payload":{}}')
    assert resp["ok"] is False
