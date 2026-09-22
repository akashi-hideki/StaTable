#!/usr/bin/env python3
# code/tools/patch_c50_v25b.py
"""Corrected patch: append candidate 6 to ISSUES_v2_5.md.

The first patch (patch_c50_v25.py) inserted candidate 6 right
after the candidate-5 header, splitting candidate 5's body.
This version inserts candidate 6 *before* the `## 変更履歴`
section, preserving all existing content.

Usage:
    python tools/patch_c50_v25b.py --dry-run
    python tools/patch_c50_v25b.py
"""

from __future__ import annotations
import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
ISSUES_PATH = BASE / "docs" / "ISSUES_v2_5.md"


CANDIDATE_6 = """\
### 候補 6: RoleFunction.namespace の「前方一致制約」を緩和

**Priority**: 🟡 Medium
**Type**: Bug / Enhancement
**Status**: v2.5 で発見（実装は v2.2.5 から）

#### 現状
`role_function_generator._should_declare_here`（および `_should_emit_implementation`）
は以下の場合のみ、その層のヘッダに宣言を出力する：

- `namespace == layer_name`（完全一致）
- `min(len(ns), len(layer)) >= 3` かつ
  `layer.lower().startswith(ns.lower())` または
  `namespace.lower().startswith(layer.lower())`（双方向の前方一致）

#### 問題
不一致の場合：
- **呼び出し**（`RoleFunc_<NS>_<Name>`）は `transition_generator` が生成する
- **宣言**は `role_function_generator` が生成しない
- → `implicit declaration of function 'RoleFunc_<NS>_*'` でコンパイルエラー

#### 再現例（v2.5 TUTORIAL で実証）
| namespace | layer_name | 判定 | 結果 |
|-----------|-----------|------|------|
| `App` | `Application` | 前方一致（3文字） | ✅ 12/12 PASS |
| `Vending` | `Application` | 双方向不一致 | ❌ 11/12 FAIL（gcc / arm 両方） |

#### 対応案
| # | 案 | 変更ファイル | リスク |
|---|----|------------|-------|
| A | SPEC に明記（v2.5 で C-50 として追加済み） | 文書のみ | なし |
| B | `_should_declare_here` を「その層から呼ばれる関数」基準に変更 | `role_function_generator.py` | 中 |
| C | XML 読み込み時に前方一致を自動補正 or 警告 | `xml_io.py` | 中 |
| D | 呼び出し側も宣言側と同じ判定を行う | 両 generator | 大 |

#### 回避策（現実的）
namespace を層の短縮名（`App`、`Drv`、`Mw` など）にする。
TUTORIAL では `Vending` → `App` に変更して解決（`tools/fix_vending_namespace_v2.py`）。

---

## 変更履歴
"""


ANCHOR = "## 変更履歴\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    if not ISSUES_PATH.exists():
        print(f"ERROR: {ISSUES_PATH} not found", file=sys.stderr)
        return 1

    text = ISSUES_PATH.read_text(encoding="utf-8")

    # Already patched?
    if "候補 6: RoleFunction.namespace" in text:
        print("[SKIP] candidate 6 already present")
        return 0

    if ANCHOR not in text:
        print(f"ERROR: anchor {ANCHOR!r} not found", file=sys.stderr)
        return 1

    # Insert CANDIDATE_6 in place of the first "## 変更履歴\n"
    new_text = text.replace(ANCHOR, CANDIDATE_6, 1)

    print(f"Target: {ISSUES_PATH}")
    print(f"Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print(f"Anchor: {ANCHOR!r}  (1 replacement)")

    if args.dry_run:
        return 0

    if not args.no_backup:
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = ISSUES_PATH.with_suffix(f".md.bak_c50b_{ts}")
        shutil.copy2(ISSUES_PATH, bak)
        print(f"Backup: {bak.name}")

    ISSUES_PATH.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"Written: {ISSUES_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())