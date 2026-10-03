# code/tools/patches/_common.py
"""Shared helpers for patch scripts (Windows-safe git invocation)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
_GIT_ENV = {**os.environ, "GIT_PAGER": "cat", "PAGER": "cat"}


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "--no-pager", *args],
        cwd=ROOT,
        env=_GIT_ENV,
        check=check,
    )


def show_diff() -> None:
    print("=" * 70)
    print("  git diff --stat")
    print("=" * 70)
    git("diff", "--stat")
    print()
    print("=" * 70)
    print("  git diff")
    print("=" * 70)
    git("diff")


def commit(paths: list[str], message: str) -> None:
    git("add", *paths)
    git("commit", "-m", message)