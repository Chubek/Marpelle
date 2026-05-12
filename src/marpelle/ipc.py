from __future__ import annotations

import json
import socket
from typing import Any

from .errors import IPCError


class IPCServer:
    def __init__(self, socket_path: str, allowed_commands: set[str], handlers: dict[str, Any]):
        self.socket_path = socket_path
        self.allowed_commands = allowed_commands
        self.handlers = handlers
        self._sock: socket.socket | None = None

    def start(self) -> None:
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(self.socket_path)
        self._sock.listen(16)

    def serve_once(self) -> None:
        if self._sock is None:
            raise IPCError("server not started")
        conn, _ = self._sock.accept()
        with conn:
            conn.settimeout(5.0)
            raw = conn.recv(65536)
            response = self._dispatch(raw)
            conn.sendall(json.dumps(response).encode())

    def _dispatch(self, raw: bytes) -> dict[str, Any]:
        try:
            request = json.loads(raw.decode())
        except Exception:
            return {"ok": False, "error": {"code": "bad_request", "message": "invalid json"}}

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

    def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None


def send_request(socket_path: str, command: str, payload: dict[str, Any], timeout: float = 5.0) -> dict[str, Any]:
    request = {"command": command, "payload": payload}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(socket_path)
        sock.sendall(json.dumps(request).encode())
        data = sock.recv(65536)
    return json.loads(data.decode())
