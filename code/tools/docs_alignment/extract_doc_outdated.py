"""Extract outdated strings from docs for alignment planning."""
from __future__ import annotations
import re
from pathlib import Path

DOCS = Path(r"C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code\docs\samples")

TARGETS = [
    "LAYER_DESIGN_zh.md",
    "ROLE_FUNCTIONS_zh.md",
    "INSTALL_GUIDE_zh.md",
    "README_zh.md",
]

# 修正対象パターン
PATTERNS = {
    "6層/六層": r"六層|6\s*層|六层|6\s*层",
    "23状態": r"\b23\b",
    "54 Role": r"\b54\b",
    "Driver 単一": r"^.*\bDriver\b.*$",
    "MwMicrowave 3状態": r"MwMicrowave.*3\s*状態",
    "MwSteam 3状態": r"MwSteam.*3\s*状態",
}


def main() -> int:
    for fname in TARGETS:
        path = DOCS / fname
        if not path.exists():
            print(f"[MISS] {fname}")
            continue

        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        print()
        print("=" * 74)
        print(f"  {fname}")
        print("=" * 74)

        for label, pat in PATTERNS.items():
            hits = []
            for i, line in enumerate(lines, 1):
                if re.search(pat, line):
                    hits.append((i, line.strip()[:100]))
            if hits:
                print(f"\n  [{label}]  {len(hits)} hits")
                for ln, content in hits[:5]:
                    print(f"    L{ln}: {content}")
                if len(hits) > 5:
                    print(f"    ... and {len(hits) - 5} more")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())