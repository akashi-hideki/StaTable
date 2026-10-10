"""v3.4.3 doc alignment — Stage B-3c: renumber chapters after DriverOutput.

Boundary: from `## 4. MwMicrowave 层（6 个）` onwards.

Renumber (per-line, single pass, +1 for N >= 4):
  ## 4.  -> ## 5.
  ## 5.  -> ## 6.
  ...
  ## 10. -> ## 11.
  ### 4.X -> ### 5.X
  ### 5.X -> ### 6.X
  ...
  ### 10.X -> ### 11.X
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "ROLE_FUNCTIONS_zh.md")

BOUNDARY = "## 4. MwMicrowave 层（6 个）"


def renumber_line(line: str) -> tuple[str, int]:
    """Renumber one line if it's a ## N. or ### N.M heading (N >= 4)."""
    m = re.match(r"^## (\d+)\. ", line)
    if m:
        old_n = int(m.group(1))
        if old_n >= 4:
            new_n = old_n + 1
            return line.replace(f"## {old_n}. ", f"## {new_n}. ", 1), 1
        return line, 0

    m = re.match(r"^### (\d+)\.(\d+) ", line)
    if m:
        old_n = int(m.group(1))
        if old_n >= 4:
            new_n = old_n + 1
            return line.replace(f"### {old_n}.", f"### {new_n}.", 1), 1
        return line, 0

    return line, 0


def renumber_tail(tail: str) -> tuple[str, int]:
    lines = tail.split("\n")
    total = 0
    for i, line in enumerate(lines):
        new_line, n = renumber_line(line)
        if n:
            lines[i] = new_line
            total += n
    return "\n".join(lines), total


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")

    # Idempotency check
    if "## 5. MwMicrowave 层（6 个）" in text and "## 4. MwMicrowave 层（6 个）" not in text:
        print("[SKIP] already renumbered")
        return 0

    idx = text.find(BOUNDARY)
    if idx == -1:
        print(f"[ERR] boundary not found: {BOUNDARY!r}")
        return 1

    head = text[:idx]
    tail = text[idx:]

    tail, count = renumber_tail(tail)
    print(f"  [renumber] {count} lines changed")

    text = head + tail
    DOC.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] ROLE_FUNCTIONS_zh.md: chapter renumbering complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())