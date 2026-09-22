#!/usr/bin/env python3
# code/tools/patch_spec_v252.py
"""Append v2.5.1 and v2.5.2 entries to SPEC §15 revision history.

Both entries are inserted ABOVE the existing v2.5 entry so that the
history stays in reverse-chronological order.

Usage:
    python tools/patch_spec_v252.py --dry-run
    python tools/patch_spec_v252.py
"""

from __future__ import annotations
import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


CANDIDATE_PATHS = [
    Path("docs/SPEC_OVERVIEW_ja.md"),
    Path("../docs/SPEC_OVERVIEW_ja.md"),
    Path("code/docs/SPEC_OVERVIEW_ja.md"),
]

ANCHOR = "| 2.5 | 2026-09-22 | ActionEditorDialog ロール関数管理（F-16）： |"

INSERT = (
    "| 2.5.2 | 2026-09-23 | (void) 抑制をユーザー編集可能領域へ移動： |\n"
    "| | | - `_generate_local_data_pointers` を `_decls` と `_suppress` に分割 |\n"
    "| | | - `(void)` 群を `STABLE_USER_CODE` マーカー内に出力 |\n"
    "| | | - ユーザーが個別行を削除可能、`code_merger` が保持 |\n"
    "| | | - `tests/test_v2_5_p3.py`（25 PASS）追加 |\n"
    "| 2.5.1 | 2026-09-23 | C-50（namespace 前方一致制約）解消： |\n"
    "| | | - `_should_declare_here` に call_map フォールバック追加 |\n"
    "| | | - `generate_all_declarations` に `state_machine` 引数追加 |\n"
    "| | | - 任意の namespace / layer_name が使用可能に |\n"
    "| | | - `tests/test_v2_5_p2.py`（16 PASS）追加 |\n"
)


def find_target() -> Path:
    for p in CANDIDATE_PATHS:
        if p.exists():
            return p
    sys.exit(
        "ERROR: SPEC_OVERVIEW_ja.md not found. Tried:\n  "
        + "\n  ".join(str(p) for p in CANDIDATE_PATHS)
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    target = find_target()
    print(f"Target: {target}")
    print(f"Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()

    text = target.read_text(encoding="utf-8")

    if "| 2.5.1 |" in text or "| 2.5.2 |" in text:
        print("[SKIP] v2.5.1 / v2.5.2 entries already present")
        return 0

    n = text.count(ANCHOR)
    if n == 0:
        print("[MISS] anchor not found:")
        print(ANCHOR)
        return 1
    print(f"[ OK ] anchor found ({n} occurrence)")

    if args.dry_run:
        print()
        print("--- entries to be inserted above anchor ---")
        print(INSERT)
        return 0

    if not args.no_backup:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = target.with_suffix(target.suffix + f".bak_spec252_{ts}")
        shutil.copy2(target, bak)
        print(f"Backup: {bak.name}")

    new_text = text.replace(ANCHOR, INSERT + ANCHOR, 1)
    target.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"Written: {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())