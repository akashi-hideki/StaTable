"""patch_v3_5_readme_l211.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
README = ROOT / "README.md"
t = README.read_text(encoding="utf-8")

OLD = "**Note for Linux users**: The automated test suite (46 suites, 1168 tests)\n"
NEW = "**Note for Linux users**: The automated test suite (47 suites, 1682 tests)\n"

n = t.count(OLD)
if n != 1:
    raise SystemExit(f"[FAIL] anchor count={n}")

README.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
print(f"[OK] {README}")
