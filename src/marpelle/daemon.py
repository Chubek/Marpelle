from __future__ import annotations

from typing import Any


def daemonize(
    working_directory: str = "/",
    umask: int = 0,
    detach_process: bool = True,
) -> Any:
    try:
        import daemon
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("python-daemon is required for daemon mode") from exc
    return daemon.DaemonContext(
        working_directory=working_directory,
        umask=umask,
        detach_process=detach_process,
    )
