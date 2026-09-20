#!/usr/bin/env python3
"""Batch-rename *_jp.* files to *_ja.* and update all references.

Usage:
    cd C:/Users/user/OneDrive/ドキュメント/GitHub/StaTable/code
    python tools/rename_ja_suffix.py             # dry-run (preview)
    python tools/rename_ja_suffix.py --apply     # execute

Safety:
    - Never touches .git/ directory.
    - Skips SKIP_DIRS and SKIP_FILES (self, pattern-defining tools).
    - Dry-run by default.
    - Does NOT rewrite itself or extract_residuals.py.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules",
             ".pytest_cache", "logs", "output", "misra_report"}

# Files that must never be rewritten.
# - rename_ja_suffix.py: contains the regex patterns below (self).
# - extract_residuals.py: holds _jp literals as processing data.
SKIP_FILES = {
    "rename_ja_suffix.py",
    "extract_residuals.py",
}

TEXT_EXTS = {".md", ".py", ".yml", ".yaml", ".json", ".txt",
             ".cfg", ".toml", ".ini", ".rst"}

# Patterns to replace (old -> new).
# NOTE: these patterns contain literal "_jp" strings;
#       therefore this file must be listed in SKIP_FILES.
RENAME_PATTERNS = [
    (re.compile(r"(_)jp(\.[A-Za-z0-9]+)"), r"\1ja\2"),
    (re.compile(r"(SPEC_SCREENS)_jp\b"), r"\1_ja"),
    (re.compile(r"(SPEC_OVERVIEW)_jp\b"), r"\1_ja"),
    (re.compile(r"(SPEC_AUDIT)_jp\b"), r"\1_ja"),
    (re.compile(r"(SPEC_CODEGEN)_jp\b"), r"\1_ja"),
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def is_skipped(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if path.name in SKIP_FILES:
        return True
    return False


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if is_skipped(p):
            continue
        yield p


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def find_jp_files(root: Path) -> list[Path]:
    hits = []
    for p in iter_files(root):
        if re.search(r"_jp\.[A-Za-z0-9]+$", p.name):
            hits.append(p)
    return hits


def compute_renames(files: list[Path]) -> list[tuple[Path, Path]]:
    plan = []
    for src in files:
        new_name = re.sub(r"_jp(\.[A-Za-z0-9]+)$", r"_ja\1", src.name)
        dst = src.with_name(new_name)
        plan.append((src, dst))
    return plan


def find_references(root: Path, jp_basenames: set[str]):
    hits = []
    for p in iter_files(root):
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        text = read_text(p)
        if text is None:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for name in jp_basenames:
                if name in line:
                    hits.append((p, i, line.rstrip()))
                    break
    return hits


def find_pattern_matches(root: Path):
    hits = []
    for p in iter_files(root):
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        text = read_text(p)
        if text is None:
            continue
        for pat, _ in RENAME_PATTERNS:
            if pat.search(text):
                hits.append(p)
                break
    return hits


def rewrite_references(root: Path):
    changed = []
    for p in iter_files(root):
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        text = read_text(p)
        if text is None:
            continue
        new_text = text
        for pat, repl in RENAME_PATTERNS:
            new_text = pat.sub(repl, new_text)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            changed.append(p)
    return changed


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="Execute the plan (default is dry-run).")
    ap.add_argument("--root", default=str(REPO_ROOT))
    return ap.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    print("=" * 70)
    print(f"  Rename *_jp.* -> *_ja.*   root={root}")
    print(f"  mode = {'APPLY' if args.apply else 'DRY-RUN'}")
    print("=" * 70)

    jp_files = find_jp_files(root)
    print(f"\n[1] Found {len(jp_files)} *_jp.* file(s):")
    for p in jp_files:
        print(f"    {p.relative_to(root)}")
    if not jp_files:
        print("    (nothing to rename)")

    renames = compute_renames(jp_files)
    print(f"\n[2] Rename plan ({len(renames)}):")
    for src, dst in renames:
        print(f"    {src.relative_to(root)}")
        print(f"      -> {dst.relative_to(root)}")

    jp_basenames = {p.name for p in jp_files}
    refs = find_references(root, jp_basenames) if jp_basenames else []
    print(f"\n[3] References to rename targets: {len(refs)} hit(s)")
    for p, ln, text in refs[:50]:
        print(f"    {p.relative_to(root)}:{ln}: {text}")

    pattern_hits = find_pattern_matches(root)
    print(f"\n[4] Files matching rename patterns: {len(pattern_hits)}")
    for p in pattern_hits[:50]:
        print(f"    {p.relative_to(root)}")

    if not args.apply:
        print("\n" + "=" * 70)
        print("  DRY-RUN complete. Re-run with --apply to execute.")
        print("=" * 70)
        return 0

    print("\n" + "=" * 70)
    print("  APPLYING")
    print("=" * 70)

    changed = rewrite_references(root)
    print(f"\n[5] Rewrote references in {len(changed)} file(s):")
    for p in changed:
        print(f"    {p.relative_to(root)}")

    print(f"\n[6] Renaming {len(renames)} file(s):")
    for src, dst in renames:
        if dst.exists():
            print(f"    SKIP (target exists): {dst.relative_to(root)}")
            continue
        src.rename(dst)
        print(f"    {src.relative_to(root)} -> {dst.relative_to(root)}")

    print("\n" + "=" * 70)
    print("  DONE. Recommended: git status")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))