from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from .build import build_with_nuitka
from .ipc import send_request
from .luaspec_daemon import load_daemon_lua
from .manifest import discover_manifest, load_manifest
from .paths import default_paths
from .registry import Registry, ServiceRecord, running_record
from .runtime import run_service

_MISC_DIR = Path(__file__).resolve().parents[2] / "misc"
sys.path.append(str(_MISC_DIR))
from termcolor import colored  # type: ignore  # noqa: E402


CLI_CONFIG_PATH = _MISC_DIR / "CLI.json"
VERSION_PATH = Path(__file__).resolve().parents[2] / "VERSION.yaml"


def _load_cli_config() -> dict[str, Any]:
    return json.loads(CLI_CONFIG_PATH.read_text(encoding="utf-8"))


def _color(text: str, role: str, cfg: dict[str, Any]) -> str:
    color_name = cfg.get("colors", {}).get(role)
    if not color_name:
        return text
    try:
        return colored(text, color_name)
    except Exception:
        return text


def _fmt_arg(item: dict[str, Any]) -> str:
    if "name" in item:
        label = item["name"]
    else:
        label = item.get("long", "")
        if item.get("short"):
            label = f"{item['short']}, {label}"
    if item.get("default") is not None:
        return f"{label} (default: {item['default']})"
    return label


def _print_help(command_chain: list[str] | None = None) -> None:
    cfg = _load_cli_config()
    command_chain = command_chain or []

    print(_color(cfg.get("prog", "marpelle"), "title", cfg))
    print(cfg.get("description", ""))
    print()

    if not command_chain:
        print(_color("Global Options:", "section", cfg))
        for item in cfg.get("global_args", []):
            print(f"  {_color(_fmt_arg(item), 'argument', cfg)}: {item.get('help', '')}")
        print()
        print(_color("Commands:", "section", cfg))
        for name, item in cfg.get("commands", {}).items():
            print(f"  {_color(name, 'command', cfg)}: {item.get('help', '')}")
        return

    node: dict[str, Any] | None = cfg.get("commands", {})
    selected: dict[str, Any] | None = None
    for part in command_chain:
        if node is None or part not in node:
            print(_color(f"Unknown command path: {' '.join(command_chain)}", "section", cfg))
            return
        selected = node[part]
        node = selected.get("subcommands")

    if selected is None:
        return

    label = " ".join([cfg.get("prog", "marpelle"), *command_chain])
    print(_color(f"Command: {label}", "section", cfg))
    print(selected.get("help", ""))
    print()

    print(_color("Arguments:", "section", cfg))
    for item in selected.get("args", []):
        print(f"  {_color(_fmt_arg(item), 'argument', cfg)}: {item.get('help', '')}")

    subcommands = selected.get("subcommands", {})
    if subcommands:
        print()
        print(_color("Subcommands:", "section", cfg))
        for name, item in subcommands.items():
            print(f"  {_color(name, 'command', cfg)}: {item.get('help', '')}")


def _extract_version() -> str:
    data = yaml.safe_load(VERSION_PATH.read_text(encoding="utf-8")) or {}
    versions = data.get("versions") or []
    if not versions:
        return "0.0.0"
    initial = versions[0].get("initial_version", []) if isinstance(versions[0], dict) else []
    parts = {"major": 0, "minor": 0, "match": 0}
    for entry in initial:
        if isinstance(entry, dict):
            for key in parts:
                if key in entry:
                    parts[key] = int(entry[key])
    return f"{parts['major']}.{parts['minor']}.{parts['match']}"


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
    manifest_data = load_manifest(manifest)
    extra = args.extra_args or []
    return build_with_nuitka(
        entry=Path(args.entry),
        manifest=manifest,
        standalone=args.standalone,
        onefile=args.onefile,
        output_name=args.output,
        extra_args=extra,
        c_compiler=args.c_compiler or manifest_data.c_compiler,
    )


def cmd_run(args: argparse.Namespace) -> int:
    run_service(
        manifest_path=args.manifest,
        hooks_module=args.hooks,
        daemon_mode=args.daemon,
        daemon_lua_path=args.daemon_lua,
    )
    return 0


def cmd_daemon_spec(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.manifest)) if args.manifest else load_manifest(discover_manifest())
    daemon_lua = Path(args.daemon_lua) if args.daemon_lua else manifest.daemon_lua_file
    if daemon_lua is None:
        print("No DAEMON.lua configured")
        return 1
    spec = load_daemon_lua(daemon_lua)
    print(json.dumps(asdict(spec), indent=2))
    return 0


def cmd_manifest_show(args: argparse.Namespace) -> int:
    manifest_path = Path(args.path) if args.path else discover_manifest()
    manifest = load_manifest(manifest_path)
    print(json.dumps(asdict(manifest), indent=2))
    return 0


def cmd_manifest_validate(args: argparse.Namespace) -> int:
    manifest_path = Path(args.path) if args.path else discover_manifest()
    load_manifest(manifest_path)
    print(f"valid manifest: {manifest_path}")
    return 0


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
    parser = argparse.ArgumentParser(prog="marpelle", add_help=False)
    parser.add_argument("-h", "--help", action="store_true", dest="help")
    parser.add_argument("-v", "--version", action="store_true", dest="version")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", add_help=False)
    p_list.add_argument("-h", "--help", action="store_true", dest="help")
    p_list.set_defaults(func=cmd_list)

    p_status = sub.add_parser("status", add_help=False)
    p_status.add_argument("service", nargs="?")
    p_status.add_argument("-h", "--help", action="store_true", dest="help")
    p_status.set_defaults(func=cmd_status)

    p_send = sub.add_parser("send", add_help=False)
    p_send.add_argument("service", nargs="?")
    p_send.add_argument("command", nargs="?")
    p_send.add_argument("--payload", default="{}")
    p_send.add_argument("-h", "--help", action="store_true", dest="help")
    p_send.set_defaults(func=cmd_send)

    p_register = sub.add_parser("register", add_help=False)
    p_register.add_argument("--manifest", default=None)
    p_register.add_argument("--name", default=None)
    p_register.add_argument("--socket", default=None)
    p_register.add_argument("--version", default="unknown")
    p_register.add_argument("--pid", type=int, default=None)
    p_register.add_argument("--state", default="running")
    p_register.add_argument("--started-at", type=int, default=None)
    p_register.add_argument("--updated-at", type=int, default=None)
    p_register.add_argument("-h", "--help", action="store_true", dest="help")
    p_register.set_defaults(func=cmd_register)

    p_unreg = sub.add_parser("unregister", add_help=False)
    p_unreg.add_argument("service", nargs="?")
    p_unreg.add_argument("-h", "--help", action="store_true", dest="help")
    p_unreg.set_defaults(func=cmd_unregister)

    p_cleanup = sub.add_parser("cleanup", add_help=False)
    p_cleanup.add_argument("-h", "--help", action="store_true", dest="help")
    p_cleanup.set_defaults(func=cmd_cleanup)

    p_build = sub.add_parser("build", add_help=False)
    p_build.add_argument("entry", nargs="?")
    p_build.add_argument("--manifest", default=None)
    p_build.add_argument("--output", default=None)
    p_build.add_argument("--standalone", action="store_true", default=True)
    p_build.add_argument("--onefile", action="store_true")
    p_build.add_argument("--extra-arg", dest="extra_args", action="append")
    p_build.add_argument("--c-compiler", default=None)
    p_build.add_argument("-h", "--help", action="store_true", dest="help")
    p_build.set_defaults(func=cmd_build)

    p_run = sub.add_parser("run", add_help=False)
    p_run.add_argument("--manifest", default=None)
    p_run.add_argument("--hooks", default="marpelle_hooks")
    p_run.add_argument("--daemon", action="store_true")
    p_run.add_argument("--daemon-lua", default=None)
    p_run.add_argument("-h", "--help", action="store_true", dest="help")
    p_run.set_defaults(func=cmd_run)

    p_dspec = sub.add_parser("daemon-spec", add_help=False)
    p_dspec.add_argument("--manifest", default=None)
    p_dspec.add_argument("--daemon-lua", default=None)
    p_dspec.add_argument("-h", "--help", action="store_true", dest="help")
    p_dspec.set_defaults(func=cmd_daemon_spec)

    p_manifest = sub.add_parser("manifest", add_help=False)
    p_manifest.add_argument("-h", "--help", action="store_true", dest="help")
    manifest_sub = p_manifest.add_subparsers(dest="manifest_cmd")

    p_manifest_show = manifest_sub.add_parser("show", add_help=False)
    p_manifest_show.add_argument("--path", default=None)
    p_manifest_show.add_argument("-h", "--help", action="store_true", dest="help")
    p_manifest_show.set_defaults(func=cmd_manifest_show)

    p_manifest_validate = manifest_sub.add_parser("validate", add_help=False)
    p_manifest_validate.add_argument("--path", default=None)
    p_manifest_validate.add_argument("-h", "--help", action="store_true", dest="help")
    p_manifest_validate.set_defaults(func=cmd_manifest_validate)

    return parser


def _command_chain_from_argv(argv: list[str]) -> list[str]:
    chain: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("-"):
            i += 1
            continue
        if not chain:
            if token in {"list", "status", "send", "register", "unregister", "cleanup", "build", "run", "daemon-spec", "manifest"}:
                chain.append(token)
            else:
                break
        elif chain == ["manifest"]:
            if token in {"show", "validate"}:
                chain.append(token)
            break
        else:
            break
        i += 1
    return chain


def main() -> None:
    argv = sys.argv[1:]
    parser = make_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False):
        print(_extract_version())
        raise SystemExit(0)

    if getattr(args, "help", False) or args.cmd is None:
        _print_help(_command_chain_from_argv(argv))
        raise SystemExit(0)

    if args.cmd == "manifest" and args.manifest_cmd is None:
        _print_help(["manifest"])
        raise SystemExit(0)

    if getattr(args, "func", None) is None:
        _print_help(_command_chain_from_argv(argv))
        raise SystemExit(1)

    raise SystemExit(args.func(args))
