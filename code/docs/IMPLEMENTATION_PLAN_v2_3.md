# `docs/IMPLEMENTATION_PLAN_v2_3.md`（完成版）

```markdown
# StaTable v2.3 実装計画書：新規プロジェクト機能

Version: 1.0
Date: 2026-09-21
Target: SPEC_OVERVIEW v2.3 / F-15
Status: 実装準備完了
Prerequisite: 調査レポート 6 種完了（B-1〜B-6 含む）

---

## 1. 目的

サンプルデータを消去し、空の Application 層から新規プロジェクトを開始する
機能（F-15）を StaTable に追加する。

---

## 2. 確定仕様

### 2.1 決定事項（最終）

| # | 論点 | 決定 |
|---|------|------|
| 1 | 起動時サンプル | **維持**（現状通り） |
| 2 | 新規時タブ数 | **1個**（`Application`, `layer_priority=5`） |
| 3 | 未保存確認 | **New / Open / Close の3箇所**（`_maybe_save()` に集約） |
| 4 | 変更フラグ | **`QWidget.windowModified`** を流用 |
| 5 | 共有ライブラリ | **クリア**（`RoleFunctionLibrary()` 等を再生成）★変更 |
| 6 | ConfigManager | **リセット**（`self.config_manager.reset()`） |
| 7 | Preferences | **保持** |
| 8 | TraceBall ログ | **保持** |
| 9 | ショートカット | **`"Ctrl+N"`**（文字列ベース、既存慣例に準拠）★変更 |
| 10 | ステータスバー通知 | **出す**（`"New project created"`、3000ms） |

### 2.2 決定#5 変更の背景

初期案では「プロジェクト横断の共有ライブラリ」として保持する設計だったが、
`open_project` がライブラリを置換する挙動（line 691-697）との非対称を解消
するため、`new_project` でも**クリア**する方針に変更。

これにより、`New` / `Open` の両方が「前プロジェクトのライブラリを引き継がない」
で対称となる。

### 2.3 決定#9 変更の背景（B-4 の結果）

既存の `setShortcut` はすべて文字列ベース（`"Ctrl+Shift+V"` 等）で統一
されている。`QKeySequence` は全ファイルで未使用。これに合わせて
`setShortcut("Ctrl+N")` を使用し、`QKeySequence` の import は追加しない。

### 2.4 競合チェック（B-4 の結果）

既存ショートカット：

| ショートカット | 用途 |
|---------------|------|
| `Ctrl+Shift+V` | Validate |
| `Ctrl+G` | Generate code |
| `Ctrl+Shift+G` | Generation settings |
| `Ctrl+Shift+S` | Save generated code |

→ **`Ctrl+N` は競合なし** ✅

---

## 3. 事前確認済み事項（B-1〜B-6 の結果）

| # | 項目 | 結果 | 実装への反映 |
|---|------|------|-------------|
| B-1 | `_get_current_state_machine()` | `None` 経路あり | テストで `assert sm is not None` を先に置く |
| B-2 | `output_directory` デフォルト | 空文字列 `""` | テスト期待値 OK |
| B-3 | `layer_priority` デフォルト | `5` | テスト期待値 OK |
| B-4 | `QKeySequence` 未使用、`setShortcut` 文字列 | 文字列 `"Ctrl+N"` を使用 | import 追加不要 |
| B-5 | `MainWindow(QMainWindow)` | `statusBar()` 利用可能 | 変更なし |
| B-6 | `open_project` 冒頭に未保存確認なし | `_maybe_save()` 追加で問題なし | 変更なし |

---

## 4. 実装順序（12ステップ）

各ステップは独立コミット。Step N 完了後にテストを実行。

### Step 1: `widgets.py` に `dataModified` シグナル追加

**変更ファイル**: `statable_gui/widgets.py`

**変更内容**:
- 冒頭 import に `from PySide6.QtCore import Signal` を追加（未 import なら）
- `class StateMachineTab(QWidget):` の直後に `dataModified = Signal()` を追加
- `__init__` 末尾（line 955-956 の直後）に2行追加：

```python
self.table.transition_changed.connect(self.dataModified)
self.settings.settings_changed.connect(self.dataModified)
```

**検証**: 既存12スイートが PASS することを確認（シグナル追加のみで動作変化なし）。

**ロールバック**: `git revert <commit>`

---

### Step 2: `main_window.py` に import 追加

**変更ファイル**: `statable_gui/main_window.py`

**変更内容**:
- 冒頭 import に追加（**QKeySequence は不要**／B-4 の結果）：
  - `from statable.global_defs import GlobalDefinitions`（未 import なら）
  - `from statable.state_machine import StateMachine`（未 import なら）
- 決定#5 変更に伴う追加 import：
  - `from statable_gui.libcntrl.role_function_library import RoleFunctionLibrary`
  - `from statable_gui.libcntrl.condition_library import ConditionLibrary`
  - `from statable_gui.libcntrl.literal_library import LiteralLibrary`
  （既に import 済みなら追加不要）

**検証**: `python -c "import statable_gui.main_window"` で import エラーなし。

---

### Step 3: `save_project` を bool 返却に変更

**変更ファイル**: `statable_gui/main_window.py`（line 575-658）

**変更内容**:
1. signature を `def save_project(self) -> bool:` に変更
2. line 596 の `return` → `return False`（キャンセル）
3. line 649 の後（成功パス）に追加：

```python
self.setWindowModified(False)
self._update_window_title()
return True
```

4. line 658 の後（例外パス）に `return False` 追加

**検証**: `test_v2_3_p1.py::test_save_project_returns_bool` が PASS。

---

### Step 4: `main_window.py` に新規メソッド5つを追加

**変更ファイル**: `statable_gui/main_window.py`（`MainWindow` クラス末尾）

**変更内容**: 以下5メソッドを追加：

#### 4.1 `new_project()`

```python
def new_project(self) -> None:
    """Start a new empty project.

    Preserves: Preferences, TraceBall log.
    Clears: tabs, global definitions, shared libraries,
            ConfigManager, windowModified flag.
    """
    if not self._maybe_save():
        return

    StaTableLogger.debug("MainWindow.new_project: start")

    # 1. Remove all tabs (close_all_tabs uses removeTab directly)
    self.close_all_tabs()

    # 2. Reset global definitions
    self.global_defs = GlobalDefinitions()
    self.global_defs.add_timer_variables()

    # 3. Clear shared libraries (decision #5, revised)
    self.role_function_library = RoleFunctionLibrary()
    self.condition_library = ConditionLibrary()
    self.literal_library = LiteralLibrary()

    # 4. Reset code generation config
    self.config_manager.reset()

    # 5. One empty Application layer
    empty_sm = StateMachine()
    empty_sm.layer_name = "Application"
    empty_sm.layer_priority = 5
    self.add_state_machine_tab("Application", empty_sm)

    # 6. Reset modified flag and title
    self.setWindowModified(False)
    self._update_window_title()

    # 7. Status bar notification
    self.statusBar().showMessage("New project created", 3000)

    StaTableLogger.debug("MainWindow.new_project: done")
```

#### 4.2 `_maybe_save()`

```python
def _maybe_save(self) -> bool:
    """Prompt to save if there are unsaved changes.

    Returns True to proceed, False to abort.
    """
    if not self.isWindowModified():
        return True

    ret = QMessageBox.warning(
        self,
        "Unsaved Changes",
        "The current project has unsaved changes.\n"
        "Do you want to save them before continuing?",
        QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
        QMessageBox.Save,
    )
    if ret == QMessageBox.Save:
        return self.save_project()
    return ret == QMessageBox.Discard
```

#### 4.3 `closeEvent()`

```python
def closeEvent(self, event) -> None:
    """Prompt on window close if there are unsaved changes."""
    if self._maybe_save():
        event.accept()
    else:
        event.ignore()
```

#### 4.4 `_update_window_title()`

```python
def _update_window_title(self) -> None:
    """Update window title with modified marker.

    Qt replaces [*] with '*' when setWindowModified(True).
    """
    self.setWindowTitle("Untitled[*] - StaTable")
```

#### 4.5 `_on_tab_data_modified()`

```python
def _on_tab_data_modified(self) -> None:
    """Slot connected to each StateMachineTab.dataModified signal."""
    self.setWindowModified(True)
    self._update_window_title()
```

**検証**: import エラーなし。GUI 手動起動で `Ctrl+N` 動作確認。

---

### Step 5: `create_menus` に New Project アクション追加

**変更ファイル**: `statable_gui/main_window.py`（line 346-349 付近）

**変更内容**: `open_action` の直前に以下を挿入：

```python
new_project_action = QAction("New Project...", self)
new_project_action.setShortcut("Ctrl+N")   # 既存慣例に合わせて文字列
new_project_action.triggered.connect(self.new_project)
file_menu.addAction(new_project_action)

file_menu.addSeparator()
```

**検証**: メニュー表示確認、`Ctrl+N` ショートカット動作確認。

---

### Step 6: `add_state_machine_tab` に `dataModified` 接続

**変更ファイル**: `statable_gui/main_window.py`（line 894 付近）

**変更内容**: `tab = StateMachineTab(...)` の直後に追加：

```python
tab.dataModified.connect(self._on_tab_data_modified)
```

**検証**: タブ生成時のエラーなし。セル編集で `windowModified` が
`True` になることを手動確認。

---

### Step 7: `add_new_tab` / `rename_tab_at` / `close_tab` に変更フラグ

**変更ファイル**: `statable_gui/main_window.py`

**変更内容**: 各メソッド成功パス末尾に2行追加：

```python
self.setWindowModified(True)
self._update_window_title()
```

**検証**: 各操作後にタイトルに `*` が付くことを確認。

---

### Step 8: `open_project` 冒頭に未保存確認

**変更ファイル**: `statable_gui/main_window.py`（line 660 付近）

**変更内容**: メソッド冒頭に追加：

```python
def open_project(self):
    if not self._maybe_save():
        return
    # ... 既存処理 ...
```

成功パス（line 686 の直後）にも追加：

```python
self.setWindowModified(False)
self._update_window_title()
```

**注意**: `setWindowModified(False)` は `add_state_machine_tab` 呼び出し
完了後（line 686 の直後）に置く。タブ追加時の `dataModified` 発火に
よる誤った `True` 設定を打ち消すため。

**検証**: 変更ありで `Open` 実行 → 確認ダイアログ表示。

---

### Step 9: `tests/test_v2_3_p1.py` 追加

**変更ファイル**: `tests/test_v2_3_p1.py`（新規）

**変更内容**: 14テスト（後述の「5. テストコード」を参照）

**検証**: 単体実行で 14 PASS / 0 FAIL。

---

### Step 10: 全テスト実行

**実行内容**:

```bash
cd code
python tests/test_v2_2_p1.py
# ... 既存12スイート ...
python tests/test_v2_3_p1.py
```

**期待**: **551 PASS / 0 FAIL / 2 SKIP**

---

### Step 11: CI ワークフロー更新

**変更ファイル**: `.github/workflows/check.yml`

**変更内容**: `tests` ジョブに以下を追加：

```yaml
python tests/test_v2_3_p1.py
```

**検証**: GitHub Actions で 13 スイートが実行されることを確認。

---

### Step 12: SPEC 差分適用

**変更ファイル**:
- `docs/SPEC_OVERVIEW_ja.md`
- `docs/SPEC_OVERVIEW_en.md`
- `docs/SPEC_SCREENS_ja.md`
- `docs/SPEC_SCREENS_en.md`

**変更内容**: v2.3 差分を適用。**決定#5 変更を反映**：

| セクション | 修正 |
|-----------|------|
| §1.5 用語集 | `dataModified` の説明は変更なし |
| §4.2.3 保持/リセット対象 | `shared libraries` を「保持」→「**クリア**」 |
| §4.2.4 `_maybe_save()` | 変更なし |
| §11.3 テスト内容 | `test_new_project_keeps_shared_libraries` → `test_new_project_clears_shared_libraries` |
| §15 改訂履歴 | v2.3 エントリに「決定#5 変更」を追記 |

**検証**: 目視レビュー。

---

## 5. テストコード（`tests/test_v2_3_p1.py`）

```python
"""Tests for v2.3 New Project feature."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication, QMessageBox


def _make_window():
    from statable_gui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    return MainWindow()


def test_new_project_creates_one_application_tab():
    win = _make_window()
    win.new_project()
    assert win.tab_widget.count() == 1
    assert win.tab_widget.tabText(0) == "Application"


def test_new_project_resets_state_machine():
    win = _make_window()
    win.new_project()
    sm = win._get_current_state_machine()          # B-1: None 経路あり
    assert sm is not None                          # B-1: 先に None チェック
    assert len(sm.states) == 0
    assert len(sm.events) == 0
    assert len(sm.transitions) == 0
    assert len(sm.role_functions) == 0
    assert sm.layer_name == "Application"
    assert sm.layer_priority == 5                  # B-3


def test_new_project_resets_global_defs():
    win = _make_window()
    win.new_project()
    assert len(win.global_defs.variables) == 0
    assert len(win.global_defs.flags) == 0
    assert len(win.global_defs.interrupts) == 0


def test_new_project_clears_shared_libraries():
    """Decision #5 (revised): shared libraries are cleared."""
    win = _make_window()
    # 起動時はサンプルから登録されたロール関数があるはず
    n_before = len(win.role_function_library.list_all())
    win.new_project()
    n_after = len(win.role_function_library.list_all())
    assert n_after == 0
    assert len(win.condition_library.list_all()) == 0
    assert len(win.literal_library.list_all()) == 0


def test_new_project_resets_config_manager():
    """Decision #6 + B-2: output_directory default is empty string."""
    win = _make_window()
    win.config_manager.update(output_directory="/tmp/xxx")
    win.new_project()
    assert win.config_manager.get_config().output_directory == ""


def test_new_project_keeps_preferences():
    """Decision #7."""
    win = _make_window()
    prefs_before = win.prefs
    win.new_project()
    assert win.prefs is prefs_before


def test_new_project_clears_window_modified():
    win = _make_window()
    win.setWindowModified(True)
    win.new_project()
    assert not win.isWindowModified()


def test_new_project_cancelled_by_user():
    win = _make_window()
    win.setWindowModified(True)
    with patch.object(QMessageBox, "warning",
                      return_value=QMessageBox.Cancel):
        win.new_project()
    assert win.tab_widget.count() >= 1


def test_new_project_discard_proceeds():
    win = _make_window()
    win.setWindowModified(True)
    with patch.object(QMessageBox, "warning",
                      return_value=QMessageBox.Discard):
        win.new_project()
    assert win.tab_widget.count() == 1
    assert win.tab_widget.tabText(0) == "Application"


def test_new_project_save_calls_save_project():
    win = _make_window()
    win.setWindowModified(True)
    with patch.object(QMessageBox, "warning",
                      return_value=QMessageBox.Save), \
         patch.object(win, "save_project", return_value=True) as mock_save:
        win.new_project()
    mock_save.assert_called_once()
    assert win.tab_widget.count() == 1


def test_maybe_save_no_changes_returns_true():
    win = _make_window()
    win.setWindowModified(False)
    assert win._maybe_save() is True


def test_save_project_returns_bool():
    win = _make_window()
    with patch("statable_gui.main_window.QFileDialog.getSaveFileName",
               return_value=("", "")):
        result = win.save_project()
    assert result is False


def test_tab_data_modified_signal_exists():
    win = _make_window()
    tab = win.tab_widget.widget(0)
    assert hasattr(tab, "dataModified")


def test_tab_data_modified_sets_window_modified():
    win = _make_window()
    win.setWindowModified(False)
    tab = win.tab_widget.widget(0)
    tab.dataModified.emit()
    assert win.isWindowModified()


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in list(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed} PASS / {failed} FAIL")
    sys.exit(1 if failed else 0)
```

---

## 6. 実装順序の依存関係

```
Step 1 (widgets.dataModified)
  └─→ Step 6 (add_state_machine_tab 接続)

Step 2 (import)
  └─→ Step 3 (save_project bool 化)
       └─→ Step 4 (_maybe_save → save_project 呼び出し)

Step 4 (new_project / _maybe_save / closeEvent)
  ├─→ Step 5 (create_menus → new_project 接続)
  └─→ Step 8 (open_project → _maybe_save 接続)

Step 9 (test_v2_3_p1.py)
  └─→ Step 10 (全テスト)
       └─→ Step 11 (CI)
            └─→ Step 12 (SPEC)
```

**並列可能**: Step 1 と Step 2、Step 7 と Step 8。

---

## 7. ロールバック単位

| 障害箇所 | ロールバック範囲 |
|---------|-----------------|
| Step 1 で widgets.py が壊れた | Step 1 のみ revert |
| Step 3 で既存 save_project 呼び出しが壊れた | Step 3 のみ revert（Step 4 以降は中断） |
| Step 4 で new_project がエラー | Step 4 のみ revert（Step 5-8 は未着手に戻す） |
| Step 9 でテスト失敗 | Step 4-8 のいずれかに問題。原因 Step を特定して revert |

**原則**: 各 Step は独立コミット。
`git commit -m "v2.3 Step N: <内容>"` の形式で。

---

## 8. 手動テスト項目

実装完了後、以下を GUI で手動確認：

| # | 操作 | 期待結果 |
|---|------|---------|
| M-1 | 起動 | サンプルプロジェクトが表示される（決定#1） |
| M-2 | `File > New Project...` | 空の Application タブ1個。サンプル消去 |
| M-3 | `Ctrl+N` | M-2 と同じ |
| M-4 | サンプル状態で `Ctrl+N` | 「未保存変更あり」確認ダイアログ |
| M-5 | ダイアログで Cancel | タブ変化なし |
| M-6 | ダイアログで Discard | 空プロジェクトに遷移 |
| M-7 | ダイアログで Save → 保存成功 | 空プロジェクトに遷移 |
| M-8 | ダイアログで Save → 保存キャンセル | タブ変化なし |
| M-9 | 空プロジェクトでセル編集 | タイトルに `*` 付与 |
| M-10 | タイトル `*` 付きで `File > Save` | 保存成功で `*` 消去 |
| M-11 | `*` 付きでウィンドウ閉じる | 未保存確認 |
| M-12 | `*` 付きで `File > Open` | 未保存確認 |
| M-13 | 空プロジェクトで `File > New Project` | 確認なしで新規作成（変更なし扱い） |
| M-14 | ステータスバー | "New project created" が3秒表示 |
| M-15 | New 後の共有ライブラリ | 空になっている（決定#5 変更） |
| M-16 | Preferences | 保持されている |
| M-17 | TraceBall ログ | 保持されている |

---

## 9. リスクと緩和策

| # | リスク | 緩和策 |
|---|-------|--------|
| R-1 | `QApplication` を複数テストで生成 → リーク | `QApplication.instance() or QApplication([])` パターン |
| R-2 | `QMessageBox` のモックが PySide6 で動かない | `unittest.mock.patch.object` で確認 |
| R-3 | `windowModified` が `QMainWindow` で動かない | Step 1 完了時に手動確認 |
| R-4 | `save_project` の bool 化で既存呼び出しが壊れる | 既存呼び出しは戻り値未使用のため影響なし |
| R-5 | `close_all_tabs` が内部で `close_tab` を呼び二重削除 | R-1 確認済み（直接 `removeTab` 使用） |
| R-6 | `dataModified` の signal-to-signal 接続が動かない | PySide6 で標準サポート。Step 6 完了時に確認 |

---

## 10. 完了条件

- [ ] 全 12 ステップ完了
- [ ] `551 PASS / 0 FAIL / 2 SKIP` 達成
- [ ] CI で 13 スイート PASS
- [ ] 手動テスト M-1〜M-17 全項目 PASS
- [ ] SPEC_OVERVIEW_ja.md / en.md 更新完了
- [ ] SPEC_SCREENS_ja.md / en.md 更新完了

---

## 11. 参考ドキュメント

- `docs/SPEC_OVERVIEW_ja.md` v2.3
- `docs/SPEC_OVERVIEW_en.md` v2.3
- 調査レポート 6 種：
  - `tools/investigate_new_project.py`（第1段階）
  - `tools/investigate_new_project_step2.py`（第2段階）
  - `tools/verify_new_project_remaining.py`（R-1/R-2/R-3）
  - `tools/verify_new_project_final.py`（V-1〜V-8）
  - `tools/verify_new_project_code_facts.py`（B-1〜B-6）

---

以上。
```

