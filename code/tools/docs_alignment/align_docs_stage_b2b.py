"""v3.4.3 doc alignment — Stage B-2b (v2): renumber headings only.

Fixes:
  - Regex group reference `\14` issue -> use \g<1>
  - Skip TOC handling (separate Stage B-2c)

Renumbers ### and #### headings in the tail (from `### 4.2 MwMicrowave 层`):
  4.2 -> 4.3
  4.3 -> 4.4
  4.4 -> 4.5
  4.5 -> 4.6
  4.6 -> 4.7
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "LAYER_DESIGN_zh.md")

BOUNDARY = "### 4.2 MwMicrowave 层"


def renumber_headings(text: str) -> tuple[str, int]:
    """Renumber `### 4.X ...` or `#### 4.X.Y ...` (X in 2..6) -> X+1."""
    total = 0
    # Process highest first to avoid collisions
    for old_n, new_n in [(6, 7), (5, 6), (4, 5), (3, 4), (2, 3)]:
        old_str = f"4.{old_n}"
        new_str = f"4.{new_n}"
        pattern = rf"^(#{{3,4}}) {re.escape(old_str)}\b"
        # Use lambda to avoid \g issues entirely
        text, n = re.subn(
            pattern,
            lambda m, new_str=new_str: f"{m.group(1)} {new_str}",
            text,
            flags=re.MULTILINE,
        )
        total += n
    return text, total


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")

    # Idempotency: already renumbered?
    if "### 4.3 MwMicrowave 层" in text and "### 4.2 MwMicrowave 层" not in text:
        print("[SKIP] headings already renumbered")
        return 0

    idx = text.find(BOUNDARY)
    if idx == -1:
        print(f"[ERR] boundary not found: {BOUNDARY!r}")
        return 1

    head = text[:idx]
    tail = text[idx:]

    tail, h_count = renumber_headings(tail)
    print(f"  [headings] {h_count} replacements in tail")

    text = head + tail
    DOC.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] LAYER_DESIGN_zh.md: heading renumbering complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())