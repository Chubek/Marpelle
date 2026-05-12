import subprocess
import sys
import os
from pathlib import Path


def _run(*args: str):
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    return subprocess.run(
        [sys.executable, "-m", "marpelle", *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_root_help_lists_commands():
    proc = _run("--help")
    assert proc.returncode == 0
    assert "Commands:" in proc.stdout
    assert "build" in proc.stdout


def test_build_help_shows_build_arguments():
    proc = _run("build", "--help")
    assert proc.returncode == 0
    assert "Command: marpelle build" in proc.stdout
    assert "--c-compiler" in proc.stdout


def test_version_flag_from_yaml():
    proc = _run("--version")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "1.0.0"
