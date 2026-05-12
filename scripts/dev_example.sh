#!/usr/bin/env bash
set -euo pipefail

export MARPELLE_RUNTIME_DIR="${MARPELLE_RUNTIME_DIR:-/tmp/marpelle/run}"
export MARPELLE_STATE_DIR="${MARPELLE_STATE_DIR:-/tmp/marpelle/state}"

python examples/example_service/app.py
