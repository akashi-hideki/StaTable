"""patch_v3_5_readme.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"

t = README.read_text(encoding="utf-8")
orig = t

# 1) badge
t = t.replace(
    "Tests-1657%20PASS",
    "Tests-1682%20PASS",
    1,
)

# 2) line 74 (Total)
t = t.replace(
    "- Total: **1657 PASS / 0 FAIL / 2 SKIP** across 46 suites",
    "- Total: **1682 PASS / 0 FAIL / 2 SKIP** across 47 suites",
    1,
)

# 3) line 157
t = t.replace(
    "- \u2705 **46 test suites, 1657 PASS / 0 FAIL / 2 SKIP**",
    "- \u2705 **47 test suites, 1682 PASS / 0 FAIL / 2 SKIP**",
    1,
)

# 4) line 303
t = t.replace(
    "Expected: **1657 PASS / 0 FAIL / 2 SKIP** across 46 suites.",
    "Expected: **1682 PASS / 0 FAIL / 2 SKIP** across 47 suites.",
    1,
)

# 5) line 820
t = t.replace(
    "All 46 suites should pass (1657 PASS / 2 SKIP).",
    "All 47 suites should pass (1682 PASS / 2 SKIP).",
    1,
)

if t == orig:
    raise SystemExit("[FAIL] no changes")

README.write_text(t, encoding="utf-8")
print(f"[OK] {README}")
