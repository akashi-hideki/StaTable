"""v3.4.3 doc alignment — Stage A: mechanical replacements.

Automated updates for:
  - 六层架构 -> 七层架构 (and 六層 -> 七層)
  - 23 状態 -> 31 状態
  - 54 Role -> 60 Role
  - Tab references

Structural changes (Driver split) are Stage B: handled separately.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

DOCS = (Path(__file__).resolve().parent.parent.parent
        / "code" / "docs" / "samples")

TARGETS = [
    "LAYER_DESIGN_zh.md",
    "ROLE_FUNCTIONS_zh.md",
    "INSTALL_GUIDE_zh.md",
    "README_zh.md",
]

# Simple 1-to-1 replacements (idempotent when new string already present)
REPLACEMENTS = [
    # Layer count: 6 -> 7
    ("六层架构", "七层架构"),
    ("六層架構", "七層架構"),
    ("六层", "七层"),
    ("六層", "七層"),
    # State count
    ("**23**", "**31**"),
    ("**23 状态**", "**31 状态**"),
    ("-> 六层架构: **23 状态**", "-> 七层架构: **31 状态**"),
    # Role count
    ("54 个 **Role 函数**", "60 个 **Role 函数**"),
    ("54 个 Role 函数参考", "60 个 Role 函数参考"),
    ("初版（54 个 Role 函数参考）", "初版（60 个 Role 函数参考）"),
]


def apply_replacements(path: Path) -> tuple[int, dict]:
    text = path.read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    for old, new in REPLACEMENTS:
        n = text.count(old)
        if n:
            counts[old] = n
            text = text.replace(old, new)
    path.write_text(text, encoding="utf-8", newline="\n")
    return sum(counts.values()), counts


def main() -> int:
    print("=" * 74)
    print("  Stage A: mechanical doc replacements")
    print("=" * 74)

    total = 0
    for fname in TARGETS:
        path = DOCS / fname
        if not path.exists():
            print(f"[MISS] {fname}")
            continue
        n, counts = apply_replacements(path)
        if n == 0:
            print(f"[SKIP] {fname}: nothing to replace")
            continue
        total += n
        print(f"[OK]   {fname}: {n} replacements")
        for old, cnt in counts.items():
            print(f"         '{old}' x {cnt}")

    print()
    print(f"  Total replacements: {total}")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())