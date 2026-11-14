"""patch_v3_5_readme_1749.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root
README = ROOT / "README.md"

t = README.read_text(encoding="utf-8")
orig = t

repls = [
    ("Tests-1682%20PASS", "Tests-1749%20PASS"),
    ("- Total: **1682 PASS / 0 FAIL / 2 SKIP** across 47 suites",
     "- Total: **1749 PASS / 0 FAIL / 2 SKIP** across 47 suites"),
    ("- \u2705 **47 test suites, 1682 PASS / 0 FAIL / 2 SKIP**",
     "- \u2705 **47 test suites, 1749 PASS / 0 FAIL / 2 SKIP**"),
    ("Expected: **1682 PASS / 0 FAIL / 2 SKIP** across 47 suites.",
     "Expected: **1749 PASS / 0 FAIL / 2 SKIP** across 47 suites."),
    ("All 47 suites should pass (1682 PASS / 2 SKIP).",
     "All 47 suites should pass (1749 PASS / 2 SKIP)."),
    ("The automated test suite (47 suites, 1682 tests)",
     "The automated test suite (47 suites, 1749 tests)"),
    ("- 47 test suites / **1682 PASS** / 0 FAIL (Python 3.10-3.13).",
     "- 47 test suites / **1749 PASS** / 0 FAIL (Python 3.10-3.13)."),
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
