#!/usr/bin/env python3
# code/tools/git_runner.py
"""Execute Git operations from a plain-text script file.

See tools/git_ops.txt for the script syntax.

Usage:
    python tools/git_runner.py                 # uses tools/git_ops.txt
    python tools/git_runner.py --file my.txt
    python tools/git_runner.py --dry-run
    python tools/git_runner.py --yes
    python tools/git_runner.py --continue-on-error
    python tools/git_runner.py --list
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_OPS_FILE = Path(__file__).resolve().parent / "git_ops.txt"
DEFAULT_REMOTE = "origin"
DEFAULT_BRANCH = "main"


# ----------------------------------------------------------------------
# Script parser
# ----------------------------------------------------------------------
class Command:
    def __init__(self, kind, args, raw_line, line_no):
        self.kind = kind
        self.args = args
        self.raw_line = raw_line
        self.line_no = line_no


def parse_script(text: str):
    lines = text.splitlines()
    commands = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        i += 1

        if not stripped or stripped.startswith("#"):
            continue

        if stripped == "commit-begin":
            body_lines = []
            start_line = i
            while i < len(lines):
                if lines[i].strip() == "commit-end":
                    i += 1
                    break
                body_lines.append(lines[i])
                i += 1
            else:
                raise ValueError(
                    f"line {start_line}: 'commit-begin' without "
                    f"matching 'commit-end'")
            commands.append(Command(
                "commit", ["\n".join(body_lines)],
                f"commit-begin ... commit-end (line {start_line})",
                start_line))
            continue

        parts = stripped.split(None, 1)
        kind = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        commands.append(Command(kind, [rest] if rest else [],
                                stripped, i))
    return commands


# ----------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------
class GitRunner:
    def __init__(self, repo_root: Path, dry_run: bool,
                 assume_yes: bool, continue_on_error: bool):
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.assume_yes = assume_yes
        self.continue_on_error = continue_on_error
        self.failed = 0

    def _run(self, args, show_output=True):
        printable = "git " + " ".join(shlex.quote(a) for a in args)
        print(f"  $ {printable}")
        if self.dry_run:
            return 0
        try:
            proc = subprocess.run(
                ["git"] + args, cwd=str(self.repo_root),
                text=True, encoding="utf-8", errors="replace",
                capture_output=True)
        except FileNotFoundError:
            print("  [ERROR] git not found in PATH")
            return 127
        if proc.stdout and show_output:
            print(proc.stdout.rstrip())
        if proc.stderr:
            print(proc.stderr.rstrip())
        return proc.returncode

    # ---- commands ----
    def cmd_status(self, args):
        return self._run(["status"])

    def cmd_branch(self, args):
        return self._run(["branch", "-vv"])

    def cmd_log(self, args):
        n = 5
        if args and args[0].strip().isdigit():
            n = int(args[0].strip())
        return self._run(["log", "--oneline", f"-{n}"])

    def cmd_diff(self, args):
        extra = shlex.split(args[0]) if args else []
        return self._run(["diff"] + extra)

    def cmd_show(self, args):
        ref = args[0].strip() if args else "HEAD"
        return self._run(["show", "--stat", ref])

    def cmd_add(self, args):
        if not args:
            print("  [ERROR] 'add' requires a path")
            return 1
        return self._run(["add"] + shlex.split(args[0]))

    def cmd_add_all(self, args):
        return self._run(["add", "-A"])

    def cmd_reset(self, args):
        if not args:
            print("  [ERROR] 'reset' requires a path")
            return 1
        return self._run(["reset"] + shlex.split(args[0]))

    def cmd_reset_hard(self, args):
        ref = args[0].strip() if args else "HEAD"
        if not self.assume_yes:
            ans = input(
                f"  reset --hard {ref} will DISCARD changes. "
                f"Continue? [y/N] ").strip().lower()
            if ans != "y":
                print("  aborted by user")
                return 1
        return self._run(["reset", "--hard", ref])

    def cmd_checkout(self, args):
        if not args:
            print("  [ERROR] 'checkout' requires a branch")
            return 1
        return self._run(["checkout", args[0].strip()])

    def cmd_fetch(self, args):
        return self._run(["fetch", "--all", "--prune"])

    def cmd_pull(self, args):
        remote, branch = DEFAULT_REMOTE, DEFAULT_BRANCH
        if args:
            parts = args[0].split()
            if len(parts) >= 1: remote = parts[0]
            if len(parts) >= 2: branch = parts[1]
        return self._run(["pull", remote, branch])

    def cmd_push(self, args):
        remote, branch = DEFAULT_REMOTE, DEFAULT_BRANCH
        if args:
            parts = args[0].split()
            if len(parts) >= 1: remote = parts[0]
            if len(parts) >= 2: branch = parts[1]
        return self._run(["push", remote, branch])

    def cmd_commit_msg(self, args):
        if not args or not args[0].strip():
            print("  [ERROR] 'commit-msg' requires a subject")
            return 1
        return self._run(["commit", "-m", args[0].strip()])

    def cmd_commit(self, args):
        if not args or not args[0].strip():
            print("  [ERROR] commit with empty message")
            return 1
        msg = args[0]
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".txt",
            delete=False, newline="\n") as f:
            f.write(msg)
            path = f.name
        try:
            return self._run(["commit", "-F", path])
        finally:
            try: os.unlink(path)
            except OSError: pass

    def cmd_run(self, args):
        if not args:
            print("  [ERROR] 'run' requires a git subcommand")
            return 1
        return self._run(shlex.split(args[0]))

    def cmd_pause(self, args):
        if self.dry_run:
            return 0
        input("  -- press Enter to continue --")
        return 0

    def cmd_abort(self, args):
        print("  script requested abort")
        return -1


HANDLERS = {
    "status": "cmd_status", "branch": "cmd_branch",
    "log": "cmd_log", "diff": "cmd_diff", "show": "cmd_show",
    "add": "cmd_add", "add-all": "cmd_add_all",
    "reset": "cmd_reset", "reset-hard": "cmd_reset_hard",
    "checkout": "cmd_checkout", "fetch": "cmd_fetch",
    "pull": "cmd_pull", "push": "cmd_push",
    "commit-msg": "cmd_commit_msg", "commit": "cmd_commit",
    "run": "cmd_run", "pause": "cmd_pause", "abort": "cmd_abort",
}


def find_repo_root() -> Path:
    here = Path.cwd().resolve()
    for p in [here, *here.parents]:
        if (p / ".git").is_dir():
            return p
    return here


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default=str(DEFAULT_OPS_FILE))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--continue-on-error", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    ops_path = Path(args.file).resolve()
    if not ops_path.is_file():
        print(f"ERROR: script not found: {ops_path}", file=sys.stderr)
        return 2

    text = ops_path.read_text(encoding="utf-8")
    try:
        commands = parse_script(text)
    except ValueError as e:
        print(f"ERROR parsing script: {e}", file=sys.stderr)
        return 2

    print("=" * 70)
    print("  Git Runner")
    print("=" * 70)
    print(f"  Script: {ops_path}")
    print(f"  Repo:   {find_repo_root()}")
    print(f"  Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print(f"  Total:  {len(commands)} command(s)")
    print("=" * 70)
    print()

    if args.list:
        for i, c in enumerate(commands, 1):
            print(f"  [{i:2d}] {c.kind:12s} {c.raw_line}")
        return 0

    runner = GitRunner(
        repo_root=find_repo_root(),
        dry_run=args.dry_run,
        assume_yes=args.yes,
        continue_on_error=args.continue_on_error)

    for i, cmd in enumerate(commands, 1):
        print()
        print("-" * 70)
        print(f"  [{i}/{len(commands)}] {cmd.kind}: {cmd.raw_line}")
        print("-" * 70)
        handler_name = HANDLERS.get(cmd.kind)
        if handler_name is None:
            print(f"  [ERROR] unknown command: {cmd.kind!r}")
            runner.failed += 1
            if not args.continue_on_error:
                return 1
            continue
        rc = getattr(runner, handler_name)(cmd.args)
        if rc == -1:
            print("  stop requested")
            break
        if rc != 0:
            runner.failed += 1
            if not args.continue_on_error:
                print()
                print(f"  [STOP] command failed (exit {rc})")
                return 1

    print()
    print("=" * 70)
    if runner.failed == 0:
        print("  DONE: all commands succeeded")
    else:
        print(f"  DONE: {runner.failed} command(s) failed")
    print("=" * 70)
    return 0 if runner.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())