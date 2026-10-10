"""v3.5.0 S-5: update GitHub Actions to Node.js 24 native versions."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
YML = REPO / ".github" / "workflows" / "check.yml"

REPLACEMENTS = [
    ("actions/checkout@v4", "actions/checkout@v5"),
    ("actions/setup-python@v5", "actions/setup-python@v6"),
    ("actions/upload-artifact@v4", "actions/upload-artifact@v5"),
]


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s5_node24")
    print("=" * 70)
    txt = YML.read_text(encoding="utf-8")
    total = 0
    for old, new in REPLACEMENTS:
        n = txt.count(old)
        if n == 0:
            print(f"  [SKIP] {old} not found")
            continue
        txt = txt.replace(old, new)
        total += n
        print(f"  replaced {n}x: {old} -> {new}")
    YML.write_text(txt, encoding="utf-8")
    print(f"  total replacements: {total}")
    print()
    print("[OK] done. Next:")
    print("     1. python -c \"import yaml; yaml.safe_load(open(r'.github/workflows/check.yml', encoding='utf-8').read()); print('YAML OK')\"")
    print("     2. git diff (review)")
    print("     3. git add / commit / push")
    return 0


if __name__ == "__main__":
    sys.exit(main())