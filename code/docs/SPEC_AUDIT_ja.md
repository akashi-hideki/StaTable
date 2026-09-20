# StaTable 監査仕様書 v1.0（日本語版）

版: 1.0
作成日: 2026-09-20
目的: 監査・引き継ぎ
対象読者: 監査担当者、新規保守担当者、技術レビュア
根拠: 既存仕様書（OVERVIEW / SCREENS / SEQUENCES / CODEGEN v3.0）

本ドキュメントは、監査上重要な事実を既存仕様書から抽出・再構成したものである。
操作マニュアルではない。操作手順は `SPEC_SCREENS_ja.md` を参照。

---

## 目次

1. 目的と適用範囲
2. システム境界
3. コンポーネント一覧
4. データモデル契約
5. コード生成契約
6. GUI 契約
7. 既知の制約（網羅）
8. 未実装機能
9. 検証と CI
10. リスク登録簿
11. 引き継ぎチェックリスト
12. 改訂履歴

---

## 1. 目的と適用範囲

### 1.1 目的

以下を単一の監査可能な参照として提供する:

- StaTable が「やること」と「やらないこと」
- 各挙動がどこに実装されているか
- どの制約が既知で、文書化され、受容されているか
- どの機能が未実装で、そのフォールバック挙動は何か
- 何がどのように検証されているか

### 1.2 適用範囲

| 項目 | 詳細 |
|------|------|
| 対象パッケージ | `statable/`, `statable_gui/`, `codegen/` |
| テストスイート | `code/tests/test_v2_2_p*.py`（12 スイート） |
| CI | `.github/workflows/check.yml` |
| 検証ツール | `code/tools/find_all_japanese.py`, `code/tools/verify_generated_code.py` |

### 1.3 適用範囲外

- 機能要望 / ロードマップ
- 宣言された役割を超えるサードパーティ依存の挙動
- 生成 C コードのハードウェア固有挙動

---

## 2. システム境界

### 2.1 外部インターフェース

| インターフェース | 方向 | 形式 | 提供元 |
|-----------------|------|------|--------|
| プロジェクト XML | 入 / 出 | XML (UTF-8) | `statable/xml_io.py` |
| 生成 C コード | 出 | C99 ソース (UTF-8) | `codegen/` |
| 設定 JSON | 出 | JSON (UTF-8) | `statable_gui/code_generation_dialog.py` |
| ログストリーム | 出 | Python `logging` | `statable_gui/logger.py` |
| GitHub Actions | 出 | YAML | `.github/workflows/check.yml` |

### 2.2 依存方向（厳格）

```
statable_gui  →  codegen  →  statable
libcntrl      →  （なし）
transition_editor_direct  →  statable_gui
```

**逆依存は存在しない**。モジュールレベルの import 解析で検証済み。

### 2.3 実行環境

| 項目 | 要件 |
|------|------|
| Python | 3.12 |
| GUI フレームワーク | PySide6 (Qt 6) |
| GUI アドオン | PySide6-Addons（`QWebEngineView` 用） |
| OS（開発） | Windows 10/11, Linux (Ubuntu 22.04+) |
| OS（CI） | `ubuntu-latest` |

---

## 3. コンポーネント一覧

### 3.1 パッケージ

| パッケージ | 用途 | ファイル数 |
|-----------|------|-----------|
| `statable/` | データモデル、XML I/O、Mermaid 生成 | 7（`__init__.py` 除く） |
| `statable_gui/` | GUI 画面、ダイアログ | 約 20 |
| `statable_gui/libcntrl/` | 共有ライブラリ | 5+ |
| `statable_gui/transition_editor_direct/` | D&D 遷移エディタ | 8 |
| `codegen/` | C コード生成 | 16 |
| `code/tests/` | テストスイート | 12 |
| `code/tools/` | 検証ツール | 2 |

### 3.2 エントリポイント

| エントリポイント | パス | 用途 |
|-----------------|------|------|
| アプリ起動 | `python -m statable_gui.main` | GUI 起動 |
| テスト実行 | `python tests/test_v2_2_p*.py` | 個別スイート |
| C コード検証 | `python tools/verify_generated_code.py --root output` | 生成後の検証 |
| CI | `main` / `develop` への `git push` | 自動チェック |

---

## 4. データモデル契約

### 4.1 `StateMachine` キー一意性（監査所見）

| コレクション | キー | 実装箇所 |
|-------------|------|---------|
| `states` | `state.name` | `state_machine.py` |
| `events` | `event.name` | `state_machine.py` |
| `role_functions` | **`rf.name`（純粋名）** | `state_machine.py` |
| `transitions` | リスト（キーなし） | `state_machine.py` |

**重大**: `role_functions` は **純粋名** をキーとする。同じ純粋名で名前空間が異なるロール関数（例: `Driver.Init` と `App.Init`）は `StateMachine` 内で **衝突** する。片方のみが残る。

### 4.2 `RoleFunction.qualified_name`（監査所見）

| 場所 | キー | 型 |
|------|------|-----|
| `statable.StateMachine.role_functions` | `rf.name` | 純粋名 |
| `libcntrl.RoleFunctionLibrary.role_functions` | `rf.qualified_name` | `namespace.name` |

**非対称性**: 同一概念オブジェクトに対し、2 つのライブラリが異なる一意性キーを使用している。

### 4.3 XML 往復忠実性（監査所見）

| フィールド | 保存 | 復元 | 備考 |
|-----------|------|------|------|
| `super_include_dir` | ❌ | ❌ | `"common"` にリセット |
| `external_includes` | ✅ | ✅ | ファイル名のみ |
| `used_role_functions`（ISR） | ✅ | ✅ | `<UsedRoleFunction ref="..."/>` |
| `used_variables`（ISR） | ✅ | ✅ | `<UsedVariable name="..."/>` |
| `RoleFunction.namespace` | ✅ | ✅ | レガシー名は自動移行 |
| `State.entry` / `State.exit` | ✅ | ✅ | `List[str]`（v2.2） |

### 4.4 `Transition` 既定値（監査参照）

| フィールド | 既定 | 意味 |
|-----------|------|------|
| `condition` | `""` | 空 = 無条件 |
| `has_else` | `True` | else 節は既定で有効 |
| `else_target` | `""` | else 遷移先未設定 |
| `transition_type` | `"external"` | 型ラベル |

---

## 5. コード生成契約

### 5.1 出力契約

| # | ファイル | 種別 | 用途 |
|---|---------|------|------|
| 1 | `statable_types.h` | ヘッダ | 型、構造体、マクロ |
| 2 | `statable_transitions.h` | ヘッダ | 遷移宣言 |
| 3 | `statable_transitions.c` | ソース | セル関数、遷移テーブル、Process |
| 4 | `statable_role_functions.h` | ヘッダ | ロール関数宣言 |
| 5 | `statable_role_functions.c` | ソース | ロール関数実装、call_sites |
| 6 | `statable_init.c` | ソース | `SystemContext_Init` |
| 7 | `statable_event_queue.c` | ソース | キュー実装 |
| 8 | `statable_interrupt.c` | ソース | ISR |
| 9 | `statable_timer.c` | ソース | タイマ構造体 + Init/Update |
| 10 | `osal.h` | ヘッダ | OS 抽象化 |
| 11 | `osal.c` | ソース | OS 抽象化実装 |
| 12 | `statable_all.h` | ヘッダ | スーパーインクルード |
| 13 | `{project}_run.c` | ソース | スーパーループ |

**総数**: 13 ファイル。

### 5.2 フォルダ構成契約

| 構成 | 規則 |
|------|------|
| `flat` | 全ファイルを 1 ディレクトリ |
| `by_type` | `include/` / `src/` / `common/` |
| `by_layer` | 層別サブディレクトリ + 共通をルートに |

層固有ファイル（5 個）: `statable_types.h`, `statable_transitions.h`, `statable_transitions.c`, `statable_role_functions.h`, `statable_role_functions.c`。

### 5.3 マーカー契約（ユーザーコード保持）

| マーカー | 用途 | マージ挙動 |
|---------|------|-----------|
| `[[STABLE_USER_CODE_START]]` / `_END` | ファイルレベル ユーザーコード | 最終 `#include` の直後に挿入 |
| `[[STABLE_USER_CODE_START:<name>]]` / `_END:<name>` | 関数レベル ユーザーコード | ブロック置換。不在時は挿入しない |
| `[[STABLE_USER_CODE_TAIL_START]]` / `_END` | ファイル末尾 ユーザーコード | ブロック置換 |
| `[[STABLE_AUTO_GENERATED_START]]` / `_END` | 自動生成領域 | 常に再生成 |
| `[[STABLE_USER_INCLUDES_START]]` / `_END` | スーパーインクルード ユーザー領域 | 保持 |

### 5.4 ISR 契約（Stage 3）

生成される各 ISR:

1. `SystemContext_t *ctx = &g_ctx;` を自動挿入
2. `(void)ctx;` で未使用警告抑制
3. アクション変換: `Driver.Init` → `RoleFunc_Driver_Init(NULL, ctx)`
4. `used_role_functions` / `used_variables` を自動抽出しモデルに書き戻す
5. ユーザーマーカー `<name> = PascalCase(handler.name)`

### 5.5 Stage 4 名前空間契約

`_normalize_func_ref` の受け入れ形式:

| 入力 | 正規化結果 |
|------|-----------|
| `Driver.Init` | `Driver.Init` |
| `Driver.Init(arg1)` | `Driver.Init` |
| `RoleFunc_Driver_Init` | `Driver.Init`（layer_name 一致時） |
| `Init` | `Init` |

---

## 6. GUI 契約

### 6.1 画面起動

| トリガー | 開く画面 | モーダル? |
|---------|---------|----------|
| ツールバー / メニュー | 15 ダイアログ | はい |
| セル ダブルクリック | `ActionEditorDialog` | はい |
| セル Enter/F2 | `ActionEditorDialog` | はい |
| SettingsPanel entry/exit/do ダブルクリック | `ActionEditDialog` | はい |

### 6.2 状態遷移図（MermaidWidget）

| 項目 | 値 |
|------|-----|
| 生成器 | `statable/mermaid_gen.py` |
| 描画エンジン | Mermaid.js（`mermaidwin.js`） |
| 形式 | `stateDiagram-v2` |
| 環境変数による上書き | `STATABLE_DISABLE_MERMAID=1` → プレースホルダ `QLabel` |
| フォールバック | WebEngine 不可時 `QPlainTextEdit` |

### 6.3 SettingsPanel 契約（v2.2）

| タブ | 列 |
|------|-----|
| `State list` | Name, Description, entry function, exit function, do function, Type |
| `Role function` | Title, Function name, Namespace, Description, Return type, Arg 1 type, Arg 1 name, Arg 2 type, Arg 2 name |

**データ型**: `State.entry` と `State.exit` は `List[str]`（v2.2）。UI では `"; "` 連結文字列として表示。パースは `_display_to_list`。

### 6.4 モーダル挙動

**全ダイアログがモーダル**。モードレスダイアログは存在しない。影響: ダイアログ表示中はメインウィンドウ操作不可。

---

## 7. 既知の制約（網羅）

**本節が最も監査上重要**。全項目がソースに対して検証済み。

| # | 項目 | 状態 | 実装箇所 | 影響 |
|---|------|------|---------|------|
| C-01 | `generation_style` / `table_type` の GUI 切替 | **不可**（`table_driven` / `array` 強制） | `code_generation_settings_dialog.py` | 設定 UI は固定ラベル表示 |
| C-02 | `switch_case` 生成 | **未実装** → `table_driven` フォールバック | `transition_generator.py` | 警告ログ出力 |
| C-03 | `switch` テーブル方式 | **未実装** → `array` フォールバック | `transition_generator.py` | 警告ログ出力 |
| C-04 | `dictionary` テーブル方式 | **未実装** → `array` フォールバック | `transition_generator.py` | 警告ログ出力 |
| C-05 | `external_includes_in_role` | **未実装** | `c_code_generator.py` | 設定フラグが無効 |
| C-06 | `external_includes_in_transitions` | **未実装** | 同上 | 同上 |
| C-07 | `external_includes_in_common` | **未実装** | 同上 | 同上 |
| C-08 | FreeRTOS OSAL | **include のみ** | `osal_generator.py` | 関数本体なし |
| C-09 | ThreadX OSAL | **include のみ** | 同上 | 同上 |
| C-10 | プロジェクト XML の `super_include_dir` | **未保存** | `xml_io.py` / `main_window.py` | `"common"` にリセット |
| C-11 | ロール関数一意性の非対称 | **設計上の非対称** | `statable` vs `libcntrl` | 名前空間跨ぎの同名衝突 |
| C-12 | `transition_to_flow_item` の空イベント | **バグ** | `transition_editor_direct/draft.py` | `"NewEvent"` に変換 |
| C-13 | `palette_widget._add_function` import | **フォールバックなし** | `palette_widget.py` | 環境により `ImportError` |
| C-14 | `project_dir_name` | **予約のみ、未使用** | `config.py` | 効果なし |
| C-15 | `flow_widget.py` / `edit_dialogs.py` | **レガシー** | `transition_editor_direct/` | デッドコード、未参照 |
| C-16 | 外部インクルードのパス | **ファイル名のみ** | `code_generation_settings_dialog.py` | ディレクトリ部分が失われる |
| C-17 | `TransitionContext_t`（共通）vs `TransitionContext_<Layer>_t` | **両方生成** | `struct_generator.py` | 同レイアウトの 2 型 |
| C-18 | 多層 `by_type` | **1 ファイルにマージ** | `c_code_generator.py` | 層分離が見えない |
| C-19 | 出力先警告の `\n` 欠落 | **表示上のバグ** | `main_window.py` | 「settingsPlease specify」と表示 |
| C-20 | `flow_item_to_transition` の title 処理 | **エッジケース** | `draft.py` | `edited_text == name` で title が `"(無題遷移)"` 化 |

---

## 8. 未実装機能

| # | 機能 | 宣言箇所 | 期待挙動 |
|---|------|---------|---------|
| U-01 | `switch_case` プロセス方式 | `CodeGenerationConfig.generation_style` | `table_driven` フォールバック + 警告 |
| U-02 | `switch` テーブル方式 | `CodeGenerationConfig.table_type` | `array` フォールバック + 警告 |
| U-03 | `dictionary` テーブル方式 | 同上 | 同上 |
| U-04 | ロール関数別 外部インクルード | `external_includes_in_role` | include 出力なし |
| U-05 | transitions 別 外部インクルード | `external_includes_in_transitions` | include 出力なし |
| U-06 | common 別 外部インクルード | `external_includes_in_common` | include 出力なし |
| U-07 | FreeRTOS OSAL 関数本体 | `osal_generator.py` | `#include "FreeRTOS.h"` 等のみ |
| U-08 | ThreadX OSAL 関数本体 | 同上 | `#include "tx_api.h"` のみ |
| U-09 | `parser.py`（Excel/CSV/JSON 入力） | `statable/parser.py` | スタブのみ |
| U-10 | `super_include_dir` のプロジェクト永続化 | `xml_io.py` | 保存されない |

---

## 9. 検証と CI

### 9.1 CI ジョブ

| ジョブ | 目的 | ツール |
|-------|------|-------|
| `no-japanese` | 非 ASCII 検出 | `tools/find_all_japanese.py` |
| `syntax` | Python 構文 | `python -m compileall` |
| `tests` | 12 テストスイート | `python tests/test_v2_2_p*.py` |
| `generated-code` | C コード生成チェック | `tools/verify_generated_code.py` |

### 9.2 CI 環境

| 変数 | 値 | 用途 |
|------|-----|------|
| `QT_QPA_PLATFORM` | `offscreen` | ヘッドレス GUI |
| `STATABLE_DISABLE_MERMAID` | `1` | WebEngine スキップ |
| `PYTHONIOENCODING` | `utf-8` | 文字化け防止 |

### 9.3 Qt システムライブラリ（CI）

```
libegl1 libgl1 libglib2.0-0 libdbus-1-3
libxkbcommon0 libxkbcommon-x11-0
libxcb-icccm4 libxcb-image0 libxcb-keysyms1
libxcb-randr0 libxcb-render-util0 libxcb-shape0
libxcb-xinerama0 libxcb-xfixes0 libxcb-cursor0
libfontconfig1 libfreetype6
```

### 9.4 検証カバレッジ

| 領域 | 検証手段 | カバレッジ |
|------|---------|-----------|
| データモデル | `test_v2_2_p1`, `p2` | 高 |
| GUI ヘルパー | `test_v2_2_p3` | 中 |
| コード生成 | `test_v2_2_p4a`, `p4b` | 高 |
| Stage 機能 | `test_v2_2_p12_*` | 高 |
| C コード正当性 | `verify_generated_code.py` | 構造のみ |

### 9.5 検証の空白（監査所見）

| 空白 | 影響 |
|------|------|
| 生成 C コードのコンパイル試験が CI にない | 型エラーが検出されない |
| `super_include_dir` 永続化のテストなし | リグレッション未検出 |
| 名前空間跨ぎのロール関数衝突テストなし | データ消失未検出 |
| 空イベント `transition_to_flow_item` のテストなし | バグが残存 |
| レガシー `flow_widget.py` / `edit_dialogs.py` 未テスト | デッドコードのドリフト |

---

## 10. リスク登録簿

| ID | リスク | 発生可能性 | 影響 | 緩和策 |
|----|-------|-----------|------|-------|
| R-01 | 名前空間跨ぎのロール関数衝突 | 中 | `StateMachine.role_functions` のデータ消失 | キーを `qualified_name` に変更 |
| R-02 | 読込時の `super_include_dir` リセット | 高 | ユーザー設定消失 | XML に永続化 |
| R-03 | 空イベント遷移が `"NewEvent"` に変換 | 中 | 不正な遷移タイトル | `transition_to_flow_item` 修正 |
| R-04 | 生成 C コードのコンパイルエラー未検出 | 中 | 壊れた出力が出荷 | `arm-none-eabi-gcc -fsyntax-only` を CI に追加 |
| R-05 | レガシーコードのドリフト | 低 | 保守混乱 | `flow_widget.py` / `edit_dialogs.py` 削除または非推奨化 |
| R-06 | `palette_widget._add_function` の import 失敗 | 低 | 一部環境で無言失敗 | try/except + フォールバック追加 |
| R-07 | Windows / Linux のパス差異 | 低 | 無言失敗 | パステストを CI に追加 |
| R-08 | ユーザーコードマーカーの上書き | 低 | ユーザー編集消失 | マージのコーナーケーステスト追加 |

---

## 11. 引き継ぎチェックリスト

| # | 項目 | 検証方法 | 状態 |
|---|------|---------|------|
| 1 | `main` で CI が通る | GitHub Actions | ✅ |
| 2 | 4 つの仕様書が存在する | `docs/` | ✅ |
| 3 | 既知の制約（§7）が確認されている | 本ドキュメント | – |
| 4 | 未実装機能（§8）が受容されている | 本ドキュメント | – |
| 5 | リスク登録簿（§10）が確認されている | 本ドキュメント | – |
| 6 | サンプル生成が動作する | `SampleDataGenerator` | – |
| 7 | プロジェクト XML 往復が動作する | `project_to_xml` / `project_from_xml` | – |
| 8 | 生成 C コードが検証済み | `tools/verify_generated_code.py` | – |
| 9 | テストスイートがローカル実行可能 | `python tests/test_v2_2_p*.py` | – |
| 10 | 依存関係が文書化されている | 本ドキュメント §2.3 | – |
| 11 | UI が英語のみ | `main_window.py` のラベル | ✅ |
| 12 | CI ワークフローがリポジトリ直下 | `.github/workflows/check.yml` | ✅ |

---

## 12. 改訂履歴

| 版 | 日付 | 内容 |
|----|------|------|
| 1.0 | 2026-09-20 | 既存仕様書からの統合監査仕様書 |