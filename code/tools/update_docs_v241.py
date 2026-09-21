#!/usr/bin/env python3
"""Update SPEC_OVERVIEW and README for v2.4.1 (merge test suite).

Targets:
  - code/docs/SPEC_OVERVIEW_ja.md : 13 -> 14 suites, 551 -> 576 PASS
  - code/docs/SPEC_OVERVIEW_en.md : same
  - README.md (repo root)         : badge 551 -> 576, Roadmap v2.4.1

Usage:
    python tools/update_docs_v241.py             # dry-run
    python tools/update_docs_v241.py --apply
    python tools/update_docs_v241.py --repo-root ..   # default
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


# ======================================================================
# SPEC_OVERVIEW_ja.md patches
# ======================================================================
JA_OLD_TEST_LINE = (
    "| テスト | 13スイート（`tests/test_v2_2_p*.py` + "
    "`tests/test_v2_3_p1.py`）、551 PASS / 2 SKIP |"
)
JA_NEW_TEST_LINE = (
    "| テスト | 14スイート（`tests/test_v2_2_p*.py` + "
    "`tests/test_v2_3_p1.py` + `tests/test_v2_4_p1_merge.py`）、"
    "576 PASS / 2 SKIP |"
)

JA_OLD_TOTAL = "**合計**：**551 PASS / 0 FAIL / 2 SKIP**"
JA_NEW_TOTAL = "**合計**：**576 PASS / 0 FAIL / 2 SKIP**"

JA_OLD_SUITE_LAST = (
    "| `test_v2_3_p1.py` | 新規プロジェクト（v2.3） | 14 PASS / 0 FAIL |\n"
)
JA_NEW_SUITE_LAST = (
    JA_OLD_SUITE_LAST
    + "| `test_v2_4_p1_merge.py` | コードマージ（v2.4.1） | 25 PASS / 0 FAIL |\n"
)

JA_OLD_REV = (
    "| 2.4 | 2026-09-22 | UI 整理・予約フィールド・Namespace コンボ対応： |\n"
)
JA_NEW_REV = (
    "| 2.4.1 | 2026-09-22 | マージ冪等性修正 + テスト追加： |\n"
    "| | | - `code_merger.py` v2.1: マージ非冪等性バグ修正（マーカー毎に +1 改行） |\n"
    "| | | - `role_function_generator.py` v3.3.1: 誤検知警告を抑制 |\n"
    "| | | - `tests/test_v2_4_p1_merge.py`: 9グループ / 25アサーション追加 |\n"
    "| | | - テストスイート 13 → 14、551 → 576 PASS / 2 SKIP |\n"
    "| 2.4 | 2026-09-22 | UI 整理・予約フィールド・Namespace コンボ対応： |\n"
)


# ======================================================================
# SPEC_OVERVIEW_en.md patches
# ======================================================================
EN_OLD_TEST_LINE = (
    "| Testing | 13 suites (`tests/test_v2_2_p*.py` + "
    "`tests/test_v2_3_p1.py`), 551 PASS / 2 SKIP |"
)
EN_NEW_TEST_LINE = (
    "| Testing | 14 suites (`tests/test_v2_2_p*.py` + "
    "`tests/test_v2_3_p1.py` + `tests/test_v2_4_p1_merge.py`), "
    "576 PASS / 2 SKIP |"
)

EN_OLD_TOTAL = "**Total**: **551 PASS / 0 FAIL / 2 SKIP**"
EN_NEW_TOTAL = "**Total**: **576 PASS / 0 FAIL / 2 SKIP**"

EN_OLD_SUITE_LAST = (
    "| `test_v2_3_p1.py` | New Project (v2.3) | 14 PASS / 0 FAIL |\n"
)
EN_NEW_SUITE_LAST = (
    EN_OLD_SUITE_LAST
    + "| `test_v2_4_p1_merge.py` | Code merge (v2.4.1) | 25 PASS / 0 FAIL |\n"
)

EN_OLD_REV = (
    "| 2.4 | 2026-09-22 | UI cleanup / reserved fields / namespace combo: |\n"
)
EN_NEW_REV = (
    "| 2.4.1 | 2026-09-22 | Merge idempotency fix + test suite: |\n"
    "| | | - `code_merger.py` v2.1: idempotency fix (each merge added +1 newline per marker) |\n"
    "| | | - `role_function_generator.py` v3.3.1: silence false-positive warnings |\n"
    "| | | - `tests/test_v2_4_p1_merge.py`: 9 groups / 25 assertions |\n"
    "| | | - Test suites 13 -> 14, 551 -> 576 PASS / 2 SKIP |\n"
    "| 2.4 | 2026-09-22 | UI cleanup / reserved fields / namespace combo: |\n"
)


# ======================================================================
# README.md patches
# ======================================================================
README_OLD_BADGE = (
    "[![Tests](https://img.shields.io/badge/Tests-551%20PASS-green.svg)]()"
)
README_NEW_BADGE = (
    "[![Tests](https://img.shields.io/badge/Tests-576%20PASS-green.svg)]()"
)

README_OLD_EXPECTED = (
    "Expected: **551 PASS / 0 FAIL / 2 SKIP** across 13 suites."
)
README_NEW_EXPECTED = (
    "Expected: **576 PASS / 0 FAIL / 2 SKIP** across 14 suites."
)

README_OLD_KEYFEAT = (
    "- ✅ **13 test suites, 551 PASS / 0 FAIL / 2 SKIP**"
)
README_NEW_KEYFEAT = (
    "- ✅ **14 test suites, 576 PASS / 0 FAIL / 2 SKIP**"
)

README_OLD_ROADMAP = (
    "### v2.4 (Current — Released 2026-09-22)\n"
)
README_NEW_ROADMAP = (
    "### v2.4.1 (Current — Released 2026-09-22)\n"
    "\n"
    "- ✅ Merge idempotency fix (`code_merger.py` v2.1)\n"
    "- ✅ False-positive warning fix (`role_function_generator.py` v3.3.1)\n"
    "- ✅ New test suite: `test_v2_4_p1_merge.py` (9 groups / 25 assertions)\n"
    "- ✅ 14 suites / **576 PASS / 0 FAIL / 2 SKIP**\n"
    "\n"
    "### v2.4 (Released 2026-09-22)\n"
)


# base = "code" (relative to code/) or "repo" (relative to repo root)
PATCHES = [
    {"file": "docs/SPEC_OVERVIEW_ja.md", "base": "code",
     "patches": [
         {"id": "JA-test-line",  "old": JA_OLD_TEST_LINE,  "new": JA_NEW_TEST_LINE},
         {"id": "JA-total",      "old": JA_OLD_TOTAL,      "new": JA_NEW_TOTAL},
         {"id": "JA-suite-last", "old": JA_OLD_SUITE_LAST, "new": JA_NEW_SUITE_LAST},
         {"id": "JA-rev",        "old": JA_OLD_REV,        "new": JA_NEW_REV},
     ]},
    {"file": "docs/SPEC_OVERVIEW_en.md", "base": "code",
     "patches": [
         {"id": "EN-test-line",  "old": EN_OLD_TEST_LINE,  "new": EN_NEW_TEST_LINE},
         {"id": "EN-total",      "old": EN_OLD_TOTAL,      "new": EN_NEW_TOTAL},
         {"id": "EN-suite-last", "old": EN_OLD_SUITE_LAST, "new": EN_NEW_SUITE_LAST},
         {"id": "EN-rev",        "old": EN_OLD_REV,        "new": EN_NEW_REV},
     ]},
    {"file": "README.md", "base": "repo",
     "patches": [
         {"id": "README-badge",    "old": README_OLD_BADGE,    "new": README_NEW_BADGE},
         {"id": "README-expected", "old": README_OLD_EXPECTED, "new": README_NEW_EXPECTED},
         {"id": "README-keyfeat",  "old": README_OLD_KEYFEAT,  "new": README_NEW_KEYFEAT},
         {"id": "README-roadmap",  "old": README_OLD_ROADMAP,  "new": README_NEW_ROADMAP},
     ]},
]


def apply_one(full_path: Path, patches, apply: bool, backup: bool) -> bool:
    print()
    print("=" * 78)
    print(f"  {full_path}")
    print("=" * 78)

    if not full_path.exists():
        print(f"  [SKIP] file not found: {full_path}")
        return True

    text = full_path.read_text(encoding="utf-8")
    original = text
    failed = 0

    for p in patches:
        count = text.count(p["old"])
        status = "OK  " if count == 1 else ("SKIP" if count == 0 else "WARN")
        print()
        print(f"  [{status}] [{p['id']}]  matches={count}")
        if count == 0:
            print("    (anchor not found; skipping)")
            continue
        if count > 1:
            print(f"    [WARN] {count} matches; replacing only the first")
        text = text.replace(p["old"], p["new"], 1)
        for line in p["old"].splitlines()[:2]:
            print(f"      - {line}")
        for line in p["new"].splitlines()[:2]:
            print(f"      + {line}")

    if text == original:
        print()
        print("  [INFO] no changes")
        return failed == 0

    if not apply:
        print()
        print("  [DRY-RUN] not written (use --apply)")
        return failed == 0

    if backup:
        bak = full_path.with_suffix(full_path.suffix + ".bak")
        shutil.copy2(full_path, bak)
        print(f"  [BACKUP] {bak}")

    full_path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  [WRITTEN] {full_path}")
    return failed == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-root", default=".",
                    help="Path to code/ (default: current)")
    ap.add_argument("--repo-root", default="..",
                    help="Path to repo root (default: ..)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    ap.add_argument("--file", default=None)
    args = ap.parse_args()

    code_root = Path(args.code_root).resolve()
    repo_root = Path(args.repo_root).resolve()
    apply_flag = args.apply
    backup = not args.no_backup

    print("=" * 78)
    print("  Docs updater v2.4.1 (merge test suite)")
    print("=" * 78)
    print(f"  Code root: {code_root}")
    print(f"  Repo root: {repo_root}")
    print(f"  Mode: {'APPLY' if apply_flag else 'DRY-RUN'}")

    all_ok = True
    for entry in PATCHES:
        if args.file and Path(entry["file"]).name != args.file:
            continue
        base = code_root if entry["base"] == "code" else repo_root
        full_path = base / entry["file"]
        ok = apply_one(full_path, entry["patches"], apply_flag, backup)
        all_ok = all_ok and ok

    print()
    print("=" * 78)
    print(f"  Result: {'OK' if all_ok else 'SOME PATCHES FAILED'}")
    print("=" * 78)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())