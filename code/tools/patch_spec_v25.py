#!/usr/bin/env python3
# code/tools/patch_spec_v25.py
"""Apply v2.5 updates to docs/SPEC_OVERVIEW_ja.md.

Usage:
    python tools/patch_spec_v25.py --dry-run   # preview only
    python tools/patch_spec_v25.py             # apply changes

The script performs *exact* string substitutions (no regex). Each
entry in REPLACEMENTS lists the expected occurrence count; if the
actual count differs, the script reports it and continues, so you
can see every mismatch at once instead of failing on the first.

Line endings (LF) are preserved by writing with newline="\\n".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ----------------------------------------------------------------------
# Target file resolution
# ----------------------------------------------------------------------
CANDIDATE_PATHS = [
    Path("code/docs/SPEC_OVERVIEW_ja.md"),
    Path("docs/SPEC_OVERVIEW_ja.md"),
    Path("../docs/SPEC_OVERVIEW_ja.md"),
]


def find_spec_path() -> Path:
    for p in CANDIDATE_PATHS:
        if p.exists():
            return p
    sys.exit(
        "ERROR: SPEC_OVERVIEW_ja.md not found. Tried:\n  "
        + "\n  ".join(str(p) for p in CANDIDATE_PATHS)
    )


# ----------------------------------------------------------------------
# Replacement table
#   (description, old_string, new_string, expected_count)
#
# expected_count is the number of times `old_string` should appear.
# If it doesn't match, the script warns but still applies the change
# (so partial matches don't block the whole run).
# ----------------------------------------------------------------------
REPLACEMENTS: list[tuple[str, str, str, int]] = [

    # ---- [1] Header: version bumps ----
    (
        "[1a] doc title: v2.4 -> v2.5",
        "# `docs/SPEC_OVERVIEW_ja.md` v2.4（決定#5 反映済み完全版）",
        "# `docs/SPEC_OVERVIEW_ja.md` v2.5",
        1,
    ),
    (
        "[1b] spec title: v2.4 -> v2.5",
        "# StaTable 全体仕様書 v2.4（日本語、詳細版）",
        "# StaTable 全体仕様書 v2.5（日本語、詳細版）",
        1,
    ),
    (
        "[1c] version block: 2.4 -> 2.5",
        "Version: 2.4\nDate: 2026-09-22\nScope: StaTable プロジェクト全体",
        "Version: 2.5\nDate: 2026-09-22\nScope: StaTable プロジェクト全体",
        1,
    ),

    # ---- [2] §1.3 F-16 ----
    (
        "[2] F-16 addition",
        "| F-15 | 新規プロジェクト | v2.3：サンプルを消去し空の Application 層から開始（Ctrl+N） |",
        "| F-15 | 新規プロジェクト | v2.3：サンプルを消去し空の Application 層から開始（Ctrl+N） |\n"
        "| F-16 | セル編集中のロール関数管理 | v2.5：ActionEditorDialog 内で Role 関数を新規作成・編集・削除 |",
        1,
    ),

    # ---- [3] §1.4 test suite count ----
    (
        "[3] test suite count in §1.4",
        "| テスト | 14スイート（`tests/test_v2_2_p*.py` + `tests/test_v2_3_p1.py` + `tests/test_v2_4_p1_merge.py`）、576 PASS / 2 SKIP |",
        "| テスト | 15スイート（`tests/test_v2_2_p*.py` + `tests/test_v2_3_p1.py` + `tests/test_v2_4_p1_merge.py` + `tests/test_v2_5_p1.py`）、651 PASS / 2 SKIP |",
        1,
    ),

    # ---- [4] §1.5 glossary (2 items) ----
    (
        "[4] §1.5 glossary: add _find_rf_by_display / _dump_sm_roles",
        "| `dataModified` | v2.3：`StateMachineTab` の変更通知シグナル |\n"
        "\n"
        "---\n"
        "\n"
        "## 2. アーキテクチャ",
        "| `dataModified` | v2.3：`StateMachineTab` の変更通知シグナル |\n"
        "| `_find_rf_by_display` | v2.5：`_ActionGroup` のヘルパー。qualified_name から `RoleFunction` オブジェクトを逆引き |\n"
        "| `_dump_sm_roles` | v2.5：`_ActionGroup` のデバッグヘルパー。`state_machine.role_functions` の内容をログ出力 |\n"
        "\n"
        "---\n"
        "\n"
        "## 2. アーキテクチャ",
        1,
    ),

    # ---- [6] §6.2 ActionEditorDialog ----
    (
        "[6] §6.2 ActionEditorDialog: add v2.5 column & note",
        "### 6.2 `ActionEditorDialog`（v2.2：5タブ）\n"
        "\n"
        "| タブ | 内容 |\n"
        "|------|------|\n"
        "| Transitions | `TransitionsTab` |\n"
        "| Pre / Post Actions | `ActionsTab` |\n"
        "| Relations | `RelationsTab` |\n"
        "| Overview | `OverviewTab` |\n"
        "| Preview | `CodeWidget` |",
        "### 6.2 `ActionEditorDialog`（v2.5：5タブ + ロール関数管理）\n"
        "\n"
        "| タブ | 内容 | v2.5 追加ボタン |\n"
        "|------|------|----------------|\n"
        "| Transitions | `TransitionsTab` | `+ New Role Function` |\n"
        "| Pre / Post Actions | `ActionsTab`（Pre / Post の2グループ） | `+ New Role Function` / `Edit Role Function` / `Delete Role Function` |\n"
        "| Relations | `RelationsTab` | – |\n"
        "| Overview | `OverviewTab` | – |\n"
        "| Preview | `CodeWidget` | – |\n"
        "\n"
        "**v2.5 補足**\n"
        "\n"
        "- 各ボタンは既存の `RoleFunctionDialog` を再利用する。\n"
        "- 新規作成された `RoleFunction` は `state_machine.role_functions`\n"
        "  （**純粋名キー** = `rf.name`）に登録され、UI には\n"
        "  `qualified_name`（`namespace.name`）で表示される。\n"
        "- この差異を吸収するため `_find_rf_by_display()` を `_ActionGroup`\n"
        "  に追加（v2.5）。Edit / Delete ハンドラは同ヘルパーを経由して\n"
        "  正しい dict エントリを操作する。\n"
        "- `TransitionsTab` には `+ New Role Function` のみ配置。追加された\n"
        "  関数は `self.role_functions` リストに反映され、以降の\n"
        "  `TransitionActionsDialog` / `ConditionBuilderDialog` の候補となる\n"
        "  （直接行への追記は行わない）。",
        1,
    ),

    # ---- [7] §11.1 header count ----
    (
        "[7a] §11.1 header: (13) -> (15)",
        "### 11.1 テストスイート（13）",
        "### 11.1 テストスイート（15）",
        1,
    ),

    # ---- [9] §11.1 table last row + total ----
    (
        "[7b] §11.1 table: append test_v2_5_p1.py and update total",
        "| `test_v2_4_p1_merge.py` | コードマージ（v2.4.1） | 25 PASS / 0 FAIL |\n"
        "\n"
        "**合計**：**576 PASS / 0 FAIL / 2 SKIP**",
        "| `test_v2_4_p1_merge.py` | コードマージ（v2.4.1） | 25 PASS / 0 FAIL |\n"
        "| `test_v2_5_p1.py` | ActionEditorDialog ロール関数管理（v2.5） | 75 PASS / 0 FAIL |\n"
        "\n"
        "**合計**：**651 PASS / 0 FAIL / 2 SKIP**",
        1,
    ),

    # ---- [8] §11.3.1 insertion ----
    (
        "[8] insert §11.3.1 before §11.4",
        "| `test_tab_data_modified_sets_window_modified` | emit で `windowModified == True` |\n"
        "\n"
        "### 11.4 実行環境",
        "| `test_tab_data_modified_sets_window_modified` | emit で `windowModified == True` |\n"
        "\n"
        "### 11.3.1 `test_v2_5_p1.py` 内容\n"
        "\n"
        "ActionEditorDialog のロール関数管理機能（v2.5）の 75 テスト：\n"
        "\n"
        "| セクション | 検証内容 | 件数 |\n"
        "|-----------|---------|-----:|\n"
        "| 1. Module import | `ActionsTab` / `TransitionsTab` / `_ActionGroup` / `_qualified_name` | 5 |\n"
        "| 2. `_ActionGroup` 新引数・3ボタン | role_function_library / literal_library / state_machine / layer_names_provider の保持、`+ New` / `Edit` / `Delete` ボタン存在 | 10 |\n"
        "| 3. `ActionsTab` 引数伝播 | 両グループへの新引数伝播、ボタン存在 | 10 |\n"
        "| 4. `TransitionsTab` 引数伝播 | 新引数と `+ New` ボタン | 5 |\n"
        "| 5. `_find_rf_by_display` | qualified / bare / miss / empty / no-sm の5パターン | 7 |\n"
        "| 6. `_get_namespace_choices` | 順序、dedup、provider なし、rfl 経由 | 7 |\n"
        "| 7. `_dialog_kwargs` | `global_vars` / `events` / `literals` / `namespace_choices` | 5 |\n"
        "| 8. `_on_new_role_function` | 正常作成、シグナル emit、行追加、combo 更新 | 6 |\n"
        "| 9. 同上（重複） | 警告表示、行追加なし、sm 不変 | 3 |\n"
        "| 10. `_on_edit_role_function` | ★回帰テスト（qualified_name → bare name 逆引き、namespace 変更） | 4 |\n"
        "| 11. 同上（rename） | bare name 変更時の旧キー削除 + 新キー追加 | 3 |\n"
        "| 12. 同上（未登録） | 情報ダイアログ、ダイアログ未起動 | 2 |\n"
        "| 13. `_on_delete_role_function` | 削除成功、行削除、combo 更新、シグナル emit | 4 |\n"
        "| 14. 同上（キャンセル） | 中止時は無変更 | 2 |\n"
        "| 15. `TransitionsTab._on_new_role_function` | 新規作成フロー | 2 |\n"
        "| **合計** | | **75** |\n"
        "\n"
        "**回帰テスト（セクション10）の重要性**:\n"
        "\n"
        "`StateMachine.role_functions` は **純粋名**（`rf.name`）でキー管理されますが、\n"
        "UI には **qualified_name**（`namespace.name`）を表示します。v2.5 実装中に\n"
        "この不一致により Edit / Delete が機能しない不具合が発生したため、\n"
        "`_find_rf_by_display()` による逆引きを実装し、本テストで再発を防止しています。\n"
        "\n"
        "### 11.4 実行環境",
        1,
    ),

    # ---- [10] §12 C-47..C-49 ----
    (
        "[9] §12 add C-47..C-49",
        "| C-46 | State.do / RoleFunction の予約フィールド | **予約（Reserved）** | UI 非表示。codegen 未使用。XML I/O で保持（v3.7 以降） |",
        "| C-46 | State.do / RoleFunction の予約フィールド | **予約（Reserved）** | UI 非表示。codegen 未使用。XML I/O で保持（v3.7 以降） |\n"
        "| C-47 | Namespace コンボ候補は現タブ + 登録済みロール関数のみ | **v2.5 スコープ外** | 全タブの layer 名を候補にする配線（`MainWindow → StateMachineTab → MatrixTableWidget → ActionEditorDialog`）は別 Issue |\n"
        "| C-48 | `_ActionGroup` の行テキストは qualified_name、`StateMachine.role_functions` は bare name | **v2.5 で吸収** | `_find_rf_by_display()` で逆引き。同種の UI を追加する際は同様の考慮が必要 |\n"
        "| C-49 | XML の `Tab name` / `layer_name` / `RoleFunction.namespace` が不一致の場合、Namespace コンボに複数候補が出る | **データ起因** | 例：`Tab name=\"Application\"` で `namespace=\"App\"` の場合、両方が候補に。正しい XML なら発生しない（§3.2.7 / C-11 参照） |",
        1,
    ),

    # ---- [11] §13 glossary ----
    (
        "[10] §13 glossary: add Role 関数管理ボタン / _find_rf_by_display",
        "| `dataModified` | v2.3：`StateMachineTab` の変更通知シグナル |\n"
        "\n"
        "---\n"
        "\n"
        "## 14. 付録",
        "| `dataModified` | v2.3：`StateMachineTab` の変更通知シグナル |\n"
        "| Role 関数管理ボタン | v2.5：ActionEditorDialog 内の `+ New` / `Edit` / `Delete Role Function` |\n"
        "| `_find_rf_by_display` | v2.5：qualified_name から `RoleFunction` を逆引きするヘルパー |\n"
        "\n"
        "---\n"
        "\n"
        "## 14. 付録",
        1,
    ),

    # ---- [12] §15 revision history ----
    (
        "[11] §15 add v2.5 entry",
        "| 2.4 | 2026-09-22 | UI 整理・予約フィールド・Namespace コンボ対応： |",
        "| 2.5 | 2026-09-22 | ActionEditorDialog ロール関数管理（F-16）： |\n"
        "| | | - §1.3：F-16 追加（セル編集中のロール関数管理） |\n"
        "| | | - §1.4：テストスイートを 15、651 PASS / 2 SKIP に更新 |\n"
        "| | | - §1.5：`_find_rf_by_display` / `_dump_sm_roles` 用語追加 |\n"
        "| | | - §6.2：ActionEditorDialog を v2.5 対応に更新（タブ表に追加ボタン列） |\n"
        "| | | - §11.1：テストスイート表に `test_v2_5_p1.py`（75 PASS）を追加 |\n"
        "| | | - §11.3.1：`test_v2_5_p1.py` の内容（15セクション / 75テスト）追加 |\n"
        "| | | - §12：C-47（Namespace 全タブ未対応）、C-48（qualified vs bare 吸収）、C-49（XML 不一致）追加 |\n"
        "| | | - §13：Role 関数管理ボタン / `_find_rf_by_display` 追加 |\n"
        "| | | - §15：本エントリ |\n"
        "| 2.4 | 2026-09-22 | UI 整理・予約フィールド・Namespace コンボ対応： |",
        1,
    ),

    # ---- [13] Footer ----
    (
        "[12] footer: v2.3 -> v2.5",
        "以上、`SPEC_OVERVIEW_ja.md` v2.3（決定#5 反映済み）の完全版です。",
        "以上、`SPEC_OVERVIEW_ja.md` v2.5 の完全版です。",
        1,
    ),
]


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show which replacements would be applied, without writing.",
    )
    args = parser.parse_args()

    spec_path = find_spec_path()
    print(f"Target: {spec_path}")
    print(f"Mode:   {'DRY-RUN' if args.dry_run else 'APPLY'}")
    print()

    original = spec_path.read_text(encoding="utf-8")
    text = original

    matched = 0
    missed: list[str] = []
    mismatched: list[tuple[str, int, int]] = []

    for desc, old, new, expected in REPLACEMENTS:
        count = text.count(old)
        if count == 0:
            missed.append(desc)
            print(f"[MISS] {desc}  (old string not found)")
            continue
        if count != expected:
            mismatched.append((desc, expected, count))
            print(f"[WARN] {desc}  "
                  f"(expected {expected}, found {count}) — applying anyway")
        else:
            print(f"[ OK ] {desc}  ({count} replacement{'s' if count > 1 else ''})")
        text = text.replace(old, new)
        matched += 1

    print()
    print("=" * 70)
    print(f"  applied:  {matched} / {len(REPLACEMENTS)}")
    print(f"  missed:   {len(missed)}")
    print(f"  mismatch: {len(mismatched)}")
    print("=" * 70)

    if missed:
        print("\nMissed entries (old string not present):")
        for d in missed:
            print(f"  - {d}")

    if args.dry_run:
        print("\nDry-run: no file written.")
        return 0

    if text == original:
        print("\nNo changes; file untouched.")
        return 0

    # Preserve LF line endings (avoid git CRLF warnings)
    spec_path.write_text(text, encoding="utf-8", newline="\n")
    print(f"\nWritten: {spec_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())