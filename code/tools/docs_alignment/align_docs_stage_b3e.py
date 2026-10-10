"""v3.4.3 doc alignment — Stage B-3e: changelog + blank-line fix.

  1. Add v1.1 entry to the changelog table (## 11. 变更历史)
  2. Fix missing blank line before `---` after TOC
"""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "ROLE_FUNCTIONS_zh.md")


def fix_toc_blank_line(text: str) -> tuple[str, bool]:
    """Ensure blank line before `---` after TOC."""
    # Pattern: `11. 变更历史\n---`
    pattern = "11. 变更历史\n---"
    if pattern in text:
        text = text.replace(pattern, "11. 变更历史\n\n---", 1)
        return text, True
    return text, False


def add_changelog_entry(text: str) -> tuple[str, bool]:
    """Add v1.1 entry after v1.0 row in changelog table."""
    if "| 1.1 | 2026-10-10 |" in text:
        return text, False

    # Find "## 11. 变更历史" section
    ch_start = text.find("## 11. 变更历史")
    if ch_start == -1:
        # Try "## 10. 变更历史" (if TOC update didn't affect header yet)
        ch_start = text.find("## 10. 变更历史")
    if ch_start == -1:
        print("[ERR] changelog section not found")
        return text, False

    # Find the v1.0 row in changelog
    lines = text[ch_start:].split("\n")
    found_idx = None
    for i, line in enumerate(lines):
        if "| 1.0 |" in line and "2026-10-04" in line:
            found_idx = i
            break

    if found_idx is None:
        print("[ERR] v1.0 changelog row not found")
        return text, False

    new_row = (
        "| 1.1 | 2026-10-10 | v3.4.3 整備：DriverInput / DriverOutput 分割、"
        "Role 60 個 |"
    )
    lines.insert(found_idx + 1, new_row)
    new_section = "\n".join(lines)
    return text[:ch_start] + new_section, True


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")
    orig = text

    # 1. Fix TOC blank line
    text, ok1 = fix_toc_blank_line(text)
    if ok1:
        print("[OK]   TOC blank line before `---` fixed")
    else:
        print("[SKIP] TOC blank line already OK")

    # 2. Add changelog entry
    text, ok2 = add_changelog_entry(text)
    if ok2:
        print("[OK]   changelog v1.1 entry added")
    else:
        print("[SKIP] changelog v1.1 already present")

    if text == orig:
        print("[SKIP] nothing changed")
        return 0

    DOC.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] ROLE_FUNCTIONS_zh.md: finalized")
    return 0


if __name__ == "__main__":
    sys.exit(main())