#!/usr/bin/env python3
"""Scan source files and report embedded version strings."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_ROOT = Path("code")
DEFAULT_EXTS = {".py", ".c", ".h", ".md", ".txt", ".yml", ".yaml", ".xml", ".json"}
DEFAULT_EXCLUDE_DIRS = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache",
    "output", "misra_report", "build", "dist",
}

PATTERNS = [
    ("__version__", re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')),
    ("VERSION", re.compile(r'\bVERSION\s*=\s*["\']([^"\']+)["\']')),
    ("Version:", re.compile(r'\bVersion\s*:\s*([0-9]+(?:\.[0-9]+){1,3})', re.I)),
    ("@version", re.compile(r'@version\s+([0-9]+(?:\.[0-9]+){1,3})', re.I)),
    ("version=", re.compile(r'\bversion\s*=\s*["\']([0-9]+(?:\.[0-9]+){1,3})["\']', re.I)),
    ("vX.Y.Z", re.compile(r'\bv([0-9]+(?:\.[0-9]+){1,3})\b')),
]


def iter_files(root: Path, exts: set[str], exclude_dirs: set[str]) -> Iterable[Path]:
    for p in root.rglob("*"):
        if any(part in exclude_dirs for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def find_versions(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, rx in PATTERNS:
            for m in rx.finditer(line):
                yield {
                    "file": str(path),
                    "line": lineno,
                    "pattern": name,
                    "version": m.group(1) if m.groups() else m.group(0),
                }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check embedded versions in source files.")
    ap.add_argument("root", nargs="?", default=str(DEFAULT_ROOT), help="root directory (default: code)")
    ap.add_argument("--ext", action="append", default=[], help="additional extension (e.g. --ext .py)")
    ap.add_argument("--exclude", action="append", default=[], help="additional exclude directory name")
    ap.add_argument("--json", action="store_true", help="output JSON")
    ap.add_argument("--csv", action="store_true", help="output CSV")
    ap.add_argument("--strict", action="store_true", help="exit 1 if no version found")
    args = ap.parse_args(argv)

    root = Path(args.root)
    exts = set(DEFAULT_EXTS)
    for e in args.ext:
        exts.add(e if e.startswith(".") else "." + e)

    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    exclude_dirs.update(args.exclude)

    records = []
    for p in sorted(iter_files(root, exts, exclude_dirs)):
        records.extend(find_versions(p))

    if args.json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
    elif args.csv:
        w = csv.DictWriter(sys.stdout, fieldnames=["file", "line", "pattern", "version"])
        w.writeheader()
        w.writerows(records)
    else:
        if not records:
            print("No version strings found.", file=sys.stderr)
        for r in records:
            print(f"{r['file']}:{r['line']}: {r['version']}  [{r['pattern']}]")

    if args.strict and not records:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())