#!/usr/bin/env python3
"""List the latest version string found in each source file."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_ROOT = Path("code")
DEFAULT_EXTS = {".py", ".c", ".h"}
DEFAULT_EXCLUDE_DIRS = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    "output", "misra_report", "build", "dist", "tests",
}

# 検出パターン（優先度順）
PATTERNS = [
    # ファイル先頭の "Version: 3.5" / "version: 3.5"
    ("header", re.compile(r'^\s*Version\s*:\s*([0-9]+(?:\.[0-9]+){1,3})', re.I | re.M)),
    # docstring 内の "@version 3.5"
    ("at",     re.compile(r'@version\s+([0-9]+(?:\.[0-9]+){1,3})', re.I)),
    # __version__ = "3.5"
    ("dunder", re.compile(r'__version__\s*=\s*["\']([0-9]+(?:\.[0-9]+){1,3})["\']')),
    # VERSION = "3.5"
    ("const",  re.compile(r'\bVERSION\s*=\s*["\']([0-9]+(?:\.[0-9]+){1,3})["\']')),
    # "Module v2.2.9" のような本文中の記述（最後の手段）
    ("body",   re.compile(r'\bv([0-9]+(?:\.[0-9]+){1,3})\b')),
]


def version_key(v: str):
    return tuple(int(x) for x in v.split("."))


def iter_files(root: Path, exts: set[str], exclude_dirs: set[str]) -> Iterable[Path]:
    for p in root.rglob("*"):
        if any(part in exclude_dirs for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def extract_version(path: Path):
    """Return (version, pattern, line) of the highest-priority match."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    # ファイル先頭 200 行に限定して誤検出を防ぐ
    head = "\n".join(text.splitlines()[:200])

    for name, rx in PATTERNS:
        m = rx.search(head)
        if m:
            return m.group(1), name
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="List latest version per source file.")
    ap.add_argument("root", nargs="?", default=str(DEFAULT_ROOT))
    ap.add_argument("--ext", action="append", default=[])
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--missing", action="store_true", help="show files with no version")
    args = ap.parse_args(argv)

    root = Path(args.root)
    exts = set(DEFAULT_EXTS)
    for e in args.ext:
        exts.add(e if e.startswith(".") else "." + e)
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    exclude_dirs.update(args.exclude)

    rows = []
    missing = []
    for p in sorted(iter_files(root, exts, exclude_dirs)):
        r = extract_version(p)
        if r:
            rows.append((str(p), r[0], r[1]))
        else:
            missing.append(str(p))

    if rows:
        w = max(len(f) for f, _, _ in rows)
        print(f"{'FILE':<{w}}  {'VERSION':<10}  SOURCE")
        print("-" * (w + 24))
        for f, v, src in rows:
            print(f"{f:<{w}}  {v:<10}  {src}")
    else:
        print("No version strings found.", file=sys.stderr)

    if args.missing and missing:
        print("\n--- No version detected ---", file=sys.stderr)
        for m in missing:
            print(m, file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())