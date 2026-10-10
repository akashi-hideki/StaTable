"""Rename SPEC_STATE_ACTIONS_v1.md -> _ja.md and update references."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Files to update (path, old_string, new_string)
PATCHES = [
    (ROOT / "code" / "docs" / "SPEC_OVERVIEW_ja.md",
     "SPEC_STATE_ACTIONS_v1.md",
     "SPEC_STATE_ACTIONS_v1_ja.md"),
    (ROOT / "code" / "tests" / "test_readme_consistency.py",
     "SPEC_STATE_ACTIONS_v1.md",
     "SPEC_STATE_ACTIONS_v1_ja.md"),
    (ROOT / "code" / "tools" / "patches" / "patch_v3_4_0_readme_section.py",
     "SPEC_STATE_ACTIONS_v1.md",
     "SPEC_STATE_ACTIONS_v1_ja.md"),
]


def main() -> int:
    for path, old, new in PATCHES:
        if not path.exists():
            print(f"[MISS] {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        if old not in text:
            print(f"[SKIP] {path.name}: '{old}' not found")
            continue
        n = text.count(old)
        text = text.replace(old, new)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"[OK]   {path.name}: {n} replacement(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())