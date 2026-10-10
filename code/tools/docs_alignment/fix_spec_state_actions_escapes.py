"""Post-process SPEC_STATE_ACTIONS_v1_{en,zh}.md:
   1. Trim JA-only chunk-4 tail (multiple language markers)
   2. Unescape common markdown escapes (Pandoc-style)
   3. Remove standalone-backslash lines
"""
from __future__ import annotations
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent.parent
DOCS = CODE_DIR / "docs"

JA_ONLY_MARKERS = [
    "## Placement Procedure",   # EN
    "## 配置步骤",                 # ZH
]

ESCAPES = [
    ("\\#", "#"), ("\\*", "*"), ("\\_", "_"), ("\\-", "-"),
    ("\\.", "."), ("\\+", "+"), ("\\(", "("), ("\\)", ")"),
    ("\\[", "["), ("\\]", "]"), ("\\`", "`"), ("\\~", "~"),
    ("\\!", "!"), ("\\{", "{"), ("\\}", "}"),
    ("\\<", "<"), ("\\>", ">"), ("\\=", "="),
    ("\\'", "'"), ('\\"', '"'), ("\\;", ";"), ("\\:", ":"),
    ("\\@", "@"), ("\\^", "^"), ("\\&", "&"), ("\\%", "%"),
    ("\\$", "$"),
]


def fix_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")

    # 1. Trim JA-only tail
    trimmed = False
    for marker in JA_ONLY_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            text = text[:idx].rstrip() + "\n"
            print(f"  [{path.name}] trimmed at '{marker}'")
            trimmed = True
            break
    if not trimmed:
        print(f"  [{path.name}] no JA-only marker found")

    # 2. Unescape
    n_escapes = 0
    for old, new in ESCAPES:
        c = text.count(old)
        if c:
            text = text.replace(old, new)
            n_escapes += c

    # 3. Remove standalone-backslash lines
    lines = text.split("\n")
    new_lines = [l for l in lines if l.strip() != "\\"]
    removed = len(lines) - len(new_lines)
    text = "\n".join(new_lines)

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  [{path.name}] {n_escapes} escape(s) fixed, {removed} lone-backslash line(s) removed")
    return 0


def main() -> int:
    print("=" * 74)
    print("  Fix escaping + trim JA-only tail")
    print("=" * 74)
    for name in ("SPEC_STATE_ACTIONS_v1_en.md", "SPEC_STATE_ACTIONS_v1_zh.md"):
        p = DOCS / name
        if p.exists():
            fix_file(p)
        else:
            print(f"[MISS] {p}")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())