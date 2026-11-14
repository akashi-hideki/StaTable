"""show_mypy_context.py

Run mypy and show each error with surrounding context.
Usage: python tools/patches/show_mypy_context.py
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # code/
CTX = 4  # lines before/after


def run_mypy() -> str:
    r = subprocess.run(
        [sys.executable, "-m", "mypy",
         "statable", "statable_gui", "codegen"],
        cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    return (r.stdout or "") + "\n" + (r.stderr or "")


def parse_errors(out: str):
    # Match: path:line: error: message  [code]
    pat = re.compile(
        r"^([^\s:]+\.py):(\d+):\s*error:\s*(.+?)\s+\[([^\]]+)\]\s*$",
        re.MULTILINE,
    )
    return [
        (m.group(1), int(m.group(2)), m.group(3), m.group(4))
        for m in pat.finditer(out)
    ]


def show(path: str, line: int, ctx: int = CTX) -> str:
    p = ROOT / path
    if not p.exists():
        return f"  (file not found: {p})"
    lines = p.read_text(encoding="utf-8").splitlines()
    lo = max(0, line - 1 - ctx)
    hi = min(len(lines), line - 1 + ctx + 1)
    out = []
    for i in range(lo, hi):
        marker = ">>" if i == line - 1 else "  "
        out.append(f"  {marker} {i+1:5d}: {lines[i]}")
    return "\n".join(out)


def main():
    out = run_mypy()
    errors = parse_errors(out)
    # Summary line
    m = re.search(r"Found (\d+) errors? in (\d+) files?", out)
    if m:
        print(f"===== mypy: {m.group(1)} errors in {m.group(2)} files =====\n")
    else:
        print("===== mypy: no summary line found =====\n")

    # Group by file
    from collections import defaultdict
    by_file = defaultdict(list)
    for path, line, msg, code in errors:
        by_file[path].append((line, msg, code))

    for path, items in by_file.items():
        print(f"##### {path} ({len(items)} error(s)) #####")
        for line, msg, code in sorted(items):
            print(f"\n--- L{line}: {msg} [{code}]")
            print(show(path, line))
        print()


if __name__ == "__main__":
    main()
