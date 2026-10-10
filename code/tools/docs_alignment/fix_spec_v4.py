"""Fix SPEC_STATE_ACTIONS EN/ZH formatting (v4 — exact-string).

Targets (exact replacements):
  1. §6.5: `        {\n\n```\n\n            EVENT_Driver_t` ->
           `        {\n            EVENT_Driver_t`
  2. §9.1: `Preserved |\n\n```\n### 9.2 XML` ->
           `Preserved |\n\n### 9.2 XML`
"""
from __future__ import annotations
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent.parent / "docs"

OLD_65 = "        {\n\n```\n\n            EVENT_Driver_t"
NEW_65 = "        {\n            EVENT_Driver_t"

OLD_91 = "| Preserved |\n\n```\n### 9.2 XML"
NEW_91 = "| Preserved |\n\n### 9.2 XML"

# Alternative patterns (Chinese variant / minor variations)
OLD_91_ALT = "| 维持 |\n\n```\n### 9.2 XML"
NEW_91_ALT = "| 维持 |\n\n### 9.2 XML"


def fix_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    orig = text
    n1 = n2 = n3 = 0

    if OLD_65 in text:
        n1 = text.count(OLD_65)
        text = text.replace(OLD_65, NEW_65)
        print(f"  [{path.name}] 6.5 fixed: {n1}")
    else:
        print(f"  [{path.name}] 6.5 pattern NOT found")

    if OLD_91 in text:
        n2 = text.count(OLD_91)
        text = text.replace(OLD_91, NEW_91)
        print(f"  [{path.name}] 9.1 (EN) fixed: {n2}")
    if OLD_91_ALT in text:
        n3 = text.count(OLD_91_ALT)
        text = text.replace(OLD_91_ALT, NEW_91_ALT)
        print(f"  [{path.name}] 9.1 (ZH) fixed: {n3}")

    if not (n1 or n2 or n3):
        print(f"  [{path.name}] no changes applied")
        return

    text = text.rstrip() + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] {path.name}: {path.stat().st_size} bytes, "
          f"{len(text.splitlines())} lines")


def main() -> int:
    for name in ("SPEC_STATE_ACTIONS_v1_en.md", "SPEC_STATE_ACTIONS_v1_zh.md"):
        p = DOCS / name
        if p.exists():
            fix_file(p)
        else:
            print(f"[MISS] {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())