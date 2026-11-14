#!/usr/bin/env python3
"""patch_v3_6_0_fix_readme.py

README のスイート数とバッジを v3.6.0 用に更新する。
"""
import sys
from pathlib import Path

# code/tools/patches/ から 4 つ上がリポジトリ直下
CODE = Path(__file__).resolve().parent.parent.parent
REPO = CODE.parent   # README.md はリポジトリ直下


REPLACEMENTS = [
    ("Tests-1873%20PASS", "Tests-1887%20PASS"),
    ("1873 PASS", "1887 PASS"),
    ("1873 tests", "1887 tests"),
    ("49 test suites", "51 test suites"),
    ("49 suites", "51 suites"),
]


def main() -> int:
    print(f"repo: {REPO}")
    p = REPO / "README.md"
    if not p.exists():
        print(f"  [error] not found: {p}")
        return 1

    print(f"  [read ] {p}")
    text = p.read_text(encoding="utf-8")
    original = text

    for old, new in REPLACEMENTS:
        if old in text:
            count = text.count(old)
            text = text.replace(old, new)
            print(f"  [repl] '{old}' -> '{new}' ({count} occurrences)")
        else:
            print(f"  [skip] '{old}' not found")

    if text == original:
        print("  [error] no changes made")
        return 1

    bak = p.with_suffix(p.suffix + ".bak_readme_v360")
    bak.write_text(original, encoding="utf-8")
    p.write_text(text, encoding="utf-8")
    print("  [write ] README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())