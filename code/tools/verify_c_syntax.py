#!/usr/bin/env python3
# code/tools/verify_c_syntax.py
"""Compile-verify generated C code with gcc and/or arm-none-eabi-gcc.

Usage:
    python tools/verify_c_syntax.py --root output
    python tools/verify_c_syntax.py --root output --compiler both
    python tools/verify_c_syntax.py --root output --log my_report.log

Evidence logging:
    By default, a timestamped log is written to `verify_report/`:
        verify_report/verify_c_syntax_YYYYMMDD_HHMMSS.log
    The log contains environment info, git commit, command line,
    target layout, per-compiler results, and the final verdict.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import platform
import shutil
import socket
import subprocess
import sys
from collections import Counter
from pathlib import Path


TOOLCHAINS = {
    "gcc": {"cc": "gcc", "extra_flags": []},
    "arm": {"cc": "arm-none-eabi-gcc",
            "extra_flags": ["-mcpu=cortex-m4", "-mthumb"]},
}


# ----------------------------------------------------------------------
# Logger: print to stdout AND write to file simultaneously
# ----------------------------------------------------------------------
class Logger:
    def __init__(self, log_path: Path | None):
        self.log_path = log_path
        self._fh = None
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(log_path, "w", encoding="utf-8", newline="\n")

    def write(self, text: str = "") -> None:
        print(text)
        if self._fh is not None:
            self._fh.write(text + "\n")

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None


# ----------------------------------------------------------------------
# Environment collection
# ----------------------------------------------------------------------
def run_capture(cmd: list[str], timeout: int = 10) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=timeout)
        return (p.stdout or p.stderr or "").strip()
    except Exception as e:
        return f"(failed: {e})"


def get_git_info(cwd: Path) -> tuple[str, str, str]:
    """Return (commit_hash, branch, status) or placeholders."""
    try:
        commit = run_capture(
            ["git", "-C", str(cwd), "rev-parse", "--short", "HEAD"])
        branch = run_capture(
            ["git", "-C", str(cwd), "rev-parse", "--abbrev-ref", "HEAD"])
        status_raw = run_capture(
            ["git", "-C", str(cwd), "status", "--porcelain"])
        status = "clean" if not status_raw else f"dirty ({len(status_raw.splitlines())} changes)"
        if not commit or commit.startswith("(failed"):
            return ("(no git)", "(no git)", "(no git)")
        return (commit, branch, status)
    except Exception:
        return ("(error)", "(error)", "(error)")


def get_compiler_version(cc_path: str | None) -> str:
    if cc_path is None:
        return "(not installed)"
    out = run_capture([cc_path, "--version"])
    return out.splitlines()[0] if out else "(unknown)"


# ----------------------------------------------------------------------
# Layout discovery
# ----------------------------------------------------------------------
def discover_layout(root: Path) -> dict:
    layout = {"include_dirs": [], "c_files": [], "h_files": []}
    for p in root.rglob("*.h"):
        layout["h_files"].append(p)
        if p.parent not in layout["include_dirs"]:
            layout["include_dirs"].append(p.parent)
    layout["c_files"] = sorted(root.rglob("*.c"))
    return layout


# ----------------------------------------------------------------------
# Compile one
# ----------------------------------------------------------------------
def compile_one(cc, std, strict, include_dirs, src, extra_flags):
    cmd = [cc, f"-std={std}", "-fsyntax-only", "-Wall", "-Wextra"]
    cmd.extend(extra_flags)
    if strict:
        cmd.append("-Werror")
    for inc in include_dirs:
        cmd.extend(["-I", str(inc)])
    cmd.append(str(src))
    proc = subprocess.run(
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout, proc.stderr


# ----------------------------------------------------------------------
# Header / footer
# ----------------------------------------------------------------------
def write_header(log: Logger, args, root: Path,
                 layout: dict, out: dict) -> None:
    sep = "=" * 78
    log.write(sep)
    log.write("  C Syntax Verification Report")
    log.write(sep)
    log.write(f"  Timestamp:      {out['timestamp']}")
    log.write(f"  Hostname:       {out['hostname']}")
    log.write(f"  Platform:       {out['platform']}")
    log.write(f"  Python:         {out['python']}")
    log.write(f"  Working dir:    {Path.cwd()}")
    log.write(f"  Target root:    {root.resolve()}")
    log.write(f"  Git commit:     {out['git_commit']} "
              f"(branch: {out['git_branch']})")
    log.write(f"  Git status:     {out['git_status']}")
    log.write(f"  Command:        {' '.join(sys.argv)}")
    log.write("")
    log.write(f"  C files:        {len(layout['c_files'])}")
    log.write(f"  H files:        {len(layout['h_files'])}")
    log.write(f"  Include dirs:   {len(layout['include_dirs'])}")
    for d in layout["include_dirs"]:
        log.write(f"    - {d}")
    log.write("")
    log.write("  Source files:")
    for f in layout["c_files"]:
        log.write(f"    - {f.relative_to(root)}")
    log.write(sep)
    log.write("")


def write_footer(log: Logger, summary: dict, log_path: Path | None) -> None:
    sep = "=" * 78
    log.write("")
    log.write(sep)
    log.write("  Summary")
    log.write(sep)
    for cname, s in summary["per_compiler"].items():
        if s["skipped"]:
            log.write(f"  {cname:8s} SKIPPED  ({s['reason']})")
        elif s["ok"] == s["total"]:
            log.write(f"  {cname:8s} PASS     ({s['ok']}/{s['total']})")
        else:
            log.write(f"  {cname:8s} FAIL     "
                      f"({s['ok']}/{s['total']}, {s['total']-s['ok']} failed)")
    log.write("")
    log.write(f"  Overall:  {summary['verdict']}")
    log.write(sep)
    if log_path is not None:
        log.write(f"  Log saved to: {log_path.resolve()}")
        log.write(sep)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="output")
    ap.add_argument("--compiler", default="gcc",
                    choices=["gcc", "arm", "both"])
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--std", default="c99")
    ap.add_argument("--show-warnings", action="store_true")
    ap.add_argument("--log", default=None,
                    help="log file path (default: auto-named under "
                         "verify_report/)")
    ap.add_argument("--no-log", action="store_true",
                    help="disable log file output")
    args = ap.parse_args()

    # ---- resolve log path ----
    if args.no_log:
        log_path = None
    elif args.log:
        log_path = Path(args.log)
    else:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = Path("verify_report") / f"verify_c_syntax_{ts}.log"

    log = Logger(log_path)

    try:
        # ---- environment ----
        out = {
            "timestamp": _dt.datetime.now().astimezone().strftime(
                "%Y-%m-%d %H:%M:%S %Z"),
            "hostname": socket.gethostname(),
            "platform": f"{platform.system()} {platform.release()} "
                        f"({platform.machine()})",
            "python": sys.version.split()[0],
        }
        git_commit, git_branch, git_status = get_git_info(Path.cwd())
        out["git_commit"] = git_commit
        out["git_branch"] = git_branch
        out["git_status"] = git_status

        # ---- layout ----
        root = Path(args.root)
        if not root.is_dir():
            log.write(f"ERROR: {root} not found")
            return 1
        layout = discover_layout(root)
        if not layout["c_files"]:
            log.write(f"ERROR: no .c files under {root}")
            return 1

        write_header(log, args, root, layout, out)

        # ---- compilers ----
        compilers = (["gcc", "arm"] if args.compiler == "both"
                     else [args.compiler])
        summary = {"per_compiler": {}, "verdict": "ALL PASS"}
        overall_rc = 0

        for cname in compilers:
            sep = "=" * 78
            log.write(sep)
            log.write(f"  Compiler: {cname}")
            log.write(sep)

            cc_path = shutil.which(TOOLCHAINS[cname]["cc"])
            if cc_path is None:
                log.write(f"  Status:   SKIPPED "
                          f"({TOOLCHAINS[cname]['cc']} not found in PATH)")
                log.write("")
                summary["per_compiler"][cname] = {
                    "ok": 0, "total": len(layout["c_files"]),
                    "skipped": True,
                    "reason": f"{TOOLCHAINS[cname]['cc']} not found",
                }
                overall_rc = max(overall_rc, 2)
                continue

            cc_version = get_compiler_version(cc_path)
            log.write(f"  Path:     {cc_path}")
            log.write(f"  Version:  {cc_version}")
            log.write(f"  Flags:    -std={args.std} -Wall -Wextra"
                      + (" -Werror" if args.strict else ""))
            log.write(f"  Files:    {len(layout['c_files'])}")
            log.write("")

            ok = 0
            ng = 0
            warning_counter: Counter = Counter()
            errors: list[tuple[Path, str]] = []

            for src in layout["c_files"]:
                rc, out_s, err_s = compile_one(
                    cc_path, args.std, args.strict,
                    layout["include_dirs"], src,
                    TOOLCHAINS[cname]["extra_flags"])
                if rc == 0:
                    ok += 1
                    for line in err_s.splitlines():
                        if ": warning:" in line:
                            if "[" in line and "]" in line:
                                name = line[line.rfind("[") + 1:
                                            line.rfind("]")]
                                warning_counter[name] += 1
                else:
                    ng += 1
                    errors.append((src, err_s or out_s))
                    log.write(f"  [FAIL] {src.relative_to(root)}")

            log.write("")
            log.write(f"  Result:   {ok} OK / {ng} FAIL "
                      f"(total {len(layout['c_files'])})")

            if warning_counter:
                log.write("")
                log.write(f"  Warnings ({sum(warning_counter.values())}):")
                for name, count in warning_counter.most_common():
                    log.write(f"    {count:4d}  {name}")

            if errors:
                log.write("")
                log.write("  Error details (first 5 files):")
                for src, msg in errors[:5]:
                    log.write("")
                    log.write(f"  --- {src.relative_to(root)} ---")
                    for line in msg.splitlines()[:20]:
                        log.write(f"    {line}")
                if len(errors) > 5:
                    log.write("")
                    log.write(f"  ... and {len(errors) - 5} more file(s)")
            log.write("")

            summary["per_compiler"][cname] = {
                "ok": ok, "total": len(layout["c_files"]),
                "skipped": False,
            }
            if ng > 0:
                overall_rc = 1

        # ---- verdict ----
        if overall_rc == 0:
            summary["verdict"] = "ALL PASS"
        elif overall_rc == 2:
            summary["verdict"] = "SOME COMPILERS MISSING"
        else:
            summary["verdict"] = "FAILURES DETECTED"

        write_footer(log, summary, log_path)

        return overall_rc

    finally:
        log.close()


if __name__ == "__main__":
    sys.exit(main())