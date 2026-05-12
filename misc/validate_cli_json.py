#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Marpelle CLI.json against CLI.json.schema")
    parser.add_argument("--config", default="CLI.json", help="Path to CLI config JSON")
    parser.add_argument("--schema", default="CLI.json.schema", help="Path to JSON Schema")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    config_path = (base / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)
    schema_path = (base / args.schema).resolve() if not Path(args.schema).is_absolute() else Path(args.schema)

    try:
        config = load_json(config_path)
        schema = load_json(schema_path)
        jsonschema.validate(instance=config, schema=schema)
    except FileNotFoundError as exc:
        print(f"validation failed: file not found: {exc}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"validation failed: invalid JSON in {exc.doc[:0] and 'file' or 'input'}: {exc}")
        return 2
    except jsonschema.ValidationError as exc:
        path = "/".join(str(x) for x in exc.absolute_path)
        where = f" at '{path}'" if path else ""
        print(f"validation failed{where}: {exc.message}")
        return 1
    except jsonschema.SchemaError as exc:
        print(f"validation failed: invalid schema: {exc.message}")
        return 2

    print(f"ok: {config_path.name} matches {schema_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
