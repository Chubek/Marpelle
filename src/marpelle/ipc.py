from __future__ import annotations

import importlib.util
import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any

from .errors import IPCError
from .serde import Deserializer, JsonSerde, Serializer
from .transport import Endpoint, TransportRegistry


class IPCTypes(str, Enum):
    REQUEST_REPLY = "request_reply"
    PUBSUB = "pubsub"


class IPCSender(ABC):
    @abstractmethod
    def send(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class IPCReceiver(ABC):
    @abstractmethod
    def serve_once(self) -> None:
        raise NotImplementedError


@dataclass(slots=True)
class IPCBackendSpec:
    name: str
    ipc_type: IPCTypes
    serializer: Serializer
    deserializer: Deserializer
    sender_factory: Any
    receiver_factory: Any
    transport: TransportRegistry = field(default_factory=TransportRegistry)
    external_handle: Any = None


class IPCManager:
    def __init__(self, name: str = "default"):
        self.name = name
        self.query_params: dict[str, str] = {}
        self.registry: dict[str, IPCBackendSpec] = {}

    def add_query_param(self, key: str, value: Any) -> None:
        self.query_params[key] = str(value)

    def register(self, spec: IPCBackendSpec) -> None:
        if spec.name in self.registry:
            raise IPCError(f"backend already registered: {spec.name}")
        self.registry[spec.name] = spec

    def resolve(self, name: str) -> IPCBackendSpec:
        backend = self.registry.get(name)
        if backend is None:
            raise IPCError(f"unknown IPC backend: {name}")
        return backend


class UnixSocketSender(IPCSender):
    def __init__(self, socket_path: str, serializer: Serializer, deserializer: Deserializer, timeout: float = 5.0):
        self.socket_path = socket_path
        self.serializer = serializer
        self.deserializer = deserializer
        self.timeout = timeout

    def send(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = {"command": command, "payload": payload}
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            sock.connect(self.socket_path)
            sock.sendall(self.serializer.dumps(request))
            data = sock.recv(65536)
        return self.deserializer.loads(data)


class UnixSocketReceiver(IPCReceiver):
    def __init__(
        self,
        socket_path: str,
        allowed_commands: set[str],
        handlers: dict[str, Any],
        serializer: Serializer,
        deserializer: Deserializer,
    ):
        self.socket_path = socket_path
        self.allowed_commands = allowed_commands
        self.handlers = handlers
        self.serializer = serializer
        self.deserializer = deserializer
        self._sock: socket.socket | None = None

    def start(self) -> None:
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(self.socket_path)
        self._sock.listen(16)

    def _dispatch(self, raw: bytes) -> dict[str, Any]:
        try:
            request = self.deserializer.loads(raw)
        except Exception:
            return {"ok": False, "error": {"code": "bad_request", "message": "invalid payload"}}

        command = request.get("command")
        payload = request.get("payload", {})
        if not isinstance(command, str):
            return {"ok": False, "error": {"code": "bad_request", "message": "command must be string"}}
        if command not in self.allowed_commands:
            return {"ok": False, "error": {"code": "forbidden", "message": f"command not allowed: {command}"}}
        if command not in self.handlers:
            return {"ok": False, "error": {"code": "not_implemented", "message": f"missing hook for: {command}"}}
        if not isinstance(payload, dict):
            return {"ok": False, "error": {"code": "bad_request", "message": "payload must be object"}}

        try:
            result = self.handlers[command](payload)
        except Exception as exc:
            return {"ok": False, "error": {"code": "handler_error", "message": str(exc)}}
        return {"ok": True, "result": result}

    def serve_once(self) -> None:
        if self._sock is None:
            raise IPCError("server not started")
        conn, _ = self._sock.accept()
        with conn:
            conn.settimeout(5.0)
            raw = conn.recv(65536)
            response = self._dispatch(raw)
            conn.sendall(self.serializer.dumps(response))

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None


class IPCServer(UnixSocketReceiver):
    """Backwards-compatible server alias."""

    def __init__(self, socket_path: str, allowed_commands: set[str], handlers: dict[str, Any]):
        serde = JsonSerde()
        super().__init__(socket_path, allowed_commands, handlers, serde, serde)


def send_request(socket_path: str, command: str, payload: dict[str, Any], timeout: float = 5.0) -> dict[str, Any]:
    serde = JsonSerde()
    sender = UnixSocketSender(socket_path=socket_path, serializer=serde, deserializer=serde, timeout=timeout)
    return sender.send(command, payload)


def _load_plugin_from_file(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"marpelle_ipc_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise IPCError(f"failed to load plugin: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def register_plugin_module(manager: IPCManager, module: ModuleType) -> None:
    register = getattr(module, "register", None)
    if callable(register):
        register(manager)
        return

    spec_data = getattr(module, "MARPELLE_IPC_PLUGIN", None)
    if not isinstance(spec_data, dict):
        raise IPCError(f"{module.__name__} must expose register(manager) or MARPELLE_IPC_PLUGIN")

    required = {"name", "type", "serializer", "deserializer", "sender_factory", "receiver_factory"}
    missing = sorted(required - set(spec_data))
    if missing:
        raise IPCError(f"{module.__name__} missing IPC plugin keys: {', '.join(missing)}")

    ipc_type_raw = spec_data["type"]
    try:
        ipc_type = IPCTypes(str(ipc_type_raw))
    except Exception as exc:
        raise IPCError(f"{module.__name__} has unsupported IPC type: {ipc_type_raw}") from exc

    backend = IPCBackendSpec(
        name=str(spec_data["name"]),
        ipc_type=ipc_type,
        serializer=spec_data["serializer"],
        deserializer=spec_data["deserializer"],
        sender_factory=spec_data["sender_factory"],
        receiver_factory=spec_data["receiver_factory"],
        external_handle=spec_data.get("external_handle"),
    )
    manager.register(backend)


def discover_backends(search_path: str | None = None) -> IPCManager:
    manager = IPCManager(name="discovered")
    raw = search_path or "~/.marpelle"
    candidates = [Path(part).expanduser() for part in raw.split(":") if part.strip()]

    for directory in candidates:
        if not directory.exists() or not directory.is_dir():
            continue
        for py_file in sorted(directory.glob("*.py")):
            module = _load_plugin_from_file(py_file)
            register_plugin_module(manager, module)
    return manager


def endpoint_from_handler(handler: Any) -> Endpoint | None:
    meta = getattr(handler, "__marpelle_transport__", None)
    if not isinstance(meta, dict):
        return None
    role = meta.get("role")
    route = meta.get("route")
    if not isinstance(role, str) or not isinstance(route, str):
        return None
    return Endpoint(role=role, route=route, handler=handler)
