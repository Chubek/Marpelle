from pathlib import Path

from marpelle.ipc import discover_backends


def test_discover_backends_register_function(tmp_path: Path):
    plugin = tmp_path / "plugin_register.py"
    plugin.write_text(
        "from marpelle.ipc import IPCBackendSpec, IPCTypes, UnixSocketSender, UnixSocketReceiver\n"
        "from marpelle.serde import JsonSerde\n"
        "def register(manager):\n"
        "    serde = JsonSerde()\n"
        "    manager.register(IPCBackendSpec(name='x', ipc_type=IPCTypes.REQUEST_REPLY, serializer=serde, deserializer=serde, sender_factory=UnixSocketSender, receiver_factory=UnixSocketReceiver))\n",
        encoding="utf-8",
    )
    manager = discover_backends(str(tmp_path))
    assert "x" in manager.registry


def test_discover_backends_manifest_dict(tmp_path: Path):
    plugin = tmp_path / "plugin_dict.py"
    plugin.write_text(
        "from marpelle.ipc import IPCTypes, UnixSocketSender, UnixSocketReceiver\n"
        "from marpelle.serde import JsonSerde\n"
        "serde = JsonSerde()\n"
        "MARPELLE_IPC_PLUGIN = {\n"
        "'name':'y', 'type': IPCTypes.REQUEST_REPLY.value,\n"
        "'serializer': serde, 'deserializer': serde,\n"
        "'sender_factory': UnixSocketSender, 'receiver_factory': UnixSocketReceiver\n"
        "}\n",
        encoding="utf-8",
    )
    manager = discover_backends(str(tmp_path))
    assert "y" in manager.registry
