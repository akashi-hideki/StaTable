"""patch_readme_1873.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
README = ROOT / "README.md"
t = README.read_text(encoding="utf-8")
orig = t

repls = [
    ("Tests-1793%20PASS", "Tests-1873%20PASS"),
    ("- Total: **1793 PASS / 0 FAIL / 2 SKIP** across 48 suites",
     "- Total: **1873 PASS / 0 FAIL / 2 SKIP** across 49 suites"),
    ("- \u2705 **48 test suites, 1793 PASS / 0 FAIL / 2 SKIP**",
     "- \u2705 **49 test suites, 1873 PASS / 0 FAIL / 2 SKIP**"),
    ("Expected: **1793 PASS / 0 FAIL / 2 SKIP** across 48 suites.",
     "Expected: **1873 PASS / 0 FAIL / 2 SKIP** across 49 suites."),
    ("All 48 suites should pass (1793 PASS / 2 SKIP).",
     "All 49 suites should pass (1873 PASS / 2 SKIP)."),
    ("The automated test suite (48 suites, 1793 tests)",
     "The automated test suite (49 suites, 1873 tests)"),
    ("- 48 test suites / **1793 PASS** / 0 FAIL (Python 3.10-3.13).",
     "- 49 test suites / **1873 PASS** / 0 FAIL (Python 3.10-3.13)."),
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
