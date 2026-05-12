# Marpelle

Marpelle is an explicit, manifest-driven local service framework for packaging Python applications with Nuitka and running them behind Unix domain socket IPC.

## Quickstart

1. Install:
   - `pip install -e .`
2. Run example service:
   - `cd examples/example_service`
   - `python app.py`
3. Query service from another shell:
   - `marpelle list`
   - `marpelle send example-service ping --payload '{"x": 1}'`

## Core Concepts

- `MARPELLE.json|yaml`: service metadata and command allowlist
- Runtime: starts socket server and registers service
- Registry: LMDB records at `/var/lib/marpelle` or user fallback
- CLI: list/status/send/unregister/cleanup/build
- Manual registry repair path: explicit `marpelle register ...` command

See `docs/` for architecture and operations details.
