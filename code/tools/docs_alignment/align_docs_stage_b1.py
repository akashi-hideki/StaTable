"""v3.4.3 doc alignment — Stage B-1: locate Driver sections.

Extract the exact sections to be split for:
  - LAYER_DESIGN_zh.md  §4.1 Driver 层
  - ROLE_FUNCTIONS_zh.md §3 Driver 层（13 个）
"""
from __future__ import annotations
import sys
from pathlib import Path

DOCS = (Path(__file__).resolve().parent.parent.parent
        / "code" / "docs" / "samples")


def extract_section(path: Path, start_marker: str, max_lines: int = 100):
    """Extract lines from start_marker up to max_lines."""
    if not path.exists():
        print(f"[MISS] {path.name}")
        return
    lines = path.read_text(encoding="utf-8").splitlines()

    start = None
    for i, line in enumerate(lines):
        if start_marker in line:
            start = i
            break

    if start is None:
        print(f"[MISS] '{start_marker}' not found in {path.name}")
        return

    print()
    print("=" * 74)
    print(f"  {path.name}: from L{start + 1}")
    print("=" * 74)
    end = min(len(lines), start + max_lines)
    for i in range(start, end):
        line = lines[i]
        # detect next same-level heading (# or ##)
        if i > start and (line.startswith("## ") or line.startswith("# ")):
            print(f"  [L{i + 1}] {line}   <-- next section (stop)")
            break
        print(f"  [L{i + 1}] {line}")


def main() -> int:
    print("\n" + "#" * 74)
    print("#  LAYER_DESIGN_zh.md - Driver section")
    print("#" * 74)
    extract_section(DOCS / "LAYER_DESIGN_zh.md",
                    "### 4.1 Driver 层", 200)

    print("\n" + "#" * 74)
    print("#  ROLE_FUNCTIONS_zh.md - Driver section")
    print("#" * 74)
    extract_section(DOCS / "ROLE_FUNCTIONS_zh.md",
                    "## 3. Driver 层", 200)

    return 0


if __name__ == "__main__":
    sys.exit(main())