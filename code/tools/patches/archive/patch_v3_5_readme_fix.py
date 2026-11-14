"""patch_v3_5_readme_fix.py"""
from __future__ import annotations
from pathlib import Path

# NOTE: README.md lives at repo root, one level above code/
#       patch file is at code/tools/patches/, so parents[3] = repo root
ROOT = Path(__file__).resolve().parents[3]
README = ROOT / "README.md"

if not README.exists():
    raise SystemExit(f"[FAIL] README not found: {README}")

t = README.read_text(encoding="utf-8")
orig = t

repls = [
    ("Tests-1657%20PASS", "Tests-1682%20PASS"),
    ("- Total: **1657 PASS / 0 FAIL / 2 SKIP** across 46 suites",
     "- Total: **1682 PASS / 0 FAIL / 2 SKIP** across 47 suites"),
    ("- \u2705 **46 test suites, 1657 PASS / 0 FAIL / 2 SKIP**",
     "- \u2705 **47 test suites, 1682 PASS / 0 FAIL / 2 SKIP**"),
    ("Expected: **1657 PASS / 0 FAIL / 2 SKIP** across 46 suites.",
     "Expected: **1682 PASS / 0 FAIL / 2 SKIP** across 47 suites."),
    ("All 46 suites should pass (1657 PASS / 2 SKIP).",
     "All 47 suites should pass (1682 PASS / 2 SKIP)."),
]

counts = []
for old, new in repls:
    n = t.count(old)
    counts.append(n)
    t = t.replace(old, new)

print(f"[INFO] replacements: {counts}")

if t == orig:
    raise SystemExit("[FAIL] no changes")

README.write_text(t, encoding="utf-8")
print(f"[OK] {README}")
