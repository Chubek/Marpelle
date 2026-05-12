from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict
from pathlib import Path

from .build import build_with_nuitka
from .ipc import send_request
from .manifest import discover_manifest, load_manifest
from .paths import default_paths
from .registry import Registry, ServiceRecord, running_record


def _registry() -> Registry:
    return Registry(default_paths())


def cmd_list(_args: argparse.Namespace) -> int:
    reg = _registry()
    try:
        for item in reg.list():
            print(json.dumps(asdict(item), indent=2))
        return 0
    finally:
        reg.close()


def cmd_status(args: argparse.Namespace) -> int:
    reg = _registry()
    try:
        record = reg.get(args.service)
        if record is None:
            print(f"service not found: {args.service}")
            return 1
        print(json.dumps(asdict(record), indent=2))
        return 0
    finally:
        reg.close()


def cmd_send(args: argparse.Namespace) -> int:
    reg = _registry()
    try:
        record = reg.get(args.service)
        if record is None:
            print(f"service not found: {args.service}")
            return 1
        payload = json.loads(args.payload)
        print(json.dumps(send_request(record.socket, args.command, payload), indent=2))
        return 0
    finally:
        reg.close()


def cmd_unregister(args: argparse.Namespace) -> int:
    reg = _registry()
    try:
        reg.unregister(args.service)
        print(f"unregistered: {args.service}")
        return 0
    finally:
        reg.close()


def cmd_cleanup(_args: argparse.Namespace) -> int:
    reg = _registry()
    try:
        removed = reg.cleanup_stale()
        print(json.dumps({"removed": removed}, indent=2))
        return 0
    finally:
        reg.close()


def cmd_build(args: argparse.Namespace) -> int:
    manifest = Path(args.manifest) if args.manifest else discover_manifest(Path.cwd())
    extra = args.extra_args or []
    return build_with_nuitka(
        entry=Path(args.entry),
        manifest=manifest,
        standalone=args.standalone,
        onefile=args.onefile,
        output_name=args.output,
        extra_args=extra,
    )


def _record_from_args(args: argparse.Namespace) -> ServiceRecord:
    if args.manifest:
        manifest = load_manifest(Path(args.manifest))
        pid = args.pid if args.pid is not None else os.getpid()
        return running_record(manifest.name, pid, manifest.socket, manifest.version)

    if not args.name or not args.socket:
        raise SystemExit("register requires --name and --socket when --manifest is not used")

    pid = args.pid if args.pid is not None else os.getpid()
    now = int(time.time())
    started_at = args.started_at if args.started_at is not None else now
    updated_at = args.updated_at if args.updated_at is not None else now
    return ServiceRecord(
        name=args.name,
        pid=pid,
        socket=args.socket,
        version=args.version,
        started_at=started_at,
        updated_at=updated_at,
        state=args.state,
    )


def cmd_register(args: argparse.Namespace) -> int:
    record = _record_from_args(args)
    reg = _registry()
    try:
        reg.register(record)
        print(json.dumps({"registered": record.name, "pid": record.pid, "socket": record.socket}, indent=2))
        return 0
    finally:
        reg.close()


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="marpelle")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list")
    p_list.set_defaults(func=cmd_list)

    p_status = sub.add_parser("status")
    p_status.add_argument("service")
    p_status.set_defaults(func=cmd_status)

    p_send = sub.add_parser("send")
    p_send.add_argument("service")
    p_send.add_argument("command")
    p_send.add_argument("--payload", default="{}")
    p_send.set_defaults(func=cmd_send)

    p_register = sub.add_parser("register")
    p_register.add_argument("--manifest", default=None)
    p_register.add_argument("--name", default=None)
    p_register.add_argument("--socket", default=None)
    p_register.add_argument("--version", default="unknown")
    p_register.add_argument("--pid", type=int, default=None)
    p_register.add_argument("--state", default="running")
    p_register.add_argument("--started-at", type=int, default=None)
    p_register.add_argument("--updated-at", type=int, default=None)
    p_register.set_defaults(func=cmd_register)

    p_unreg = sub.add_parser("unregister")
    p_unreg.add_argument("service")
    p_unreg.set_defaults(func=cmd_unregister)

    p_cleanup = sub.add_parser("cleanup")
    p_cleanup.set_defaults(func=cmd_cleanup)

    p_build = sub.add_parser("build")
    p_build.add_argument("entry")
    p_build.add_argument("--manifest", default=None)
    p_build.add_argument("--output", default=None)
    p_build.add_argument("--standalone", action="store_true", default=True)
    p_build.add_argument("--onefile", action="store_true")
    p_build.add_argument("--extra-arg", dest="extra_args", action="append")
    p_build.set_defaults(func=cmd_build)

    return parser


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
