# `docs/SPEC_SCREENS_ja.md` v2.4（画面仕様書、決定#5 反映済み）

**注記**：既存の `SPEC_SCREENS_ja.md` の内容が手元にないため、`SPEC_OVERVIEW_ja.md` v2.3 の記述と事前調査結果から**再構成した完全版**を出力します。既存ファイルと差異がある場合は、該当セクションのみ差分適用してください。

```markdown
# StaTable 画面仕様書 v2.4（日本語）

Version: 2.4
Date: 2026-09-22
Scope: StaTable GUI 画面全体
Prerequisite: `SPEC_OVERVIEW_ja.md` v2.3 参照

---

## 目次

1. 画面一覧
2. MainWindow
3. メニューバー
4. ツールバー
5. タブウィジェット
6. ダイアログ一覧
7. 新規プロジェクト機能（v2.3）
8. 未保存確認ダイアログ（v2.3）
9. ウィンドウタイトル（v2.3）
10. ステータスバー（v2.3）
11. 改訂履歴

---

## 1. 画面一覧

| # | 画面 / ウィジェット | クラス | ファイル | モーダル |
|---|---------------------|--------|---------|---------|
| 1 | メインウィンドウ | `MainWindow` | `statable_gui/main_window.py` | – |
| 2 | ステートマシンタブ | `StateMachineTab` | `statable_gui/widgets.py` | – |
| 3 | 設定パネル | `SettingsPanel` | `statable_gui/widgets.py` | – |
| 4 | Mermaid プレビュー | `MermaidWidget` | `statable_gui/widgets.py` | – |
| 5 | 遷移マトリクス | `MatrixTableWidget` | `statable_gui/matrix_table.py` | – |
| 6 | グローバル定義 | `GlobalDefinitionsDialog` | `statable_gui/global_defs_dialog.py` | モーダル |
| 7 | 型定義マネージャ | `TypeManagerDialog` | `statable_gui/common_widgets.py` | モーダル |
| 8 | イベント定義 | `EventDefinitionDialog` | `statable_gui/event_definition_dialog.py` | モーダル |
| 9 | イベント配送設定 | `EventDeliverySettingsDialog` | `statable_gui/event_delivery_settings_dialog.py` | モーダル |
| 10 | 割り込みハンドラ編集 | `InterruptHandlerEditDialog` | `statable_gui/interrupt_handler_edit_dialog.py` | モーダル |
| 11 | 層設定 | `LayerSettingsDialog` | `statable_gui/layer_settings_dialog.py` | モーダル |
| 12 | 検証ダイアログ | `ValidationDialog` | `statable_gui/validation_dialog.py` | モーダル |
| 13 | コード生成 | `CodeGenerationDialog` | `statable_gui/code_generation_dialog.py` | モーダル |
| 14 | コード生成設定 | `CodeGenerationSettingsDialog` | `statable_gui/code_generation_settings_dialog.py` | モーダル |
| 15 | 遷移エディタ | `ActionEditorDialog` | `statable_gui/transition_editor_direct/dialog.py` | モーダル |
| 16 | TraceBall ログ | `TraceBallWidget` | `statable_gui/traceball.py` | ドック |
| 17 | **未保存確認ダイアログ（v2.3）** | `QMessageBox` | （Qt 標準） | モーダル |
| 18 | **タブ名入力（v2.3 既存）** | `QInputDialog` | （Qt 標準） | モーダル |

---

## 2. MainWindow

### 2.1 全体レイアウト

```
┌────────────────────────────────────────────────────────────┐
│ MainWindow (QMainWindow)                                   │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ メニューバー（File / Edit / Validate / Code generation / View）│
│ ├────────────────────────────────────────────────────────┤ │
│ │ ツールバー                                              │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ ┌────────────────────────────────────────────────────┐ │ │
│ │ │ QTabWidget                                          │ │ │
│ │ │ ┌─────────────────────────────────────────────────┐│ │ │
│ │ │ │ StateMachineTab "Application"                   ││ │ │
│ │ │ │ ┌──────────────────────────┬──────────────────┐││ │ │
│ │ │ │ │ MatrixTableWidget        │ SettingsPanel    │││ │ │
│ │ │ │ │ （遷移マトリクス）        │ （状態/ロール関数）│││ │ │
│ │ │ │ ├──────────────────────────┤                  │││ │ │
│ │ │ │ │ MermaidWidget            │                  │││ │ │
│ │ │ │ │ （状態図プレビュー）      │                  │││ │ │
│ │ │ │ └──────────────────────────┴──────────────────┘││ │ │
│ │ │ └─────────────────────────────────────────────────┘│ │ │
│ │ └────────────────────────────────────────────────────┘ │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ TraceBall ドック（非表示、トグル可）                    │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ ステータスバー                                          │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 2.2 属性

| 属性 | 値 |
|------|-----|
| 基底クラス | `QMainWindow` |
| 初期サイズ | `WINDOW_WIDTH × WINDOW_HEIGHT` |
| ウィンドウタイトル | `Untitled[*] - StaTable`（v2.3） |
| メニューバー | 5メニュー（§3 参照） |
| ツールバー | `TopToolBarArea` |
| 中央ウィジェット | `QTabWidget` |
| ドックウィジェット | `TraceBallWidget`（`BottomDockWidgetArea`、初期非表示） |
| ステータスバー | `QStatusBar`（v2.3 で使用開始） |

---

## 3. メニューバー

### 3.1 メニュー構成（v2.3）

```
File
├── New Project...          (Ctrl+N)         ★v2.3 追加
├── ─────────────
├── Open Project...         (なし)
├── Save Project...         (なし)
├── Rename Tab...           (なし)
├── ─────────────
└── New State Machine       (なし)

Edit
├── Global Definitions...   (なし)
├── Type Definitions...     (なし)
├── Event Definitions...    (なし)
├── Event Delivery Settings... (なし)
├── Interrupt Handlers...   (なし)
└── Layer Settings...       (なし)

Validate(&V)
└── Validate Project...     (Ctrl+Shift+V)

Code generation(&G)
├── Generate Code...        (Ctrl+G)
├── Generation Settings...  (Ctrl+Shift+G)
└── Save Generated Code...  (Ctrl+Shift+S)

View
└── TraceBall               (チェック可能)
```

### 3.2 File メニュー詳細

| # | 項目 | ショートカット | 接続先 | v2.3 |
|---|------|--------------|--------|------|
| 1 | **New Project...** | `Ctrl+N` | `MainWindow.new_project` | ★追加 |
| 2 | ───────────── | – | – | ★追加 |
| 3 | Open Project... | なし | `MainWindow.open_project` | 既存 |
| 4 | Save Project... | なし | `MainWindow.save_project` | 既存 |
| 5 | Rename Tab... | なし | `MainWindow.rename_current_tab` | 既存 |
| 6 | ───────────── | – | – | 既存 |
| 7 | New State Machine | なし | `MainWindow.add_new_tab` | 既存 |

### 3.3 既存ショートカット一覧（v2.3）

| ショートカット | メニュー | 用途 |
|---------------|---------|------|
| `Ctrl+N` | File | 新規プロジェクト ★追加 |
| `Ctrl+Shift+V` | Validate | 検証実行 |
| `Ctrl+G` | Code generation | コード生成 |
| `Ctrl+Shift+G` | Code generation | 生成設定 |
| `Ctrl+Shift+S` | Code generation | 生成コード保存 |

**競合なし**：`Ctrl+N` は v2.3 まで未使用。既存ショートカットと衝突しない。

---

## 4. ツールバー

### 4.1 ツールバー構成

`TopToolBarArea` に配置。`MainWindow.create_toolbar()` で生成。

| # | ボタン | 接続先 |
|---|--------|--------|
| 1 | Global definitions | `open_global_defs_dialog` |
| 2 | Type definitions | `open_type_manager` |
| 3 | Event definitions | `open_event_definition_dialog` |
| 4 | Event delivery | `open_event_delivery_settings` |
| 5 | Interrupts | `open_interrupt_settings` |
| 6 | Layer settings | `open_layer_settings` |
| 7 | Validate | `open_validation_dialog` |
| 8 | Generate | `open_code_generation_dialog` |
| 9 | Generation settings | `open_code_generation_settings` |
| 10 | Save generated code | `save_generated_code_direct` |
| 11 | Show log | `toggle_traceball`（チェック可能） |

**v2.3 変更**：ツールバーへの `New Project` ボタン追加は**なし**（メニューのみ）。理由：既存ツールバーの一貫性（編集系・生成系のみ）を保つ。

---

## 5. タブウィジェット

### 5.1 タブ構成

`QTabWidget` に各層（Layer）をタブとして配置。各タブは `StateMachineTab` インスタンス。

### 5.2 StateMachineTab レイアウト

```
┌──────────────────────────────────────────────────────────┐
│ QHBoxLayout                                              │
│ ┌────────────────────────────────┬──────────────────────┐│
│ │ QSplitter (Vertical)           │ SettingsPanel        ││
│ │ ┌────────────────────────────┐ │ ┌──────────────────┐││
│ │ │ MatrixTableWidget          │ │ │ State list タブ  │││
│ │ │ （遷移マトリクス）          │ │ │ Role function タブ│││
│ │ │ 最小高 300px               │ │ └──────────────────┘││
│ │ ├────────────────────────────┤ │                      ││
│ │ │ MermaidWidget              │ │                      ││
│ │ │ （状態図プレビュー）        │ │                      ││
│ │ │ 最小高 MERMAID_PREVIEW_MIN_HEIGHT│                  ││
│ │ └────────────────────────────┘ │                      ││
│ └────────────────────────────────┴──────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

### 5.3 v2.3 追加シグナル

| シグナル | 発火元 | 接続先 |
|---------|--------|--------|
| `dataModified` | `__init__` 内で signal-to-signal 接続 | `MainWindow._on_tab_data_modified` |

内部接続（`__init__` 末尾）：
```python
self.table.transition_changed.connect(self.dataModified)
self.settings.settings_changed.connect(self.dataModified)

```

### 5.4 v3.11 追加配線

| 項目 | 内容 |
|------|------|
| `layer_names_provider` | `StateMachineTab` が `SettingsPanel` に伝播 |
| 用途 | Namespace コンボボックスに全タブのレイヤ名を候補表示 |
| 追加元 | `MainWindow._get_all_layer_names()`（v2.4） |

---

## 6. ダイアログ一覧

| # | ダイアログ | モーダル | `exec()` 戻り値使用 | v2.3 での変更フラグ |
|---|-----------|---------|-------------------|-------------------|
| 1 | `GlobalDefinitionsDialog` | モーダル | **なし**（C-36） | 反映されない |
| 2 | `TypeManagerDialog` | モーダル | **なし**（C-37） | 反映されない |
| 3 | `EventDefinitionDialog` | モーダル | あり（`QDialog.Accepted`） | 反映されない（C-36） |
| 4 | `EventDeliverySettingsDialog` | モーダル | あり | 反映されない（C-37） |
| 5 | `InterruptHandlerEditDialog` | モーダル | **なし**（C-37） | 反映されない |
| 6 | `LayerSettingsDialog` | モーダル | あり（`_on_ok` → `accept`） | 反映されない（C-37） |
| 7 | `ValidationDialog` | モーダル | なし | – |
| 8 | `CodeGenerationDialog` | モーダル | なし | – |
| 9 | `CodeGenerationSettingsDialog` | モーダル | なし | – |
| 10 | `ActionEditorDialog` | モーダル | – | タブ内編集は反映 |

**v2.3 のスコープ**：ダイアログ経由の編集は `windowModified` に反映されない（C-36〜C-39）。タブ内編集のみ反映。

---

## 7. 新規プロジェクト機能（v2.3 / F-15）

### 7.1 画面遷移

```
┌─────────────────────────┐
│ MainWindow              │
│ （サンプルプロジェクト表示中）│
└───────────┬─────────────┘
            │
            │ File > New Project... または Ctrl+N
            ▼
┌─────────────────────────┐
│ 未保存確認ダイアログ       │ ← windowModified == True の場合のみ
│ （Save / Discard / Cancel）│
└───────────┬─────────────┘
            │
            ├── Cancel ────→ MainWindow（変化なし）
            │
            ├── Save ────→ 保存ダイアログ ──→ 保存成功 ──┐
            │                                └── 保存失敗 ──→ MainWindow（変化なし）
            │
            └── Discard ────────────────────────────────┐
                                                        │
                                                        ▼
                                        ┌─────────────────────────┐
                                        │ MainWindow（新規プロジェクト）│
                                        │ ・Application タブ1個      │
                                        │ ・状態/イベント/遷移 0件    │
                                        │ ・GlobalDefinitions 空     │
                                        │ ・共有ライブラリ 空        │
                                        │ ・ConfigManager デフォルト │
                                        │ ・windowModified = False   │
                                        │ ・タイトル: Untitled       │
                                        │ ・ステータスバー: 通知3秒   │
                                        └─────────────────────────┘
```

### 7.2 新規プロジェクト実行時の状態変化

| 対象 | 変化 | 決定# |
|------|------|-------|
| タブ | 全削除 → `Application` タブ1個 | #2 |
| 状態/イベント/遷移 | 全削除（0件） | – |
| `StateMachine.role_functions` | 全削除（0件） | – |
| `cell_actions` / `cell_relations` | 全削除（`{}`） | – |
| GlobalDefinitions | 再生成（空） | – |
| **RoleFunctionLibrary** | **再生成（空）** | **#5 変更** |
| **ConditionLibrary** | **再生成（空）** | **#5 変更** |
| **LiteralLibrary** | **再生成（空）** | **#5 変更** |
| ConfigManager | `reset()` | #6 |
| Preferences | 保持 | #7 |
| TraceBall ログ | 保持 | #8 |
| `windowModified` | `False` | #4 |

### 7.3 メニュー項目の表示仕様

| 項目 | 表示テキスト | ショートカット | ツールチップ |
|------|-------------|--------------|-------------|
| New Project | `New Project...` | `Ctrl+N` | なし（デフォルト） |

### 7.4 起動時との対比

| 動作 | 起動時 | New Project 時 |
|------|-------|---------------|
| タブ | `Application`（サンプル） | `Application`（空） |
| 状態/イベント/遷移 | サンプルデータ | 空 |
| GlobalDefinitions | デモデータ | 空 |
| 共有ライブラリ | サンプル登録済み | 空 |
| ConfigManager | デフォルト | デフォルト（`reset()`） |
| Preferences | ロード済み | 保持 |
| TraceBall ログ | 起動ログ | 保持（前のログ） |
| タイトル | 初期は `StaTable - State Transition Editor` | `Untitled[*] - StaTable` |

**注意**：起動時のタイトルは v2.3 でも `StaTable - State Transition Editor` のまま。`_update_window_title()` は `new_project` / `open_project` / `save_project` 成功時 / タブ編集時にのみ呼ばれる。

---

## 8. 未保存確認ダイアログ（v2.3）

### 8.1 表示条件

`MainWindow._maybe_save()` から呼ばれる。以下の3箇所で実行：

| トリガ | 呼び出し元 |
|--------|-----------|
| `File > New Project...` / `Ctrl+N` | `MainWindow.new_project` 冒頭 |
| `File > Open Project...` | `MainWindow.open_project` 冒頭 |
| ウィンドウクローズ | `MainWindow.closeEvent` |

### 8.2 ダイアログ仕様

| 項目 | 値 |
|------|-----|
| クラス | `QMessageBox` |
| アイコン | `QMessageBox.Warning` |
| タイトル | `"Unsaved Changes"` |
| メッセージ | `"The current project has unsaved changes.\nDo you want to save them before continuing?"` |
| ボタン | `Save` / `Discard` / `Cancel` |
| デフォルトボタン | `Save` |

### 8.3 ボタン別動作

| ボタン | `_maybe_save()` の戻り値 | 呼び出し元の動作 |
|--------|------------------------|----------------|
| Save | `save_project()` の戻り値 | 保存成功 → 続行、保存キャンセル/失敗 → 中止 |
| Discard | `True` | 続行 |
| Cancel | `False` | 中止 |

### 8.4 変更なしの場合

`windowModified == False` の場合は**ダイアログを表示せず** `True` を返す。

### 8.5 表示例（テキストベース）

```
┌─────────────────────────────────────────────────┐
│  ⚠  Unsaved Changes                             │
│                                                 │
│  The current project has unsaved changes.       │
│  Do you want to save them before continuing?    │
│                                                 │
│       [ Save ]  [ Discard ]  [ Cancel ]         │
└─────────────────────────────────────────────────┘
```

---

## 9. ウィンドウタイトル（v2.3）

### 9.1 タイトル形式

| 状態 | タイトル |
|------|---------|
| 起動時（v2.0 から変更なし） | `StaTable - State Transition Editor` |
| `new_project` 実行後 | `Untitled[*] - StaTable` |
| `open_project` 成功後 | `Untitled[*] - StaTable` |
| `save_project` 成功後 | `Untitled[*] - StaTable` |
| `windowModified == True` 時 | `Untitled* - StaTable`（`[*]` が `*` に置換） |
| `windowModified == False` 時 | `Untitled - StaTable`（`[*]` が除去） |

### 9.2 `[*]` プレースホルダ

Qt の `QMainWindow.setWindowTitle("[*] ...")` と `setWindowModified(bool)` の組み合わせで動作：

```python
def _update_window_title(self) -> None:
    self.setWindowTitle("Untitled[*] - StaTable")
```

`setWindowModified(True)` → タイトルが `Untitled* - StaTable` に
`setWindowModified(False)` → タイトルが `Untitled - StaTable` に

### 9.3 制約

- プロジェクトファイル名（`project_path`）の保持は v2.3 では未実装。常に `Untitled` 固定。
- 将来の v2.4 以降で `project_path` を保持し、`<ファイル名>[*] - StaTable` に拡張する余地あり。

---

## 10. ステータスバー（v2.3）

### 10.1 使用箇所

| トリガ | メッセージ | タイムアウト |
|--------|-----------|-------------|
| `new_project` 完了時 | `"New project created"` | 3000 ms |
| `open_project` 完了時 | （未実装／将来追加） | – |
| `save_project` 成功時 | （未実装／将来追加） | – |

### 10.2 表示例

```
┌─────────────────────────────────────────────────┐
│ New project created                             │  ← 3秒表示
└─────────────────────────────────────────────────┘
```

### 10.3 `QMainWindow` 基底の確認

`MainWindow(QMainWindow)` を継承しているため、`statusBar()` が自動利用可能（B-5 確認済み）。

---

## 11. 改訂履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-20 | 初版 |
| 2.0 | 2026-09-20 | 詳細版（ダイアログ一覧、タブ構造追加） |
| 2.3 | 2026-09-21 | 新規プロジェクト機能（F-15）： |
| | | - §1：画面一覧に「未保存確認ダイアログ」「タブ名入力」を追加 |
| | | - §3：File メニューに `New Project...`（Ctrl+N）を追加、ショートカット一覧更新 |
| | | - §4：ツールバーへの New Project 追加はなし（メニューのみ）を明記 |
| | | - §5：`StateMachineTab.dataModified` シグナル追加 |
| | | - §6：ダイアログの `windowModified` 反映状況を表に追加（C-36〜C-39） |
| | | - §7：新規プロジェクト機能セクション追加（画面遷移、状態変化、決定#5 反映） |
| | | - §8：未保存確認ダイアログ仕様追加 |
| | | - §9：ウィンドウタイトル仕様追加（`Untitled[*] - StaTable`） |
| | | - §10：ステータスバー仕様追加（v2.3 で使用開始） |
| | | - §11：改訂履歴（本エントリ） |

| 2.4 | 2026-09-22 | UI 整理・Namespace コンボ対応： |
| | | - §5.4: `layer_names_provider` 配線を追記 |
| | | - §11: 改訂履歴（本エントリ） |
---

以上、`SPEC_SCREENS_ja.md` v2.3（決定#5 反映済み）の完全版です。
```

---

**注意**：本ファイルは**再構成版**です。既存の `SPEC_SCREENS_ja.md` と内容が異なる場合、以下の対応を推奨します：

1. 既存ファイルの構成（章立て、粒度）を確認
2. 本章立てに合わせて差分のみをマージ
3. 特に §3（メニューバー）、§7（新規プロジェクト）、§8（未保存確認）の3セクションが本質的な追加

「次」で `docs/SPEC_SCREENS_en.md`（同内容の英語版）を出力します。