from __future__ import annotations

import os
import signal
from pathlib import Path

from .daemon import daemonize
from .hooks import load_hooks
from .ipc import IPCServer
from .luaspec_daemon import load_daemon_lua
from .manifest import Manifest, discover_manifest, load_manifest
from .paths import default_paths, ensure_paths
from .registry import Registry, running_record


class ServiceRuntime:
    def __init__(self, manifest: Manifest, hooks_module: str = "marpelle_hooks"):
        self.manifest = manifest
        self.paths = default_paths()
        ensure_paths(self.paths)
        self.registry = Registry(self.paths)
        hooks = load_hooks(hooks_module)
        self.handlers = {name: hooks[name] for name in manifest.commands if name in hooks}
        self.server = IPCServer(manifest.socket, set(manifest.commands), self.handlers)
        self._running = True
        self._lua_spec = None

    def _shutdown(self, *_args: object) -> None:
        self._running = False

    def apply_daemon_lua(self, daemon_lua_path: str | None = None) -> None:
        spec_path = daemon_lua_path or self.manifest.daemon_lua_file
        if not spec_path:
            return
        spec = load_daemon_lua(spec_path)
        self._lua_spec = spec
        if spec.working_directory:
            self.manifest.working_directory = spec.working_directory
        if spec.pid_file:
            self.manifest.pid_file = spec.pid_file
        if spec.socket:
            self.manifest.socket = spec.socket
            self.server.socket_path = spec.socket
        if spec.daemonize:
            self.manifest.daemonize = True
        if spec.ipc_backend:
            self.manifest.ipc_backend = spec.ipc_backend

    def run(self, force_daemonize: bool = False, daemon_lua_path: str | None = None) -> None:
        self.apply_daemon_lua(daemon_lua_path)
        if self.manifest.working_directory:
            os.chdir(self.manifest.working_directory)
        if self.manifest.daemonize or force_daemonize:
            umask = self._lua_spec.umask if self._lua_spec and self._lua_spec.umask is not None else 0
            context = daemonize(
                working_directory=self.manifest.working_directory or "/",
                umask=umask,
            )
            context.open()
        if self.manifest.pid_file:
            Path(self.manifest.pid_file).write_text(str(os.getpid()), encoding="utf-8")

        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

        if Path(self.manifest.socket).exists():
            Path(self.manifest.socket).unlink()

        self.server.start()
        if self.manifest.register:
            self.registry.register(running_record(self.manifest.name, os.getpid(), self.manifest.socket, self.manifest.version))

        try:
            while self._running:
                self.server.serve_once()
        finally:
            self.server.close()
            if self.manifest.register:
                self.registry.unregister(self.manifest.name)
            if Path(self.manifest.socket).exists():
                Path(self.manifest.socket).unlink()
            if self.manifest.pid_file and Path(self.manifest.pid_file).exists():
                Path(self.manifest.pid_file).unlink()
            self.registry.close()


def run_service(
    manifest_path: str | None = None,
    hooks_module: str = "marpelle_hooks",
    daemon_mode: bool = False,
    daemon_lua_path: str | None = None,
) -> None:
    manifest_file = Path(manifest_path) if manifest_path else discover_manifest()
    runtime = ServiceRuntime(load_manifest(manifest_file), hooks_module=hooks_module)
    runtime.run(force_daemonize=daemon_mode, daemon_lua_path=daemon_lua_path)
