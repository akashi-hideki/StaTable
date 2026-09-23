#!/usr/bin/env python3
# code/tools/patch_c51.py
"""Add C-51 (event trigger definition gap) to SPEC and ISSUES.

Usage:
    python tools/patch_c51.py --dry-run
    python tools/patch_c51.py
"""

from __future__ import annotations
import argparse
import re
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

SPEC = BASE / "docs" / "SPEC_OVERVIEW_ja.md"
ISSUES = BASE / "docs" / "ISSUES_v2_5.md"

C51_ROW = (
    "| C-51 | イベントの「発生条件」を XML で定義できない | "
    "**設計ギャップ（別 Issue）** | "
    "`<Event>` には kind / delivery_type / source_layer はあるが、"
    "「いつ・何を契機に発生するか」（トリガー種別・発生源・"
    "周期・デバウンス）を書く場所がない。`GetNextEvent_<Layer>` は"
    "ユーザー実装に委ねられており、codegen は生成しない。"
    "→ ISSUES_v2_5.md 候補7参照 |"
)

CANDIDATE_7 = """### 候補 7: イベントの「発生条件」定義（trigger）

**Priority**: 🟡 Medium
**Type**: Enhancement / Data model
**Status**: v2.5.2 で発見（設計ギャップ）

#### 現状

`<Event>` 要素には以下の属性がある:

- `kind`（signal / call / time / change）
- `delivery_type`（direct / queue / double）
- `source_layer`（driver / middleware）
- `priority`, `data_type`, `data_name`

しかし **「いつ発生するか」を書く場所がない**。
`description` に自由記述はできるが、構造化されていない:

| 不足情報 | 例（SELECT_ITEM） |
|---------|-----------------|
| 発生源 | 商品ボタン GPIO |
| トリガー種別 | エッジ検出 |
| デバウンス | 20ms |
| ポーリング周期 | 10ms |
| データ生成 | `item_id = ボタン index` |

#### 影響

- 状態遷移表のセルを見ても「そのイベントがいつ来るか」が分からない
- `StateMachine_GetNextEvent_<Layer>` はユーザー実装（codegen は空関数を出力）
- バリデーションで「time イベントなのに周期未定義」を検出できない

#### 対応案（段階的）

| # | 案 | 工数 | codegen |
|---|----|------|---------|
| A | `trigger` 自由記述属性を追加 | 1〜2h | 影響なし |
| B | `<Trigger type="..." source="..."/>` 構造化 | 4〜6h | v2.6 で活用 |
| C | GUI に「イベントカタログ」タブ | 1日 | – |

#### 推奨

段階的に進める:

1. SPEC に C-51 として記録（本 Issue で実施）
2. 投稿後のフィードバックを待つ
3. v2.6 で案 A → 案 B の順に実装

#### 対象ファイル（将来）

- `statable/model.py`（`EventTrigger` dataclass 追加）
- `statable/xml_io.py`（`<Trigger>` 子要素の I/O）
- `statable_gui/event_definition_dialog.py`（トリガー編集 UI）
- `codegen/transition_generator.py`（v2.6 で GetNextEvent 自動生成）

---

"""


def patch_spec(dry: bool) -> int:
    if not SPEC.exists():
        print(f"ERROR: {SPEC} not found")
        return 1
    text = SPEC.read_text(encoding="utf-8")
    if "C-51" in text:
        print("[SKIP] SPEC C-51 already present")
        return 0
    m = re.search(r'^\| C-50 \|.*$', text, re.MULTILINE)
    if not m:
        print("[MISS] SPEC: C-50 row not found")
        return 1
    insert_at = m.end()
    new_text = text[:insert_at] + "\n" + C51_ROW + text[insert_at:]
    if dry:
        print("[OK] SPEC: would insert C-51 after C-50")
        return 0
    bak = SPEC.with_suffix(".md.bak_c51")
    shutil.copy2(SPEC, bak)
    SPEC.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK] SPEC: C-51 inserted (backup: {bak.name})")
    return 0


def patch_issues(dry: bool) -> int:
    if not ISSUES.exists():
        print(f"ERROR: {ISSUES} not found")
        return 1
    text = ISSUES.read_text(encoding="utf-8")
    if "候補 7" in text:
        print("[SKIP] ISSUES candidate 7 already present")
        return 0
    anchor = "## 変更履歴\n"
    if anchor not in text:
        print("[MISS] ISSUES: '## 変更履歴' anchor not found")
        return 1
    new_text = text.replace(anchor, CANDIDATE_7 + anchor, 1)
    if dry:
        print("[OK] ISSUES: would insert candidate 7")
        return 0
    bak = ISSUES.with_suffix(".md.bak_c51")
    shutil.copy2(ISSUES, bak)
    ISSUES.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK] ISSUES: candidate 7 inserted (backup: {bak.name})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    print(f"BASE: {BASE}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()
    rc1 = patch_spec(args.dry_run)
    rc2 = patch_issues(args.dry_run)
    return 0 if (rc1 == 0 and rc2 == 0) else 1


if __name__ == "__main__":
    sys.exit(main())