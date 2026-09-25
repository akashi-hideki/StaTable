#!/usr/bin/env python3
"""git_runner.py - execute git operations from a declarative ops file.

Usage (from code/ directory):

    # Traditional: read code/tools/git_ops.txt
    python tools/git_runner.py
    python tools/git_runner.py --list

    # Phase-based (C-51 Step 3 and later):
    # Reads code/tools/git_ops_c51s3_phase<N>.txt
    python tools/git_runner.py --phase 1
    python tools/git_runner.py --phase 2
    python tools/git_runner.py --phase 34

    # Dry run (show what would be executed, no side effects):
    python tools/git_runner.py --dry-run
    python tools/git_runner.py --phase 1 --dry-run

Ops file format (one command per line, leading # comments allowed):

    add <path>
    commit <message>
    push [<remote> <branch>]

Safety features:
  - 'add' verifies the file exists before running git add.
  - 'commit' is skipped if nothing is staged.
  - 'push' is skipped if there are no new commits.
  - --dry-run performs no side effects.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
CODE = TOOLS.parent
REPO = CODE.parent


# ---------------------------------------------------------------------------
# Ops file loading
# ---------------------------------------------------------------------------

def resolve_ops_file(args) -> Path:
    """Return the ops file path based on CLI arguments."""
    if args.phase:
        return TOOLS / f"git_ops_c51s3_phase{args.phase}.txt"
    if args.ops:
        p = Path(args.ops)
        return p if p.is_absolute() else TOOLS / p
    return TOOLS / "git_ops.txt"


def parse_ops(path: Path) -> list[tuple[str, list[str]]]:
    """Parse ops file. Returns list of (verb, args)."""
    if not path.exists():
        print(f"[ERROR] ops file not found: {path}")
        sys.exit(2)

    ops: list[tuple[str, list[str]]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        verb = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""
        if verb == "add":
            ops.append(("add", [rest.strip()]))
        elif verb == "commit":
            ops.append(("commit", [rest.strip()]))
        elif verb == "push":
            # push may have "origin main" or be bare
            args_ = rest.split() if rest else []
            ops.append(("push", args_))
        else:
            print(f"[WARN] unknown verb skipped: {line}")
    return ops


# ---------------------------------------------------------------------------
# git helpers
# ---------------------------------------------------------------------------

def run_git(args: list[str], dry_run: bool = False) -> int:
    cmd = ["git"] + args
    print(f"  $ {' '.join(cmd)}")
    if dry_run:
        print("    (dry-run: skipped)")
        return 0
    try:
        return subprocess.run(cmd, cwd=str(REPO), check=True).returncode
    except subprocess.CalledProcessError as e:
        print(f"    [ERROR] exit code {e.returncode}")
        return e.returncode


def has_staged_changes() -> bool:
    r = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(REPO),
        capture_output=True,
    )
    # exit 0 = no diff; exit 1 = has diff
    return r.returncode == 1


def has_unpushed_commits() -> bool:
    r = subprocess.run(
        ["git", "log", "@{u}..HEAD", "--oneline"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    return bool(r.stdout.strip())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute git operations from a declarative ops file.",
    )
    parser.add_argument("--list", action="store_true",
                        help="show planned commands without executing")
    parser.add_argument("--dry-run", action="store_true",
                        help="run in dry-run mode (no git side effects)")
    parser.add_argument("--phase",
                        help="use git_ops_c51s3_phase<PHASE>.txt")
    parser.add_argument("--ops",
                        help="use a specific ops file (relative to tools/)")
    args = parser.parse_args(argv)

    ops_path = resolve_ops_file(args)
    ops = parse_ops(ops_path)

    print("=" * 70)
    print("  Git Runner")
    print("=" * 70)
    print(f"  Script: {ops_path}")
    print(f"  Repo:   {REPO}")
    print(f"  Mode:   {'LIST' if args.list else 'DRY-RUN' if args.dry_run else 'APPLY'}")
    print(f"  Total:  {len(ops)} command(s)")
    print("=" * 70)

    if args.list:
        for i, (verb, a) in enumerate(ops, 1):
            print(f"  [{i:2}] {verb:8} {verb} {' '.join(a)}".rstrip())
        return 0

    dry = args.dry_run
    failures = 0

    for i, (verb, a) in enumerate(ops, 1):
        print()
        print("-" * 70)
        print(f"  [{i}/{len(ops)}] {verb}: {verb} {' '.join(a)}".rstrip())
        print("-" * 70)

        if verb == "add":
            target = a[0]
            # Normalize path: allow both "code/..." and bare filename
            candidates = [
                REPO / target,
                CODE / target,
                REPO / "code" / target,
            ]
            found = next((c for c in candidates if c.exists()), None)
            if found is None:
                print(f"    [SKIP] file not found: {target}")
                continue
            rc = run_git(["add", target], dry_run=dry)
            if rc != 0:
                failures += 1

        elif verb == "commit":
            msg = a[0]
            if not dry and not has_staged_changes():
                print("    [SKIP] no staged changes; commit skipped")
                continue
            rc = run_git(["commit", "-m", msg], dry_run=dry)
            if rc != 0:
                failures += 1

        elif verb == "push":
            if not dry and not has_unpushed_commits():
                print("    [SKIP] no unpushed commits; push skipped")
                continue
            push_args = a if a else ["origin", "main"]
            rc = run_git(["push"] + push_args, dry_run=dry)
            if rc != 0:
                failures += 1

    print()
    print("=" * 70)
    if failures:
        print(f"  DONE: {failures} command(s) failed")
        return 1
    print("  DONE: all commands succeeded" if not dry else "  DONE: dry-run complete")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())