"""v3.5.0: update HANDOVER with Phase 1b + GUI output-clear issue."""
from __future__ import annotations
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DOC = REPO / "code" / "docs" / "HANDOVER_v3_5_0.md"

REPLACEMENTS: list[tuple[str, str]] = []

# 1) 最新コミット (CI green 7 連続 -> 8 連続, prepend 16237ff)
REPLACEMENTS.append((
    "### 最新コミット (CI green 7 連続)\n"
    "\n"
    "- `29cf425` ci(v3.5.0): update GitHub Actions to Node.js 24 versions (S-5)\n",
    "### 最新コミット (CI green 8 連続)\n"
    "\n"
    "- `16237ff` refactor(v3.5.0): Phase 1b mypy cleanup (218 -> 58 errors)\n"
    "- `29cf425` ci(v3.5.0): update GitHub Actions to Node.js 24 versions (S-5)\n",
))

# 2) 品質状態 (mypy baseline 更新)
REPLACEMENTS.append((
    "- **mypy baseline: 218 errors / 23 files** (informational, 削減目標)\n",
    "- **mypy baseline: 58 errors / 16 files** (Phase 1b 後、218 から -73%)\n",
))

# 3) S-5 の後に Phase 1b セクション追加
OLD_S5 = (
    "### S-5: GitHub Actions Node.js 24 対応 (commit 29cf425)\n"
    "\n"
    "- `actions/checkout@v4` -> `v5`（8 箇所）\n"
    "- `actions/setup-python@v5` -> `v6`（8 箇所）\n"
    "- `actions/upload-artifact@v4` -> `v5`（5 箇所）\n"
    "- 効果: Node.js 20 deprecation 警告が 21 件 -> 1 件に削減\n"
    "  - 残る 1 件は `upload-artifact@v5` 側の問題（GitHub 側の対応待ち）\n"
)
NEW_S5 = (
    OLD_S5
    + "\n"
    + "### Phase 1b: mypy 218 -> 58 errors (commit 16237ff)\n"
    + "\n"
    + "- `CodeTemplates` の 15 dict に `dict[str, Any]` 注釈\n"
    + "- 各ジェネレータの `*_TEMPLATES` 26 dict に `dict[str, Any]` 注釈\n"
    + "- `xml_io.py` の truthy-function 6 件 (`X is not None`)\n"
    + "- 7 ファイルの var-annotated 12 件（dict/list 型注釈）\n"
    + "- `SubElement(..., **attrs)` 15 行に `# type: ignore[arg-type]`\n"
    + "  - mypy の dict invariance 由来、実行時は問題なし\n"
    + "- **結果: 218 -> 58 errors (-73%)**\n"
)
REPLACEMENTS.append((OLD_S5, NEW_S5))

# 4) コミット履歴 (7 -> 8)
REPLACEMENTS.append((
    "## v3.5.0 コミット履歴\n"
    "\n"
    "- `29cf425` ci(v3.5.0): update GitHub Actions to Node.js 24 versions (S-5)\n",
    "## v3.5.0 コミット履歴\n"
    "\n"
    "- `16237ff` refactor(v3.5.0): Phase 1b mypy cleanup (218 -> 58 errors)\n"
    "- `29cf425` ci(v3.5.0): update GitHub Actions to Node.js 24 versions (S-5)\n",
))

# 5) 優先度 S 更新 (Phase 1b 完了)
REPLACEMENTS.append((
    "1. **v3.5.0 続行**\n"
    "   - Phase 1b: `CodeTemplates` の型問題解消 (~150 errors 削減)\n"
    "   - Phase 1c: `Optional[X]` -> `X | None` 統一 (88 箇所)\n"
    "   - S-3 Step 2: ubuntu-26.04 preview ジョブ追加 (**10/19 以降**)\n"
    "   - 完了済み: S-4 (matrix + coverage), S-5 (Node.js 24 対応)\n",
    "1. **v3.5.0 続行**\n"
    "   - Phase 1c: 残り 58 errors の削減（`statable/xml_io.py` 中心）\n"
    "   - S-3 Step 2: ubuntu-26.04 preview ジョブ追加 (**10/19 以降**)\n"
    "   - **GUI 生成時の output クリア問題**（下記「未解決の問題」参照）\n"
    "   - 完了済み: S-4, S-5, Phase 1b\n",
))

# 6) mypy Baseline セクション更新
REPLACEMENTS.append((
    "## mypy Baseline (Phase 1a 完了時点)\n"
    "\n"
    "| File | errors |\n"
    "|---|---:|\n"
    "| `statable/xml_io.py` | 47 |\n"
    "| `codegen/osal_generator.py` | 35 |\n"
    "| `codegen/role_function_generator.py` | 34 |\n"
    "| `codegen/transition_generator.py` | 31 |\n"
    "| `codegen/enum_generator.py` | 16 |\n"
    "| `codegen/struct_generator.py` | 13 |\n"
    "| others | 42 |\n"
    "| **Total** | **218** |\n"
    "\n"
    "**Phase 1b の主眼**: `CodeTemplates` が `object` 型として推論される問題 (~150 errors)\n"
    "**Phase 1c の主眼**: `Optional[X]` -> `X | None` 統一 (88 箇所)\n",
    "## mypy Baseline (Phase 1b 完了時点)\n"
    "\n"
    "| File | errors |\n"
    "|---|---:|\n"
    "| `statable/xml_io.py` | ~30 |\n"
    "| `codegen/validate/validation_dialog.py` | ~9 |\n"
    "| PySide6 `type[Qt]` 系 | ~7 |\n"
    "| others | ~12 |\n"
    "| **Total** | **58** |\n"
    "\n"
    "**Phase 1c の主眼**:\n"
    "- `statable/xml_io.py` の残り（型注釈・`# type: ignore`）\n"
    "- `statable_gui.*` の PySide6 stub 問題（overrides で抑制可）\n"
    "- `Optional[X]` -> `X | None` 統一 (88 箇所)\n",
))

# 7) 「未解決の問題」セクションを新規追加（新スレッド開始時の推奨アクションの前）
REPLACEMENTS.append((
    "## 新スレッド開始時の推奨アクション\n",
    "## 未解決の問題: GUI コード生成時の output クリア漏れ\n"
    "\n"
    "### 症状\n"
    "- GUI でプロジェクトを生成時、`output/` をクリアしないため、\n"
    "  古いアーキテクチャ（例: v3.3.x の `Driver/` 層）のファイルが残存\n"
    "- 新プロジェクトで未定義の変数（`retry_count` 等）を参照 → コンパイル失敗\n"
    "\n"
    "### 再現手順（2026-10-11 確認済み）\n"
    "1. v3.3.x の XML を GUI で読み込み、`output/` に生成\n"
    "2. v3.4.3 以降の XML（7 層調理器サンプル）を読み込み、同じ `output/` に生成\n"
    "   （クリアせず）\n"
    "3. `output/Driver/` の古いファイルが残り、`arm-none-eabi-gcc` で失敗\n"
    "\n"
    "### 確認済みの事実\n"
    "- `output/` 完全削除 → 再生成で **LINK PASS**（firmware.bin 28540 bytes）\n"
    "- `statable_types_common.h` の `SystemData_t` に `retry_count` なし\n"
    "- しかし `Driver/statable_role_functions_Driver.c` が参照（古いファイル）\n"
    "- **codegen 側のバグではなく、GUI 側の運用問題**\n"
    "\n"
    "### 対処案（未決定）\n"
    "- A. 生成前に自動クリア（オプション or 常時）\n"
    "- B. 生成後に古いファイルを警告\n"
    "- C. 「クリーン生成」ボタン追加\n"
    "- D. output/ を一時ディレクトリに生成してから同期\n"
    "\n"
    "---\n"
    "\n"
    "## 新スレッド開始時の推奨アクション\n",
))


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_0_handover_update2")
    print("=" * 70)
    txt = DOC.read_text(encoding="utf-8")
    for i, (old, new) in enumerate(REPLACEMENTS, 1):
        if old not in txt:
            print(f"  [FAIL] replacement #{i}: pattern not found")
            print("----- expected (first 200 chars) -----")
            print(repr(old[:200]))
            sys.exit(1)
        txt = txt.replace(old, new, 1)
        print(f"  applied #{i}")
    DOC.write_text(txt, encoding="utf-8")
    print()
    print(f"[OK] wrote {DOC.relative_to(REPO)} ({len(txt)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())