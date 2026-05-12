# Architecture

Marpelle has five components: manifest loader, runtime orchestration, Unix socket IPC, LMDB registry, and CLI/build tooling.

Lifecycle:
1. Service loads manifest and hooks.
2. Runtime creates directories and socket.
3. Service registers itself in LMDB.
4. CLI discovers service and sends JSON commands.
5. Service dispatches allowed commands to declared hooks.
6. Shutdown unregisters service and removes socket/pid file.
