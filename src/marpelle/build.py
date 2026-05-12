from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path


def build_with_nuitka(
    entry: Path,
    manifest: Path,
    hooks_module: str = "marpelle_hooks",
    standalone: bool = True,
    onefile: bool = False,
    output_name: str | None = None,
    extra_args: list[str] | None = None,
) -> int:
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--follow-imports",
        f"--include-data-files={manifest.resolve()}={manifest.name}",
        "--include-package=marpelle",
        f"--include-module={hooks_module}",
    ]
    if standalone:
        cmd.append("--standalone")
    if onefile:
        cmd.append("--onefile")
    if output_name:
        cmd.append(f"--output-filename={output_name}")
    if extra_args:
        cmd.extend(extra_args)

    cmd.append(str(entry.resolve()))
    print("+", shlex.join(cmd))
    proc = subprocess.run(cmd, check=False)
    return proc.returncode
