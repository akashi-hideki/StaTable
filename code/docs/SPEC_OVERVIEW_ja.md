# `docs/SPEC_OVERVIEW_ja.md` v2.3（決定#5 反映済み完全版）

```markdown
# StaTable 全体仕様書 v2.3（日本語、詳細版）

Version: 2.3
Date: 2026-09-21
Scope: StaTable プロジェクト全体
Prerequisite: ソースツリーが利用可能（`statable/`、`statable_gui/`、`codegen/`）

---

## 目次

1. プロジェクト概要
2. アーキテクチャ
3. データモデル層（`statable/`）
4. GUI層（`statable_gui/`）
5. 共有ライブラリ（`statable_gui/libcntrl/`）
6. 遷移エディタ（`statable_gui/transition_editor_direct/`）
7. コード生成（`codegen/`）
8. CI/CD
9. 開発環境
10. コーディング規約
11. テスト方針
12. 既知の制約
13. 用語集
14. 付録
15. 改訂履歴

---

## 1. プロジェクト概要

### 1.1 目的

**StaTable** は、組み込みシステム向けの状態遷移設計から C コード生成までのワークフロー全体を支援する GUI ツールである。設計者は状態遷移を表形式で定義し、条件とアクションをドラッグ＆ドロップで編集し、組み込み向け C コードを直接生成する。

### 1.2 対象ユーザー

| ユーザー種別 | 想定用途 |
|-------------|---------|
| 組み込みエンジニア | 状態機械設計、C コード生成 |
| 設計レビュア | 生成された Mermaid 図・遷移テーブルによるレビュー |
| テストエンジニア | 生成コードの単体テスト・CI検証 |

### 1.3 機能一覧

| # | 機能 | 概要 |
|---|------|------|
| F-01 | 多層ステートマシン編集 | タブで層を表現、優先度で実行順を制御 |
| F-02 | 遷移マトリクス編集 | (状態 × イベント) マトリクス上のセル編集 |
| F-03 | ドラッグ＆ドロップフローエディタ | 遷移条件・pre/else アクションを視覚配置 |
| F-04 | ロール関数ライブラリ | 名前空間対応の共有可能な関数定義 |
| F-05 | 条件・リテラルライブラリ | 条件テンプレートとリテラル化 |
| F-06 | グローバル定義 | 変数、フラグ、割り込み、タイマー、キュー |
| F-07 | Mermaid 図生成 | 状態図の自動生成とプレビュー |
| F-08 | C コード生成 | マーカー付き14ファイル |
| F-09 | ユーザコード保持 | マーカー方式マージで再生成時もユーザコードを保持 |
| F-10 | 検証・AI診断 | 生成前の一貫性検証（35ルール、11バリデータ） |
| F-11 | プロジェクト XML 永続化 | プロジェクト全体の保存・読込 |
| F-12 | CI 検証 | GitHub Actions による自動チェック |
| F-13 | MISRA C:2012 対応 | 生成 C コードを MISRA C:2012 で検証（情報提供目的） |
| F-14 | セル単位 AI アクション | v2.2：17種の変更アクション（legacy 10 + cell-level 7） |
| F-15 | 新規プロジェクト | v2.3：サンプルを消去し空の Application 層から開始（Ctrl+N） |

### 1.4 非機能要件

| 項目 | 要件 |
|------|------|
| 対応 OS | Windows 10/11、Linux（Ubuntu 22.04+） |
| Python | 3.12 |
| GUI | PySide6（Qt 6） |
| I/O | XML（UTF-8）、C ソース（UTF-8） |
| 依存関係 | PySide6、pycparser（テストのみ） |
| 生成コード | C99 準拠、`static` 関数を多用 |
| テスト | 13スイート（`tests/test_v2_2_p*.py` + `tests/test_v2_3_p1.py`）、551 PASS / 2 SKIP |
| CI | GitHub Actions、`ubuntu-latest` |
| MISRA | cppcheck 2.x + MISRA addon（情報提供のみ） |

### 1.5 用語集

| 用語 | 定義 |
|------|------|
| 層（Layer） | タブ名で識別されるステートマシン群。`sm.layer_name` |
| セル（Cell） | (状態, イベント) の組。遷移関数の最小単位 |
| セル関数 | 1つのセルを処理する `static` 関数 |
| ロール関数 | 遷移・条件・ISR から呼ばれる関数 |
| 名前空間（namespace） | ロール関数の所属層または明示的名前空間 |
| qualified_name | `namespace.name` 形式の一意名（例：`Driver.Init`） |
| call_sites | 各ロール関数の呼び出しセル一覧 |
| transition_id | call_sites 内のインデックス。`0xFFFF` = 一致なし |
| スーパー include | `statable_all.h`。全生成ヘッダを集約 |
| スーパーループ | `{project}_run.c`。全層のメインループ |
| マーカー | ユーザコード保持用コメント（`[[STABLE_...]]`） |
| MISRA 抑制 | MISRA C:2012 からの文書化された意図的逸脱 |
| セルアクション | v2.2：セルに付属する遷移非依存の `ActionStep` |
| セル関係 | v2.2：セル内遷移間の `TransitionRelation`（sequential/exclusive/group） |
| `early_return` | v2.2：`True` = Commit（同セル内の後続遷移評価を停止） |
| `label` | v2.2：セル内の安定識別子（例：`"T1"`、`"T2"`） |
| `windowModified` | v2.3：Qt 標準の変更フラグ。`[*]` プレースホルダでタイトルに反映 |
| `_maybe_save()` | v2.3：未保存確認ダイアログを一元化する MainWindow メソッド |
| `dataModified` | v2.3：`StateMachineTab` の変更通知シグナル |

---

## 2. アーキテクチャ

### 2.1 全体構成

```
┌──────────────────────────────────────────────────────────────┐
│                        StaTable                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  statable_gui/                         │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │ main_window.py  : MainWindow                     │  │  │
│  │  │ widgets.py      : StateMachineTab, SettingsPanel │  │  │
│  │  │ matrix_table.py : MatrixTableWidget              │  │  │
│  │  │ code_generation_*.py : Dialogs                   │  │  │
│  │  │ + various edit dialogs                           │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────┐  ┌───────────────────┐   │  │
│  │  │ transition_editor_direct │  │ libcntrl/         │   │  │
│  │  │ (D&D editor)             │  │ (Shared libraries)│   │  │
│  │  └──────────────────────────┘  └───────────────────┘   │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │ 呼出し                          │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    codegen/                            │  │
│  │  CCodeGenerator + 15 sub-generators                    │  │
│  │  + validate/ subsystem (v2.2: 20+ files)               │  │
│  │  (generated C is MISRA C:2012-aware; see §7.4)         │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │ 読込                            │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    statable/                           │  │
│  │  StateMachine, GlobalDefinitions, XML I/O              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 層構成

| 層 | パッケージ | 責務 | 依存先 |
|----|-----------|------|--------|
| プレゼンテーション | `statable_gui/` | GUI 表示とユーザ操作 | codegen, statable, libcntrl |
| D&D 編集 | `statable_gui/transition_editor_direct/` | セル単位の遷移編集 UI | statable_gui |
| 共有ライブラリ | `statable_gui/libcntrl/` | ロール関数等の共有管理 | （なし） |
| コード生成 | `codegen/` | C コード生成 + 検証 | statable |
| データモデル | `statable/` | ステートマシン、グローバル定義、XML | （なし） |

**依存方向**：`statable_gui` → `codegen` → `statable`。逆依存なし。

**例外（v2.2）**：`statable/xml_io.py` は `try/except ImportError` フォールバック付きで `statable_gui.libcntrl` を import する（§12 C-22 参照）。

### 2.3 詳細依存関係

```
statable_gui/main_window.py
  ├── statable.state_machine.StateMachine
  ├── statable.xml_io.project_to_xml / project_from_xml
  ├── statable.global_defs.GlobalDefinitions
  ├── statable.sample_data.create_sample_*
  ├── statable_gui.libcntrl.role_function_library.RoleFunctionLibrary
  ├── statable_gui.libcntrl.condition_library.ConditionLibrary
  ├── statable_gui.libcntrl.literal_library.LiteralLibrary
  ├── codegen.c_code_generator.CCodeGenerator
  ├── codegen.sample_data.SampleDataGenerator
  ├── codegen.config.ConfigManager
  ├── statable_gui.code_generation_dialog.CodeGenerationDialog
  ├── statable_gui.code_generation_settings_dialog.CodeGenerationSettingsDialog
  └── statable_gui.widgets.StateMachineTab
```

### 2.4 データフロー

#### 2.4.1 起動 → 編集

```
MainWindow.__init__
  ├── create_sample_global_defs()        # デモデータ
  ├── RoleFunctionLibrary()              # 空ライブラリ
  ├── ConditionLibrary()                 # 空ライブラリ
  ├── LiteralLibrary()                   # 空ライブラリ
  ├── create_sample_state_machine()      # デモステートマシン
  ├── add_state_machine_tab("Application", sample_sm)
  └── 各タブが StateMachineTab を生成
       ├── MatrixTableWidget（遷移マトリクス）
       ├── MermaidWidget（図）
       └── SettingsPanel（状態 / ロール関数）
```

#### 2.4.2 セル編集 → 保存

```
MatrixTableWidget.cellDoubleClicked(row, col)
  ├── sm.get_transitions_for_cell(state, event)
  ├── transition_to_flow_item(trans) -> ActionDraft 構築
  ├── ActionEditorDialog を開く（5タブ：Transitions / Actions / Relations / Overview / Preview）
  │    ├── PaletteWidget（左）
  │    ├── FlowCanvas（中央）
  │    └── CodeWidget（下部）
  ├── D&D で flow_items を編集
  ├── OK -> flow_item_to_transition(item) -> Transition
  └── sm.transitions 更新 -> populate() -> 再描画
```

#### 2.4.3 コード生成

```
MainWindow.save_generated_code_direct()
  ├── config = config_manager.get_config()
  ├── layers = _get_all_layers()        # 全タブ、優先度昇順
  ├── collector = WarningCollector()
  ├── root_logger.addHandler(collector)
  ├── generator = CCodeGenerator(config=config)
  ├── files = generator.generate_all_layers(layers, global_defs, lib)
  ├── if config.save_with_merge:
  │      saved = generator.save_generated_code_with_merge(files, output_dir)
  │   else:
  │      saved = generator.save_generated_code(files, output_dir)
  ├── root_logger.removeHandler(collector)
  └── QMessageBox: 完了通知 + 警告
```

#### 2.4.4 検証フロー（v2.2）

```
ValidationDialog / CodeGenerationDialog
  ├── validator = CodeGenerationValidator()
  ├── result = validator.validate(sm, gd)
  │    ├── 11カテゴリそれぞれについて：
  │    │    └── validator.validate(context) -> List[ValidationIssue]
  │    └── 例外はカテゴリ単位で捕捉、処理継続
  ├── AI診断要求時：
  │    ├── prompt = AIPromptGenerator().generate_diagnosis_prompt(...)
  │    └── changes = AIResponseParser().parse(ai_response)
  └── ChangeApplier(sm, gd).apply_all(changes)
```

#### 2.4.5 新規プロジェクトフロー（v2.3）

```
MainWindow.new_project()
  ├── _maybe_save()                      # 未保存確認（Save/Discard/Cancel）
  │    └── False なら中断
  ├── close_all_tabs()                   # タブ全削除（確認ダイアログなし）
  ├── GlobalDefinitions() 再生成          # 空
  ├── 共有ライブラリをクリア（決定#5）
  │    ├── RoleFunctionLibrary() 再生成
  │    ├── ConditionLibrary() 再生成
  │    └── LiteralLibrary() 再生成
  ├── config_manager.reset()             # CodeGenerationConfig() に戻す
  ├── StateMachine(layer_name="Application") を生成
  ├── add_state_machine_tab("Application", empty_sm)
  ├── setWindowModified(False)
  ├── _update_window_title()
  └── statusBar().showMessage("New project created", 3000)
```

### 2.5 起動シーケンス

```
1. python -m statable_gui.main  (または main_window.py 直接実行)
2. PySide6.QtWidgets.QApplication 生成
3. MainWindow() 生成
   ├── StaTableLogger() 初期化
   ├── Preferences() 読込
   ├── ConfigManager() 生成
   ├── GlobalDefinitions デモデータ
   ├── RoleFunctionLibrary / ConditionLibrary / LiteralLibrary
   ├── create_sample_state_machine() -> role_functions を libcntrl に登録
   ├── QTabWidget 設定
   ├── create_menus() / create_toolbar()
   ├── TraceBallWidget 生成（非表示）
   └── add_state_machine_tab("Application", sample_sm)
4. app.exec() でイベントループへ
```

**v2.3 変更なし**：起動時は引き続きサンプルプロジェクトで開始（決定#1）。空起動が必要な場合は `File > New Project`（Ctrl+N）を使用。

---

## 3. データモデル層（`statable/`）

### 3.1 モジュール一覧

| # | モジュール | 概算 LOC | 責務 |
|---|-----------|---------|------|
| 1 | `__init__.py` | - | 公開 API |
| 2 | `model.py` | 200 | Dataclass と Enum |
| 3 | `state_machine.py` | 100 | StateMachine コンテナ |
| 4 | `global_defs.py` | 260 | グローバル定義 |
| 5 | `xml_io.py` | 700 | XML 保存・読込 |
| 6 | `mermaid_gen.py` | 120 | Mermaid 図生成 |
| 7 | `sample_data.py` | 250 | サンプルデータ |
| 8 | `parser.py` | 3 | スタブ |

### 3.2 `model.py`

#### 3.2.1 Enum 定義

```python
class StateType(Enum):
    NORMAL = "normal"
    CONCURRENT = "concurrent"
    REGION = "region"
    INITIAL = "initial"
    FINAL = "final"
    CHOICE = "choice"
    JUNCTION = "junction"

class EventKind(Enum):
    SIGNAL = "signal"
    CALL = "call"
    TIME = "time"
    CHANGE = "change"

class EventDeliveryType(Enum):
    DIRECT = "direct"
    QUEUE  = "queue"
    DOUBLE = "double"

class EventSourceLayer(Enum):
    DRIVER = "driver"
    MIDDLEWARE = "middleware"
```

#### 3.2.2 `State`

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `name` | str | – | 状態名 |
| `type` | StateType | NORMAL | 状態種別 |
| `parent` | Optional[str] | None | 親状態（階層化用） |
| `entry` | List[str] | [] | エントリ時アクション（v2.2） |
| `exit` | List[str] | [] | エグジット時アクション（v2.2） |
| `do` | str | "" | do アクション |
| `description` | str | "" | 説明 |

**v2.2 変更**：`entry` / `exit` は `List[str]`。旧 `str` / `None` は `__post_init__` で自動正規化。

#### 3.2.3 `Event`

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `name` | str | – | イベント名（空 = 完了遷移） |
| `id` | Optional[int] | None | イベント ID |
| `kind` | EventKind | SIGNAL | 種別 |
| `params` | List[str] | [] | パラメータ名 |
| `priority` | int | 0 | 優先度 |
| `description` | str | "" | 説明 |
| `delivery_type` | EventDeliveryType | DIRECT | 配送方式 |
| `source_layer` | EventSourceLayer | DRIVER | 発生源層 |
| `data_type` | str | "" | 付随データ型 |
| `data_name` | str | "" | 付随データ名 |
| `title` | str | "" | 表示名（未設定時は自動生成） |

#### 3.2.4 `Transition`（v2.2）

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `source` | str | – | 遷移元状態 |
| `event` | str | – | イベント名 |
| `condition` | str | "" | 条件式 |
| `pre_actions` | List[str] | [] | 遷移前アクション |
| `target` | str | "" | 遷移先状態 |
| `has_else` | bool | True | else 節の有無 |
| `else_target` | str | "" | else 時の遷移先 |
| `else_actions` | List[str] | [] | else 時アクション |
| `early_return` | bool | False | v2.2：True = Commit |
| `label` | str | "" | v2.2：セル内ラベル（T1, T2, ...） |
| `action` | str | "" | レガシーフィールド（未使用） |
| `transition_type` | str | "external" | 遷移種別 |
| `title` | str | "" | 表示名 |

**v1.6 変更**：`kw_only=True` で位置引数エラーを防止。
**v2.2 追加**：`early_return`、`label`。

#### 3.2.5 `ActionStep`（v2.2）

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `role_function` | str | "" | ロール関数の qualified_name |
| `trigger` | str | "before_transitions" | 実行タイミング（`before_transitions` / `after_transitions`） |
| `title` | str | "" | 表示名 |

**v2.2.4 変更**：`kw_only=True`。旧 `"always"` はロード時に `"before_transitions"` にマッピング。

#### 3.2.6 `TransitionRelation`（v2.2）

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `kind` | str | "sequential" | 関係種別 |
| `members` | List[str] | [] | 参照する `Transition.label` |
| `shared_condition` | str | "" | 共有条件（`kind == "group"` 時のみ） |
| `note` | str | "" | メモ |
| `children` | List[TransitionRelation] | [] | v2.2 §12-5：ネストされた子関係（再帰） |

**`kind` の値**：

| 値 | 説明 |
|-----|------|
| `sequential` | メンバーを順に評価（デフォルト） |
| `exclusive` | 最大1つ発火、コード生成時に early return を強制 |
| `group` | 論理グループ、`shared_condition` を外側の `if` に巻き上げ |

**v2.2.4 変更**：`kw_only=True`。

#### 3.2.7 `RoleFunction`（statable 版）

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `name` | str | – | 純粋名 |
| `namespace` | str | "" | 名前空間 |
| `description` | str | "" | 説明 |
| `return_type` | str | "void" | 戻り値型 |
| `arg1_type` | str | "" | 引数1の型 |
| `arg1_name` | str | "" | 引数1の名前 |
| `arg2_type` | str | "" | 引数2の型 |
| `arg2_name` | str | "" | 引数2の名前 |
| `title` | str | "" | 表示名 |

**プロパティ**：`qualified_name -> str`：`namespace.name` または `name`。

**クラスメソッド**：`from_legacy_name(legacy_name, layer_names=None) -> RoleFunction`：
- `"Driver_Init"` → `namespace="Driver", name="Init"`
- `layer_names` に含まれない場合、`namespace=""`

**注意**：本クラスは `statable_gui.libcntrl.role_function_library.RoleFunction` とは別クラス（§5.3 参照）。

### 3.3 `state_machine.py`

#### 3.3.1 `StateMachine` クラス

**属性**

| 属性 | 型 | デフォルト | 説明 |
|------|-----|-----------|------|
| `states` | Dict[str, State] | {} | 状態辞書 |
| `events` | Dict[str, Event] | {} | イベント辞書 |
| `transitions` | List[Transition] | [] | 遷移リスト |
| `role_functions` | Dict[str, RoleFunction] | {} | ロール関数辞書 |
| `initial_state` | Optional[str] | None | 初期状態 |
| `layer_priority` | int | 5 | 層優先度（1〜9） |
| `layer_description` | str | "" | 層説明 |
| `layer_name` | str | "" | 層名 |
| `cell_actions` | Dict[Tuple[str,str], List[ActionStep]] | {} | v2.2：セルアクション |
| `cell_relations` | Dict[Tuple[str,str], List[TransitionRelation]] | {} | v2.2：セル関係 |

**メソッド**

| メソッド | 説明 | 例外 |
|---------|------|------|
| `add_state(state)` | 状態追加 | 重複時 `ValueError` |
| `add_event(event)` | イベント追加 | 重複時 `ValueError` |
| `remove_event(name)` | イベントと関連遷移＋セルメタデータ削除 | – |
| `add_transition(trans)` | 遷移追加 | source/target/event 未定義時 `ValueError` |
| `remove_transition(trans)` | 遷移削除 | – |
| `set_initial(name)` | 初期状態設定 | 未定義時 `ValueError` |
| `add_role_function(rf)` | ロール関数追加 | `rf.name` 重複時 `ValueError` |
| `remove_role_function(name)` | ロール関数削除 | – |
| `get_transitions_for_cell(source, event) -> List[Transition]` | セル遷移取得 | – |
| `get_transitions_for_event(event) -> List[Transition]` | イベント全遷移取得 | – |
| `get_actions_for_cell(source, event) -> List[ActionStep]` | v2.2：セルアクション | – |
| `set_actions_for_cell(source, event, actions)` | v2.2：セルアクション設定 | – |
| `get_relations_for_cell(source, event) -> List[TransitionRelation]` | v2.2：セル関係 | – |
| `set_relations_for_cell(source, event, relations)` | v2.2：セル関係設定 | – |
| `get_cell_keys() -> List[Tuple[str,str]]` | v2.2：全セルキー | – |
| `remove_cell_metadata(source, event)` | v2.2：セルメタデータ削除 | – |

**注意**：`add_role_function` は `rf.name`（純粋名）でキー管理。`Driver.Init` と `App.Init` は衝突する。§12 C-11 参照。

### 3.4 `global_defs.py`

#### 3.4.1 Dataclass 一覧

| クラス | 用途 |
|--------|------|
| `StructMemberDef` | 構造体メンバ |
| `CustomTypeDef` | ユーザ定義型 |
| `SystemVariable` | グローバル変数 |
| `EventFlag` | イベントフラグ |
| `InterruptAction` | 割り込みアクション |
| `InterruptHandlerDef` | 割り込みハンドラ |
| `DevicePlaceholderDef` | デバイスプレースホルダ |
| `TimerDerivedDef` | 派生タイマー |
| `TimerBaseDef` | ベースタイマー |
| `EventQueueDef` | イベントキュー |

#### 3.4.2 `GlobalDefinitions`

**属性**
- `variables: List[SystemVariable]`
- `flags: List[EventFlag]`
- `interrupts: List[InterruptHandlerDef]`
- `placeholders: List[DevicePlaceholderDef]`
- `timer_base: TimerBaseDef`
- `extra_timers: List[TimerBaseDef]`
- `event_queues: List[EventQueueDef]`
- `custom_types: List[CustomTypeDef]`

**メソッド**
- `add_timer_variables()`：タイマー変数を `variables` に自動登録（group="Timer"）
- `variable_groups() -> List[str]`：変数グループ一覧
- `flag_groups() -> List[str]`：フラググループ一覧
- `custom_type_names() -> List[str]`：カスタム型名一覧

### 3.5 `xml_io.py`

#### 3.5.1 公開関数

| 関数 | 説明 |
|------|------|
| `project_to_xml(tabs, gd, filepath, role_lib=None, cond_lib=None, lit_lib=None, project_settings=None)` | プロジェクト保存 |
| `project_from_xml(filepath) -> (tabs, gd, role_lib, cond_lib, lit_lib, project_settings)` | プロジェクト読込 |
| `state_machine_to_element(sm) -> ET.Element` | StateMachine → XML |
| `state_machine_from_element(elem) -> StateMachine` | XML → StateMachine |
| `global_defs_to_element(gd) -> ET.Element` | GlobalDefinitions → XML |
| `global_defs_from_element(elem) -> GlobalDefinitions` | XML → GlobalDefinitions |
| `role_function_library_to_element(lib)` | 共有ライブラリ → XML |
| `role_function_library_from_element(elem)` | XML → 共有ライブラリ |
| `condition_library_to_element(lib)` | 同上 |
| `condition_library_from_element(elem)` | 同上 |
| `literal_library_to_element(lib)` | 同上 |
| `literal_library_from_element(elem)` | 同上 |

#### 3.5.2 XML 構造（v2.2 拡張）

```xml
<Project name="MyProject">
  <ProjectSettings>
    <CodeGeneration ... />
  </ProjectSettings>
  <GlobalDefinitions>
    <CustomTypes>...</CustomTypes>
    <SystemVariables>...</SystemVariables>
    <EventFlags>...</EventFlags>
    <Interrupts>
      <Interrupt name="..." ...>
        <Action condition="..." action="..."/>
        <UsedRoleFunction ref="Driver.Init"/>
        <UsedVariable name="counter"/>
      </Interrupt>
    </Interrupts>
    <DevicePlaceholders>...</DevicePlaceholders>
    <TimerBase>...</TimerBase>
    <ExtraTimers>...</ExtraTimers>
    <EventQueues>...</EventQueues>
  </GlobalDefinitions>
  <SharedLibraries>
    <RoleFunctionLibrary>...</RoleFunctionLibrary>
    <ConditionLibrary>...</ConditionLibrary>
    <LiteralLibrary>...</LiteralLibrary>
  </SharedLibraries>
  <Tab name="Application">
    <StateMachine initial="..." layer_priority="5" layer_name="Application">
      <States>
        <State name="Idle" ...>
          <Entry>
            <Action name="Driver.IdleEntry"/>
          </Entry>
          <Exit>
            <Action name="Driver.IdleExit"/>
          </Exit>
        </State>
      </States>
      <Events>...</Events>
      <RoleFunctions>
        <RoleFunction name="Init" namespace="Driver" .../>
      </RoleFunctions>
      <Transitions>
        <Transition source="..." event="..." condition="..." target="..."
                    has_else="true" else_target="..."
                    early_return="true" label="T1">
          <PreAction action="..."/>
          <ElseAction action="..."/>
        </Transition>
      </Transitions>
      <Cells>
        <Cell source="Error" event="RESET">
          <Actions>
            <Action role_function="Driver.PreCheck"
                    trigger="before_transitions" title="Pre-check" />
            <Action role_function="Driver.Cleanup"
                    trigger="after_transitions" title="Cleanup" />
          </Actions>
          <Relations>
            <Relation kind="group" members="T1,T2"
                      shared_condition="running == false" note="...">
              <Children>
                <Relation kind="exclusive" members="T1,T2"
                          shared_condition="" note="..." />
              </Children>
            </Relation>
          </Relations>
        </Cell>
      </Cells>
    </StateMachine>
  </Tab>
</Project>
```

#### 3.5.3 レガシー移行

- `RoleFunction` に `namespace` がなく、`name` に `<layer>_` プレフィックスがある場合、名前空間を自動分離。
- `State.entry` / `exit` が旧 `str` の場合、`List[str]` に変換。
- `_normalize_actions` は旧データの1文字分割（例：`["a","b","c"]`）を自動結合（`["abc"]`）。

#### 3.5.4 既知の制約

- `super_include_dir` は**永続化されない**（ロード時にデフォルト `"common"` にリセット）。§12 C-10 参照。
- `xml_io.py` は `try/except ImportError` フォールバック付きで `statable_gui.libcntrl` を import する。§12 C-22 参照。

### 3.6 `mermaid_gen.py`

| 関数 | 説明 |
|------|------|
| `generate_mermaid(sm) -> str` | StateMachine から `stateDiagram-v2` を生成 |
| `_truncate_condition(condition, max_chars=50) -> str` | 長い条件の切詰め |

**出力形式**：

```
stateDiagram-v2
    direction LR
    [*] --> InitialState
    Source --> Target : Title (Event) [Condition] [Commit]
    Source --> ElseTarget : (Event) else [Commit]
    note right of State : internal: Title (Event)
```

**v2.2 追加**：
- `early_return=True` でラベルに ` [Commit]` を追加
- `else_target` は別エッジとして出力（`stateDiagram-v2` は破線非対応）
- `entry` / `exit` は**出力しない**（メタデータ扱い）

### 3.7 `sample_data.py`

| 関数 | 説明 |
|------|------|
| `create_sample_state_machine() -> StateMachine` | 4状態、5イベント、6遷移、9ロール関数、4セルアクション、2セル関係 |
| `create_sample_global_defs() -> GlobalDefinitions` | 4変数、2フラグ、2型、1割り込み、2タイマーグループ、1キュー |

**注意**：`create_sample_state_machine` のロール関数は**レガシー形式**（`Sensor_Init`、`Error_Log`）。名前空間未使用。

---

## 4. GUI層（`statable_gui/`）

### 4.1 モジュール一覧

| # | モジュール | 主要クラス | 用途 |
|---|-----------|-----------|------|
| 1 | `main_window.py` | `MainWindow` | メインウィンドウ |
| 2 | `widgets.py` | `StateMachineTab`, `SettingsPanel`, `MermaidWidget` | タブ |
| 3 | `matrix_table.py` | `MatrixTableWidget` | 遷移マトリクス |
| 4 | `code_generation_dialog.py` | `CodeGenerationDialog`, `WarningCollector` | 生成 UI |
| 5 | `code_generation_settings_dialog.py` | `CodeGenerationSettingsDialog` | 設定 UI |
| 6 | `condition_builder_dialog.py` | `ConditionBuilderDialog`, `LiteralizationDialog` | 条件ビルダー |
| 7 | `config.py` | – | 定数、リソースパス |
| 8 | `logger.py` | `StaTableLogger` | ロギング |
| 9 | `preferences.py` | `Preferences` | アプリ設定 |
| 10 | `traceball.py` | `TraceBallWidget` | ログ表示 |
| 11 | `global_defs_dialog.py` | `GlobalDefinitionsDialog` | グローバル定義 |
| 12 | `event_definition_dialog.py` | `EventDefinitionDialog` | イベント定義 |
| 13 | `event_delivery_settings_dialog.py` | `EventDeliverySettingsDialog` | 配送設定 |
| 14 | `interrupt_handler_edit_dialog.py` | `InterruptHandlerEditDialog` | 割り込み編集 |
| 15 | `layer_settings_dialog.py` | `LayerSettingsDialog` | 層設定 |
| 16 | `validation_dialog.py` | `ValidationDialog` | 検証（GUI） |
| 17 | `common_widgets.py` | `TypeManagerDialog` | 型管理 |
| 18 | `action_edit_dialog.py` | `ActionEditDialog` | レガシーアクション編集 |
| 19 | `role_function_dialog.py` | `RoleFunctionDialog` | レガシーロール関数編集 |
| 20 | `dialogs.py` | `TransitionListDialog`, `TransitionTable` | 遷移リスト |
| 21 | `event_queue_dialog.py` | `EventQueueDefsDialog` | イベントキュー編集 |
| 22 | `symbol_picker.py` | `SymbolPickerWidget` | シンボルピッカー |
| 23 | `condition_edit_dialog.py` | `ConditionEditDialog` | 条件編集 |

### 4.2 `MainWindow`

*（v2.0 から変更なし。v2.2 で `codegen/validate/` 統合、v2.3 で新規プロジェクト機能が追加。）*

#### 4.2.1 v2.3 追加メソッド

| メソッド | 用途 |
|---------|------|
| `new_project()` | 空の Application 層でプロジェクトを初期化 |
| `_maybe_save() -> bool` | 未保存確認（Save/Discard/Cancel）。`new_project` / `open_project` / `closeEvent` から呼ぶ |
| `closeEvent(event)` | 終了時の未保存確認 |
| `_update_window_title()` | `Untitled[*] - StaTable` 形式でタイトル更新 |
| `_on_tab_data_modified()` | `StateMachineTab.dataModified` を受けるスロット |

#### 4.2.2 v2.3 変更メソッド

| メソッド | 変更内容 |
|---------|---------|
| `save_project()` | 戻り値を `None` → `bool` に変更（成功時 `True`、キャンセル/失敗時 `False`）。成功パスで `setWindowModified(False)` + `_update_window_title()` |
| `open_project()` | 冒頭に `_maybe_save()` を追加。成功パスで `setWindowModified(False)` + `_update_window_title()` |
| `add_state_machine_tab()` | `tab.dataModified.connect(self._on_tab_data_modified)` を追加 |
| `add_new_tab` / `rename_tab_at` / `close_tab` | 成功時に `setWindowModified(True)` + `_update_window_title()` を追加 |
| `create_menus()` | `File > New Project...`（Ctrl+N）を `Open Project...` の直前に追加 |

#### 4.2.3 保持 / リセット対象（v2.3 決定）

| 対象 | New 時 |
|------|--------|
| Preferences | **保持** |
| shared libraries (`libcntrl`) | **クリア**（`RoleFunctionLibrary()` / `ConditionLibrary()` / `LiteralLibrary()` を再生成）★変更 |
| TraceBall ログ | **保持**（決定#8） |
| GlobalDefinitions | **リセット**（`GlobalDefinitions()` 再生成） |
| ConfigManager | **リセット**（`reset()` → `CodeGenerationConfig()` に戻す） |
| タブ | 空の `Application` タブ1個 |
| `windowModified` | `False` に |

**決定#5 変更の背景**：`open_project` がライブラリを置換する挙動（line 691-697）との非対称を解消するため、`new_project` でもクリアする方針に変更。これにより、`New` / `Open` の両方が「前プロジェクトのライブラリを引き継がない」で対称となる。

#### 4.2.4 `_maybe_save()` の仕様

| 入力 | 出力 | 動作 |
|------|------|------|
| `windowModified == False` | `True` | 確認スキップ |
| `windowModified == True` + Save 選択 | `save_project()` の戻り値 | 保存成功なら `True`、失敗なら `False` |
| `windowModified == True` + Discard 選択 | `True` | 変更破棄 |
| `windowModified == True` + Cancel 選択 | `False` | 中止 |

#### 4.2.5 v2.3 ショートカット方針

既存の `setShortcut` は文字列ベース（`"Ctrl+Shift+V"` 等）で統一。`QKeySequence` は未使用。これに合わせて `setShortcut("Ctrl+N")` を使用し、`QKeySequence` の import は追加しない。

### 4.3 `StateMachineTab`

*（v2.0 から変更なし。v2.3 で `dataModified` シグナル追加。）*

#### 4.3.1 構造

| 属性 | 型 | 説明 |
|------|-----|------|
| `sm` | `StateMachine` | 対象ステートマシン |
| `global_defs` | `GlobalDefinitions` | 共有グローバル定義 |
| `role_function_library` | `RoleFunctionLibrary` | 共有ロール関数 |
| `condition_library` | `ConditionLibrary` | 共有条件 |
| `literal_library` | `LiteralLibrary` | 共有リテラル |
| `table` | `MatrixTableWidget` | 遷移マトリクス |
| `mermaid` | `MermaidWidget` | 図プレビュー |
| `settings` | `SettingsPanel` | 状態/ロール関数パネル |

#### 4.3.2 v2.3 追加

- `dataModified = Signal()`：子ウィジェットの編集を MainWindow に伝播
- `__init__` 末尾（line 955-956 の直後）に以下の2行を追加：

```python
self.table.transition_changed.connect(self.dataModified)
self.settings.settings_changed.connect(self.dataModified)
```

`Signal.connect(Signal)` による signal-to-signal 接続で、子の変更が直接 MainWindow に伝播する。

### 4.4 `MermaidWidget`

*（v2.0 から変更なし。）*

### 4.5 `MatrixTableWidget`

**v2.2 追加**：
- `_truncate_text`、`_build_transition_tooltip`、`_event_header_label`
- ツールチップに `early_return`（Commit / Tentative マーカー）を含む
- セルラベルに複数ターゲット、Commit/Tentative マーカーを表示
- イベントヘッダに `[Q]` / `[D]` プレフィックス（`QUEUE` / `DOUBLE` 配送）

**シグナル**：
- `transition_changed = Signal()`：遷移編集確定時に発火（`open_transition_dialog` と `keyPressEvent` の2箇所）

### 4.6 `SettingsPanel`（v2.2）

| タブ名 | 列 |
|--------|-----|
| `State list` | Name / Description / entry function / exit function / do function / Type |
| `Role function` | Title / Function name / **Namespace** / Description / Return type / Arg 1 type / Arg 1 name / Arg 2 type / Arg 2 name |

`State.entry` と `State.exit` は `List[str]`。UI は `"; "` で結合・分割。

**シグナル**：
- `settings_changed = Signal()`：状態/ロール関数テーブルの編集確定時に発火（`_emit_settings_changed`、`on_state_table_cell_double_clicked`、`delete_state`、`add_role_function`、`delete_role_function` から emit）

### 4.7 `CodeGenerationDialog`

**UI**：
- 設定情報（出力先、生成方式、OS種別、マージ）
- アクションボタン（生成 / 保存 / 閉じる）
- プレビュー（タブコンボ + 読取専用テキスト）
- プログレスバー

**`WarningCollector`**：`WARNING` 以上のレコードを収集する `logging.Handler` サブクラス。

### 4.8 `CodeGenerationSettingsDialog`

**4タブ**：
- Basic settings（プロジェクト名、生成方式**固定**、OS種別、命名、コメント）
- Log settings（debug/info/error、最大 pending events）
- External include（ファイルリスト、挿入先チェックボックス）
- Output settings（出力先、フォルダ構成、スーパーinclude、マージ）

**注意**：`generation_style` と `table_type` は **強制的に** `table_driven` / `array` に設定（v2.2 C-01/C-02/C-03/C-04）。

---

## 5. 共有ライブラリ（`statable_gui/libcntrl/`）

### 5.1 モジュール一覧

| モジュール | 主要クラス |
|-----------|-----------|
| `role_function_library.py` | `RoleFunctionLibrary`, `RoleFunction` |
| `condition_library.py` | `ConditionLibrary`, `ConditionTemplate` |
| `literal_library.py` | `LiteralLibrary`, `LiteralDefinition` |
| `role_function_edit_dialog.py` | `RoleFunctionEditDialog` |
| `literal_management_dialog.py` | `LiteralManagementDialog`, `LiteralEditDialog` |

### 5.2 `RoleFunctionLibrary`

| メソッド | 説明 |
|---------|------|
| `_key(rf) -> str` | `rf.qualified_name` |
| `add(rf)` | `qualified_name` 重複時 `ValueError` |
| `remove(name)` | qualified / bare 両対応 |
| `get(name) -> Optional[RoleFunction]` | qualified / bare 両対応 |
| `list_all() -> List[RoleFunction]` | 全エントリ |
| `to_dict() -> dict` | シリアライズ |
| `from_dict(data) -> RoleFunctionLibrary` | デシリアライズ（重複は無視） |

### 5.3 `RoleFunction`（libcntrl 版）

| フィールド | 型 | デフォルト |
|-----------|-----|-----------|
| `name` | str | – |
| `namespace` | str | "" |
| `description` | str | "" |
| `title` | str | "" |
| `used_global_vars` | List[str] | [] |
| `used_events` | List[str] | [] |
| `used_literals` | List[str] | [] |

**プロパティ**：`qualified_name -> str`

**メソッド**：`to_dict`、`from_dict`

**注意**：`statable.model.RoleFunction` とは**別クラス**。主な違い：

| 観点 | `statable/model.py` | `libcntrl/` |
|------|---------------------|-------------|
| 用途 | C シグネチャ定義 | GUI 使用シンボル追跡 |
| 主要フィールド | `return_type`、`arg1/2_type/name` | `used_global_vars/events/literals` |
| キーメソッド | `name`（純粋名） | `qualified_name` |
| kw_only | あり | なし |

### 5.4 `ConditionLibrary`

| メソッド | 説明 |
|---------|------|
| `add(ct: ConditionTemplate)` | `name` 重複時 `ValueError` |
| `remove(name)` | エントリ削除 |
| `get(name) -> Optional[ConditionTemplate]` | エントリ取得 |
| `list_all() -> List[ConditionTemplate]` | 全エントリ |
| `to_dict` / `from_dict` | シリアライズ |

### 5.5 `LiteralLibrary`

| メソッド | 説明 |
|---------|------|
| `add(lit: LiteralDefinition)` | `name` 重複時 `ValueError` |
| `remove(name)` | エントリ削除 |
| `get(name) -> Optional[LiteralDefinition]` | エントリ取得 |
| `list_all() -> List[LiteralDefinition]` | 全エントリ |
| `to_dict` / `from_dict` | シリアライズ |

---

## 6. 遷移エディタ（`statable_gui/transition_editor_direct/`）

### 6.1 モジュール一覧

| モジュール | 主要クラス | 用途 |
|-----------|-----------|------|
| `draft.py` | `ActionDraft`, `FlowItem`, `SystemGlobal`, `TransitionParams` | モデル（v2.2：cell_actions/cell_relations） |
| `dialog.py` | `ActionEditorDialog` | エントリポイント（5タブ） |
| `palette_widget.py` | `PaletteWidget`, `PaletteListWidget` | パレット |
| `canvas_widget.py` | `FlowCanvas`, `FlowNodeItem` | キャンバス |
| `code_widget.py` | `CodeWidget` | コードプレビュー |
| `system_global_dialog.py` | `SystemGlobalDialog` | グローバル編集 |
| `transitions_tab.py` | `TransitionsTab` | v2.2 |
| `actions_tab.py` | `ActionsTab`, `_ActionGroup` | v2.2（Pre / Post） |
| `relations_tab.py` | `RelationsTab` | v2.2 |
| `overview_tab.py` | `OverviewTab` | v2.2 |
| `coverage_analyzer.py` | `CoverageAnalyzer` | v2.2（到達性・カバレッジ） |
| `relations_edit_dialog.py` | `RelationsEditDialog` | v2.2 |
| `transition_actions_dialog.py` | `TransitionActionsDialog` | v2.2 |
| `flow_widget.py` | `FlowWidget`, `FlowListWidget` | **レガシー** |
| `edit_dialogs.py` | `FunctionEditDialog`, `TransitionEditDialog` | **レガシー** |

### 6.2 `ActionEditorDialog`（v2.2：5タブ）

| タブ | 内容 |
|------|------|
| Transitions | `TransitionsTab` |
| Pre / Post Actions | `ActionsTab` |
| Relations | `RelationsTab` |
| Overview | `OverviewTab` |
| Preview | `CodeWidget` |

### 6.3 `CoverageAnalyzer`（v2.2）

| メソッド | 説明 |
|---------|------|
| `analyze_cell(sm, source, event) -> CellReport` | セル内解析 |
| `analyze_state_graph(sm) -> StateGraphReport` | 状態グラフ解析 |

**`CellReport`**：`transitions_count`、`unreachable_labels`、`duplicate_targets`、`overlap_pairs`

**`StateGraphReport`**：`unreachable_states`、`terminal_states`、`self_loops`

---

## 7. コード生成（`codegen/`）

### 7.1 モジュール一覧（16 + validate サブシステム）

| # | モジュール | 用途 | 現行バージョン |
|---|-----------|------|--------------|
| 1 | `c_code_generator.py` | Step-table driven オーケストレーション | v2.2.9 |
| 2 | `role_function_generator.py` | ロール関数の宣言・実装 | v3.3 |
| 3 | `transition_generator.py` | Cell 関数・テーブル・GetNextEvent | v2.6 |
| 4 | `code_templates.py` | テンプレート辞書（OSAL + コードパターン） | **v2.2.5** |
| 5 | `struct_generator.py` | システム構造体 | v2.2.1 |
| 6 | `enum_generator.py` | State / Event / Flag enum | v1.5 |
| 7 | `variable_generator.py` | 変数マクロ + `SystemContext_Init` | v2.0 |
| 8 | `event_queue_generator.py` | イベントキュー実装 | – |
| 9 | `interrupt_generator.py` | ISR 生成 | H3 |
| 10 | `timer_generator.py` | タイマー構造体 / `Timer_Init` / `Timer_Update` | v2.2 |
| 11 | `osal_generator.py` | OSAL ヘッダ / ソース | v2.2 |
| 12 | `type_mapper.py` | C 型マッピング | – |
| 13 | `naming_convention.py` | 命名規則 | v2.2.5 |
| 14 | `code_merger.py` | マーカー方式マージ | v2.0 |
| 15 | `config.py` | `CodeGenerationConfig` / `ConfigManager` | – |
| 16 | `sample_data.py` | 生成用デモデータ | – |
| 17 | `validate/` | 検証サブシステム（§7.5 参照） | v2.2 |

### 7.2 出力ファイル（14）

| # | ファイル | 種別 | 用途 |
|---|---------|------|------|
| 1 | `statable_types_common.h` | Header | 共通構造体、enum（`FLAG_t` 含む）、ログマクロ、`SystemContext_Init` / `Timer_*` プロトタイプ |
| 2 | `statable_types.h` | Header | 層別 enum + `TransitionContext_<Layer>_t` |
| 3 | `statable_transitions.h` | Header | `StateMachine_Process_*` + `StateMachine_GetNextEvent_*` プロトタイプ |
| 4 | `statable_transitions.c` | Source | Cell 関数、遷移テーブル、`Process`、`GetNextEvent` |
| 5 | `statable_role_functions.h` | Header | `RoleFunc_<NS>_<Name>` 宣言（自層のみ） |
| 6 | `statable_role_functions.c` | Source | ロール関数実装 + `call_sites` + `Transition_GetId` |
| 7 | `statable_init.c` | Source | `SystemContext_Init` |
| 8 | `statable_event_queue.c` | Source | イベントキュー実装 |
| 9 | `statable_interrupt.c` | Source | ISR |
| 10 | `statable_timer.c` | Source | タイマー構造体 + `Timer_Init` / `Timer_Update` |
| 11 | `osal.h` | Header | OS 抽象化 |
| 12 | `osal.c` | Source | OS 抽象化（NonRTOS / FreeRTOS includes / ThreadX includes） |
| 13 | `statable_all.h` | Header | スーパー include |
| 14 | `{project}_run.c` | Source | スーパーループ |

### 7.3 フォルダ構成

| 構成 | レイアウト |
|------|-----------|
| `flat` | 全ファイルを1ディレクトリに配置 |
| `by_type` | `include/` / `src/` / `common/` |
| `by_layer` | 層別サブディレクトリ + ルート直下に common |

### 7.4 MISRA C:2012 対応

#### 7.4.1 概要

StaTable の生成 C コードは、**`cppcheck` + 公式 MISRA addon** で **MISRA C:2012** に対して検証される。チェックは**情報提供のみ** — ビルドを失敗させない（`misra_report/summary.md` 参照）。ベースライン履歴と抑制は `misra/baseline.md` および `misra/suppressions.txt` に記録。

#### 7.4.2 ベースライン履歴

| バージョン | 日付 | MISRA ヒット | 非 MISRA | 主な修正 |
|-----------|------|------------:|---------:|---------|
| v2.2.5 | 2026-09-19 | 183 | 290 | 初期測定 |
| v2.2.6 | 2026-09-20 | 38 | 9 | 層間 `role_functions` include、未使用ローカル変数への `(void)` |
| v2.2.7 | 2026-09-20 | 29 | 9 | `LOG_*` マクロ定義、`GetNextEvent_*` プロトタイプ |
| v2.2.8 | 2026-09-20 | 14 | 9 | 12.1 括弧、10.4 OSAL の符号なしリテラル |
| v2.2.9 | 2026-09-20 | 14 | 9 | `statable_types_common.h` を `transitions_c` に追加 |
| v2.6 | 2026-09-20 | 11 | 9 | 生成 `GetNextEvent_*` 本体から `LOG_ERROR` を削除 |
| v2.6.1 | 2026-09-20 | **10** | 9 | 10.4 タイマー乗数 `10U` |

#### 7.4.3 現状（v2.6.1）

**MISRA ヒット：10（全て設計上抑制）**

| ルール | 件数 | 抑制理由 |
|-------|-----:|---------|
| `8.4` | 3 | モジュール構造：層別 extern 可視性 |
| `11.5` | 4 | ベアメタル OSAL のポインタキャスト（`void *` → `uint8_t *`） |
| `18.4` | 2 | ベアメタル OSAL のポインタ演算 |
| `15.7` | 1 | `_handled` パターン：独立 `if` ガード |

**非 MISRA 警告：9（情報提供のみ）**

| ID | 件数 | 状態 |
|----|-----:|------|
| `knownConditionTrueFalse` | 3 | 許容（関係ネスト） |
| `redundantInitialization` | 2 | 化粧的 |
| `variableScope` | 2 | 化粧的 |
| `unreadVariable` | 2 | 許容（ユーザコードマーカー） |

#### 7.4.4 抑制理由

全文は `misra/suppressions.txt` 参照。現行ファイルは **11ルール**（全て設計上抑制）を列挙。

| ルール | 理由 |
|-------|------|
| `2.3` | 未使用型宣言（予約型） |
| `2.4` | 未使用タグ（構造体タグ） |
| `2.5` | 未使用マクロ（将来用に予約） |
| `5.9` | 内部リンケージ識別子の重複（層別ファイル） |
| `8.4` | 層別 extern 可視性はモジュール再構成が必要。層間協調を維持する設計判断 |
| `8.7` | 外部リンケージ関数の参照（層間協調） |
| `8.9` | 単一翻訳単位でのオブジェクト定義（設計判断） |
| `11.5` | ベアメタル OSAL は `memcpy` 回避のため `void *` + `uint8_t *` キャストを使用（リアルタイム性 / コードサイズ） |
| `15.5` | 単一 exit point を使用しない（可読性優先） |
| `15.7` | `_handled` パターン：各 `if` は独立ガード。`else if` は意味論を変える |
| `18.4` | `11.5` と同様：OSAL キューのポインタ演算 |

**注意**：本セクションで文書化されているのは11ルール中4件（8.4、11.5、18.4、15.7）のみ。残り7件（2.3、2.4、2.5、5.9、8.7、8.9、15.5）は完全性のため本セクションに記録。§12 C-23 参照。

#### 7.4.5 条件側ロール関数呼び出し

`Transition.condition` および `Relation.shared_condition` 内のロール関数呼び出しは、`int` 戻り値を保持するため **`(void)` キャストなし**で出力される：

```c
if (RoleFunc_Driver_PreCheck(transition, ctx) == 0) {   /* 戻り値保持 */
    next_state = STATE_Driver_Ready;
}
```

**アクションコンテキスト**（`pre_actions`、`else_actions`、セルアクション、状態 entry / exit）のロール関数呼び出しは、MISRA 17.7 準拠のため `(void)` キャスト付きで出力される：

```c
(void)RoleFunc_Driver_LogError(transition, ctx);
```

この区別は以下で実装：
- `_role_func_call_expr()` — 条件式用（`(void)` なし）
- `_role_func_call_action()` — アクションコンテキスト用（`(void)` キャスト）
- `Transition.condition` / `Relation.shared_condition` の生テキスト挿入

### 7.5 検証サブシステム（`codegen/validate/`）

#### 7.5.1 モジュール一覧

| # | モジュール | 主要クラス | 用途 |
|---|-----------|-----------|------|
| 1 | `validator.py` | `CodeGenerationValidator` | エントリポイント（11カテゴリ） |
| 2 | `models.py` | `ValidationSeverity`, `ValidationIssue`, `ValidationResult`, `ValidationContext` | データモデル |
| 3 | `change_actions.py` | `ChangeActionType`, `ChangeRequest` | AI 変更アクション（17種） |
| 4 | `change_applier.py` | `ChangeApplier` | 変更適用（17ハンドラ） |
| 5 | `prompt_generator.py` | `AIPromptGenerator` | AI プロンプト生成 |
| 6 | `response_parser.py` | `AIResponseParser` | AI 応答解析 |
| 7 | `clipboard_manager.py` | `ClipboardManager` | クリップボード補助 |
| 8 | `validation_dialog.py` | `ValidationDialog` | GUI（5タブ） |
| 9 | `data/validation_rules.py` | – | ルール定義（35ルール） |
| 10 | `data/prompt_templates.py` | – | プロンプトテンプレート |
| 11 | `data/action_definitions.py` | – | アクション定義 |
| 12 | `data/keywords.py` | – | キーワード |
| 13 | `items/base_validator.py` | `BaseValidator` | 基底クラス |
| 14 | `items/state_validator.py` | `StateValidator` | 4ルール |
| 15 | `items/event_validator.py` | `EventValidator` | 2ルール |
| 16 | `items/transition_validator.py` | `TransitionValidator` | 5ルール |
| 17 | `items/role_function_validator.py` | `RoleFunctionValidator` | 3ルール |
| 18 | `items/variable_validator.py` | `VariableValidator` | 3ルール |
| 19 | `items/flag_validator.py` | `FlagValidator` | 2ルール |
| 20 | `items/queue_validator.py` | `QueueValidator` | 2ルール |
| 21 | `items/interrupt_validator.py` | `InterruptValidator` | 2ルール |
| 22 | `items/timer_validator.py` | `TimerValidator` | 2ルール |
| 23 | `items/custom_type_validator.py` | `CustomTypeValidator` | 2ルール |
| 24 | `items/cell_validator.py` | `CellValidator` | 8ルール（v2.2） |

#### 7.5.2 検証ルール（全35）

| カテゴリ | Error | Warning | Info |
|---------|------:|--------:|-----:|
| state | 1 | 3 | 0 |
| event | 0 | 2 | 0 |
| transition | 3 | 1 | 1 |
| role_function | 2 | 1 | 0 |
| variable | 2 | 1 | 0 |
| flag | 1 | 1 | 0 |
| queue | 1 | 1 | 0 |
| interrupt | 1 | 1 | 0 |
| timer | 2 | 0 | 0 |
| custom_type | 1 | 1 | 0 |
| cell | 2 | 4 | 2 |
| **合計** | **16** | **16** | **3** |

#### 7.5.3 `ChangeActionType`（17種）

**レガシー（10）**：`SET_INITIAL`、`ADD_TRANSITION`、`ADD_STATE`、`ADD_EVENT`、`REMOVE_TRANSITION`、`UPDATE_TRANSITION`、`ADD_ROLE_FUNCTION`、`REMOVE_ROLE_FUNCTION`、`ADD_VARIABLE`、`ADD_FLAG`

**v2.2 セル単位（7）**：`ADD_CELL`、`REMOVE_CELL`、`ADD_ACTION_STEP`、`REMOVE_ACTION_STEP`、`ADD_TRANSITION_RELATION`、`REMOVE_TRANSITION_RELATION`、`SET_EARLY_RETURN`

---

## 8. CI/CD

### 8.1 ワークフロー

`.github/workflows/check.yml`（リポジトリルート）

### 8.2 ジョブ構成

| ジョブ | 依存先 | 用途 |
|-------|--------|------|
| `no-japanese` | – | 非 ASCII 検出 |
| `syntax` | – | compileall |
| `tests` | syntax | 13テストスイート（v2.3：+1） |
| `generated-code` | syntax | C コード生成検証 |

### 8.3 環境変数

| 変数 | 値 | 用途 |
|------|-----|------|
| `QT_QPA_PLATFORM` | `offscreen` | GUI ヘッドレス |
| `STATABLE_DISABLE_MERMAID` | `1` | Mermaid 抑制 |
| `PYTHONIOENCODING` | `utf-8` | エンコーディング問題防止 |

### 8.4 Qt システムライブラリ

```
libegl1, libgl1, libglib2.0-0, libdbus-1-3,
libxkbcommon0, libxkbcommon-x11-0,
libxcb-icccm4, libxcb-image0, libxcb-keysyms1,
libxcb-randr0, libxcb-render-util0, libxcb-shape0,
libxcb-xinerama0, libxcb-xfixes0, libxcb-cursor0,
libfontconfig1, libfreetype6
```

### 8.5 推奨（未実装）

- 全生成 `.c` ファイルの `gcc -fsyntax-only`
- 組み込み向け `arm-none-eabi-gcc -fsyntax-only`
- CI での MISRA 検証（現在は手動）

---

## 9. 開発環境

### 9.1 要件

| 項目 | バージョン |
|------|-----------|
| Python | 3.12 |
| PySide6 | 最新 |
| Git | 最新 |
| OS | Windows 10/11 または Ubuntu 22.04+ |
| cppcheck | 2.x（MISRA 検証用） |

### 9.2 セットアップ

```bash
git clone https://github.com/akashi-hideki/StaTable.git
cd StaTable/code
pip install PySide6 pycparser
```

### 9.3 実行

```bash
cd code
python -m statable_gui.main
```

### 9.4 テスト

```bash
cd code
python tests/test_v2_2_p1.py
# ... 他11スイート
python tests/test_v2_3_p1.py     # v2.3 追加
```

### 9.5 MISRA 検証

```bash
cd code
python tools/run_misra_check.py --root output --out misra_report
python tools/analyze_misra_impact.py \
  --xml misra_report/cppcheck_raw.xml \
  --out misra_report/impact.md \
  --csv misra_report/impact.csv
```

---

## 10. コーディング規約

### 10.1 Python

| 項目 | 規約 |
|------|------|
| インデント | 4スペース |
| 文字列 | ダブルクォート推奨 |
| 型ヒント | 公開 API で必須 |
| Docstring | モジュール先頭 + 公開クラス/メソッド |
| 命名 | `snake_case`（関数/変数）、`PascalCase`（クラス） |

### 10.2 コメント言語

- **コード内コメント・docstring**：英語推奨（`no-japanese` CI ジョブで検出）
- **仕様書**：日本語版と英語版を分離

### 10.3 C コード

- C99 準拠
- `static` 関数を多用
- 生成ファイル先頭に `@file` / `@brief` / `@note` / `@date`
- MISRA C:2012 対応（§7.4 参照）

---

## 11. テスト方針

### 11.1 テストスイート（13）

| ファイル | 対象 | 期待結果 |
|---------|------|---------|
| `test_v2_2_p1.py` | データモデル（v2.2 追加） | 94 PASS / 0 FAIL |
| `test_v2_2_p2.py` | コード生成（v2.2 / MISRA 対応期待値） | 67 PASS / 0 FAIL |
| `test_v2_2_p3.py` | GUI ヘルパー | 37 PASS / 0 FAIL |
| `test_v2_2_p4a.py` | コード生成（基本） | 82 PASS / 0 FAIL |
| `test_v2_2_p4b.py` | コード生成（詳細） | 30 PASS / 0 FAIL |
| `test_v2_2_p12_2.py` | Stage 2 機能 | 31 PASS / 0 FAIL |
| `test_v2_2_p12_5.py` | Stage 5 機能（グループネスト） | 37 PASS / 0 FAIL |
| `test_v2_2_p12_6.py` | Stage 6 機能（AI アクション拡張） | 55 PASS / 0 FAIL |
| `test_v2_2_p12_7.py` | Stage 7 機能 | 9 PASS / 0 FAIL |
| `test_v2_2_p12_8.py` | Stage 8 機能（生成 C 構造体） | 25 PASS / 0 FAIL |
| `test_v2_2_p12_9.py` | Stage 9 機能（XML ラウンドトリップ） | 41 PASS / 0 FAIL |
| `test_v2_2_p12_10.py` | Stage 10 機能（構造） | 29 PASS / 2 SKIP / 0 FAIL |
| `test_v2_3_p1.py` | 新規プロジェクト（v2.3） | 14 PASS / 0 FAIL |

**合計**：**551 PASS / 0 FAIL / 2 SKIP**

### 11.2 `test_v2_2_p2.py` 更新履歴

- **v2.2.6**：MISRA 対応コード生成の期待値を更新：
  - 単一 Commit は `_handled` を宣言しない
  - 混在 `!`/`&&` 条件に括弧を追加（MISRA 12.1）
  - `_role_func_call_action()` がアクションコンテキストで `(void)` を出力
  - 2個以上の Commit 遷移 → `_handled` フラグを出力

### 11.3 `test_v2_3_p1.py` 内容

新規プロジェクト機能（v2.3）の 14 テスト：

| テスト | 検証内容 |
|--------|---------|
| `test_new_project_creates_one_application_tab` | タブが1個（Application） |
| `test_new_project_resets_state_machine` | 状態/イベント/遷移/ロール関数が空 |
| `test_new_project_resets_global_defs` | GlobalDefinitions が空 |
| `test_new_project_clears_shared_libraries` | 共有ライブラリがクリアされる（決定#5 変更） |
| `test_new_project_resets_config_manager` | ConfigManager が `reset()` される |
| `test_new_project_keeps_preferences` | Preferences 保持（決定#7） |
| `test_new_project_clears_window_modified` | `windowModified` が `False` |
| `test_new_project_cancelled_by_user` | Cancel で中断 |
| `test_new_project_discard_proceeds` | Discard で続行 |
| `test_new_project_save_calls_save_project` | Save で `save_project()` 呼出 |
| `test_maybe_save_no_changes_returns_true` | 変更なしで `True` |
| `test_save_project_returns_bool` | `save_project` が bool を返す |
| `test_tab_data_modified_signal_exists` | `dataModified` シグナル存在 |
| `test_tab_data_modified_sets_window_modified` | emit で `windowModified == True` |

### 11.4 実行環境

- ローカル：Windows でも動作
- CI：`ubuntu-latest` + `QT_QPA_PLATFORM=offscreen`

### 11.5 検証ツール

- `tools/find_all_japanese.py`：非 ASCII 検出
- `tools/verify_generated_code.py`：生成 C コードの構文・構造検証
- `tools/run_misra_check.py`：cppcheck + addon による MISRA C:2012 チェック
- `tools/analyze_misra_impact.py`：MISRA 違反を責任 codegen ソースにマッピング
- `tools/investigate_new_project.py`（v2.3）：新規プロジェクト機能の事前調査
- `tools/investigate_new_project_step2.py`（v2.3）：第2段階調査
- `tools/verify_new_project_remaining.py`（v2.3）：R-1/R-2/R-3 検証
- `tools/verify_new_project_final.py`（v2.3）：実装前最終確認
- `tools/verify_new_project_code_facts.py`（v2.3）：B-1〜B-6 コード事実確認

### 11.6 テストギャップ

| ギャップ | 影響 |
|---------|------|
| CI での `gcc -fsyntax-only` なし | コンパイルエラー未検出 |
| `super_include_dir` 永続化テストなし | リグレッション未検出 |
| 名前空間衝突テストなし | データロス未検出 |
| 空イベント `transition_to_flow_item` テストなし | バグ残存 |
| レガシー `flow_widget.py` / `edit_dialogs.py` 未テスト | デッドコードのドリフト |
| `codegen/validate/` サブシステムのテストなし | 検証バグ未検出 |
| v2.3：ダイアログ編集が `windowModified` に反映されない | C-36〜C-39 参照 |

---

## 12. 既知の制約

| # | 項目 | 状態 | 影響 |
|---|------|------|------|
| C-01 | `generation_style` / `table_type` の GUI 切替 | **選択不可**（強制） | 設定 UI のラベル固定 |
| C-02 | `switch_case` 生成 | **未実装** → `table_driven` | 警告ログ |
| C-03 | `switch` テーブル | **未実装** → `array` | 警告ログ |
| C-04 | `dictionary` テーブル | **未実装** → `array` | 警告ログ |
| C-05 | `external_includes_in_role` | **未実装** | 設定フラグ無視 |
| C-06 | `external_includes_in_transitions` | **未実装** | 同上 |
| C-07 | `external_includes_in_common` | **未実装** | 同上 |
| C-08 | FreeRTOS OSAL | **include のみ** | 関数本体なし |
| C-09 | ThreadX OSAL | **include のみ** | 同上 |
| C-10 | プロジェクト XML `super_include_dir` | **永続化されない** | `"common"` にリセット |
| C-11 | ロール関数の一意性不一致 | **設計上の非対称** | 名前空間間の衝突 |
| C-12 | `transition_to_flow_item` 空イベント | **バグ** | `"NewEvent"` に変換 |
| C-13 | `palette_widget._add_function` import | **フォールバックなし** | `ImportError` の可能性 |
| C-14 | `project_dir_name` | **予約、未使用** | 効果なし |
| C-15 | `flow_widget.py` / `edit_dialogs.py` | **レガシー** | デッドコード、未参照 |
| C-16 | 外部 include パス | **ファイル名のみ** | ディレクトリ部が消失 |
| C-17 | `TransitionContext_t` vs `TransitionContext_<Layer>_t` | **両方出力** | 2型、同一レイアウト |
| C-18 | 多層 `by_type` | **1ファイルにマージ** | 層分離不可視 |
| C-19 | 出力先警告の `\n` 欠落 | **化粧的バグ** | "settingsPlease specify" |
| C-20 | `flow_item_to_transition` タイトル処理 | **エッジケース** | `edited_text == name` → `"(無題遷移)"` |
| C-21 | MISRA 8.4 / 11.5 / 18.4 / 15.7 | **設計上抑制** | §7.4.4 および `misra/suppressions.txt` 参照 |
| C-22 | `statable/xml_io.py` が `statable_gui.libcntrl` を import | **逆依存** | `try/except ImportError` フォールバック |
| C-23 | MISRA 抑制リスト（11ルール）vs 文書化（4ルール） | **文書ギャップ** | 7ルール（2.3、2.4、2.5、5.9、8.7、8.9、15.5）未文書 |
| C-24 | `analyze_misra_impact.SUPPRESSED_RULES` vs `suppressions.txt` | **不一致** | 11.5/18.4 欠落、21.6 追加 |
| C-25 | `misra/baseline.md` | **空テンプレート** | 実測値未記録 |
| C-26 | MISRA 出力 XML ファイル名 | **`cppcheck_raw.xml`**（stdout から） | 文書は `cppcheck_stderr.txt` |
| C-27 | `AIResponseParser` のセル単位アクション | **未実装** | v2.2 の7アクション未解析 |
| C-28 | `ChangeApplier._add_variable` / `_add_flag` | **重複チェックなし** | データ重複の可能性 |
| C-29 | `AIPromptGenerator._format_data` | **v2.2 未反映** | `pre_actions` 等が未出力 |
| C-30 | `CellValidator` | **設計が異なる** | `validate()` オーバーライドなし、`suggestion` 未設定 |
| C-31 | `EventValidator` ルール | **意味重複** | `EVENT_UNUSED` ≡ `EVENT_NO_TRANSITION` |
| C-32 | `RoleFunctionValidator.ROLE_FUNC_UNUSED` | **文字列完全一致のみ** | 条件式内の関数呼び出し未検出 |
| C-33 | `StateMachine.role_functions` キー | **純粋名のみ** | 名前空間間の衝突（C-11 参照） |
| C-34 | `libcntrl.RoleFunctionLibrary` キー | **qualified_name** | 衝突なし（`StateMachine` と異なる） |
| C-35 | `RoleFunction` の二重定義 | **2つの別クラス** | `statable.model`（C シグネチャ）vs `libcntrl`（GUI 追跡） |
| C-36 | `GlobalDefinitionsDialog` / `EventDefinitionDialog` の編集が `windowModified` に反映されない | **未対応（v2.4）** | accept/reject 未使用のため |
| C-37 | `InterruptSettingsDialog` / `TypeManagerDialog` の編集が `windowModified` に反映されない | **未対応（v2.4）** | exec() 戻り値未使用 |
| C-38 | `SettingsPanel.add_state` が `settings_changed` を emit しない | **既存動作** | state 追加が windowModified に伝播しない |
| C-39 | ダイアログ経由の編集が `dataModified` に伝播しない | **設計判断** | v2.3 スコープをタブ内編集に限定 |

---

## 13. 用語集

| 用語 | 説明 |
|------|------|
| 層（Layer） | タブごとのステートマシン群 |
| セル（Cell） | (状態, イベント) の組 |
| セル関数 | セルごとの `static` 遷移関数 |
| セルアクション | v2.2：セルに付属する遷移非依存の `ActionStep` |
| セル関係 | v2.2：セル内遷移間の `TransitionRelation` |
| ロール関数 | 条件評価とアクション用の関数 |
| 名前空間（namespace） | ロール関数の名前空間 |
| qualified_name | `namespace.name` |
| call_sites | ロール関数の呼び出しセル一覧 |
| transition_id | call_sites 内のインデックス |
| スーパー include | `statable_all.h` |
| スーパーループ | `{project}_run.c` |
| マーカー | ユーザコード保持用コメント |
| ISR | Interrupt Service Routine（割り込みサービスルーチン） |
| D&D | Drag and Drop |
| MIME | ドラッグデータの形式識別子 |
| MISRA | Motor Industry Software Reliability Association |
| cppcheck | C/C++ 用静的解析ツール |
| Commit | v2.2：`early_return=True`（後続遷移評価を停止） |
| Tentative | v2.2：`early_return=False`（後続遷移が上書き可能） |
| `windowModified` | v2.3：Qt 標準の変更フラグ。タイトルの `[*]` プレースホルダで `*` に置換される |
| `_maybe_save()` | v2.3：未保存確認を一元化する `MainWindow` メソッド |
| `dataModified` | v2.3：`StateMachineTab` の変更通知シグナル |

---

## 14. 付録

### 14.1 ファイルツリー

```
StaTable/
├── .github/
│   └── workflows/
│       └── check.yml
├── code/
│   ├── statable/
│   │   ├── model.py
│   │   ├── state_machine.py
│   │   ├── global_defs.py
│   │   ├── xml_io.py
│   │   ├── mermaid_gen.py
│   │   ├── sample_data.py
│   │   └── parser.py
│   ├── statable_gui/
│   │   ├── main_window.py
│   │   ├── widgets.py
│   │   ├── matrix_table.py
│   │   ├── dialogs.py
│   │   ├── code_generation_dialog.py
│   │   ├── code_generation_settings_dialog.py
│   │   ├── validation_dialog.py
│   │   ├── condition_builder_dialog.py
│   │   ├── global_defs_dialog.py
│   │   ├── event_definition_dialog.py
│   │   ├── event_delivery_settings_dialog.py
│   │   ├── event_queue_dialog.py
│   │   ├── interrupt_handler_edit_dialog.py
│   │   ├── layer_settings_dialog.py
│   │   ├── common_widgets.py
│   │   ├── action_edit_dialog.py
│   │   ├── condition_edit_dialog.py
│   │   ├── role_function_dialog.py
│   │   ├── symbol_picker.py
│   │   ├── logger.py
│   │   ├── preferences.py
│   │   ├── config.py
│   │   ├── traceball.py
│   │   ├── libcntrl/
│   │   │   ├── role_function_library.py
│   │   │   ├── condition_library.py
│   │   │   ├── literal_library.py
│   │   │   ├── role_function_edit_dialog.py
│   │   │   └── literal_management_dialog.py
│   │   └── transition_editor_direct/
│   │       ├── dialog.py
│   │       ├── draft.py
│   │       ├── palette_widget.py
│   │       ├── canvas_widget.py
│   │       ├── code_widget.py
│   │       ├── system_global_dialog.py
│   │       ├── transitions_tab.py
│   │       ├── actions_tab.py
│   │       ├── relations_tab.py
│   │       ├── relations_edit_dialog.py
│   │       ├── transition_actions_dialog.py
│   │       ├── overview_tab.py
│   │       ├── coverage_analyzer.py
│   │       ├── flow_widget.py       (legacy)
│   │       └── edit_dialogs.py      (legacy)
│   ├── codegen/
│   │   ├── c_code_generator.py
│   │   ├── config.py
│   │   ├── code_templates.py
│   │   ├── code_merger.py
│   │   ├── type_mapper.py
│   │   ├── naming_convention.py
│   │   ├── struct_generator.py
│   │   ├── enum_generator.py
│   │   ├── transition_generator.py
│   │   ├── role_function_generator.py
│   │   ├── variable_generator.py
│   │   ├── event_queue_generator.py
│   │   ├── interrupt_generator.py
│   │   ├── timer_generator.py
│   │   ├── osal_generator.py
│   │   ├── sample_data.py
│   │   └── validate/
│   │       ├── validator.py
│   │       ├── models.py
│   │       ├── change_actions.py
│   │       ├── change_applier.py
│   │       ├── prompt_generator.py
│   │       ├── response_parser.py
│   │       ├── clipboard_manager.py
│   │       ├── validation_dialog.py
│   │       ├── logger.py
│   │       ├── data/
│   │       │   ├── validation_rules.py
│   │       │   ├── prompt_templates.py
│   │       │   ├── action_definitions.py
│   │       │   └── keywords.py
│   │       └── items/
│   │           ├── base_validator.py
│   │           ├── state_validator.py
│   │           ├── event_validator.py
│   │           ├── transition_validator.py
│   │           ├── role_function_validator.py
│   │           ├── variable_validator.py
│   │           ├── flag_validator.py
│   │           ├── queue_validator.py
│   │           ├── interrupt_validator.py
│   │           ├── timer_validator.py
│   │           ├── custom_type_validator.py
│   │           └── cell_validator.py
│   ├── tests/
│   │   ├── test_v2_2_p1.py
│   │   ├── test_v2_2_p2.py
│   │   ├── test_v2_2_p3.py
│   │   ├── test_v2_2_p4a.py
│   │   ├── test_v2_2_p4b.py
│   │   ├── test_v2_2_p12_2.py
│   │   ├── test_v2_2_p12_5.py
│   │   ├── test_v2_2_p12_6.py
│   │   ├── test_v2_2_p12_7.py
│   │   ├── test_v2_2_p12_8.py
│   │   ├── test_v2_2_p12_9.py
│   │   ├── test_v2_2_p12_10.py
│   │   └── test_v2_3_p1.py       (v2.3)
│   ├── tools/
│   │   ├── run_misra_check.py
│   │   ├── analyze_misra_impact.py
│   │   ├── find_all_japanese.py
│   │   ├── verify_generated_code.py
│   │   ├── investigate_new_project.py           (v2.3)
│   │   ├── investigate_new_project_step2.py     (v2.3)
│   │   ├── verify_new_project_remaining.py      (v2.3)
│   │   ├── verify_new_project_final.py          (v2.3)
│   │   └── verify_new_project_code_facts.py     (v2.3)
│   ├── misra/
│   │   ├── suppressions.txt
│   │   └── baseline.md
│   └── sdk_doc_tools/
│       ├── class_index.py
│       └── class_index.md
├── docs/
│   ├── SPEC_OVERVIEW_ja.md
│   ├── SPEC_OVERVIEW_en.md
│   ├── SPEC_SCREENS_ja.md
│   ├── SPEC_SCREENS_en.md
│   ├── SPEC_AUDIT_ja.md
│   ├── SPEC_CODEGEN_v3.md
│   └── IMPLEMENTATION_PLAN_v2_3.md    (v2.3)
└── README.md
```

### 14.2 概算ファイルサイズ

| ファイル | 概算 LOC |
|---------|---------|
| `codegen/c_code_generator.py` | ~1,400 |
| `codegen/role_function_generator.py` | ~950 |
| `codegen/code_templates.py` | ~750 |
| `codegen/transition_generator.py` | ~700 |
| `statable/xml_io.py` | ~700 |
| `statable_gui/main_window.py` | ~1,100（v2.3 で +100） |
| `statable_gui/code_generation_dialog.py` | ~400 |
| `transition_editor_direct/canvas_widget.py` | ~450 |

### 14.3 MISRA 成果物

| 成果物 | パス | 内容 |
|--------|------|------|
| 抑制リスト | `misra/suppressions.txt` | 文書化された意図的逸脱（11ルール） |
| ベースライン | `misra/baseline.md` | MISRA 件数のバージョン履歴（現在はテンプレートのみ） |
| 生 XML（stdout） | `misra_report/cppcheck_raw.xml` | cppcheck 出力（stdout からの XML） |
| 生 XML（stderr） | `misra_report/cppcheck_stderr.txt` | cppcheck 出力（stderr からの XML、空の場合あり） |
| サマリ | `misra_report/summary.md` | 集約ルール件数 |
| 影響分析 | `misra_report/impact.md` | codegen ソース帰属 |
| 影響 CSV | `misra_report/impact.csv` | 機械可読な帰属情報 |

---

## 15. 改訂履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-20 | 初版（概要） |
| 2.0 | 2026-09-20 | 詳細版（モジュール別記述、データフロー追加） |
| 2.1 | 2026-09-20 | MISRA C:2012 対応作業：§7.4 追加（ベースライン履歴、抑制、条件/アクション呼び出し分離）、§7.1 にバージョン列追加、§11.2/11.5 更新、§12 C-21 追加、§14.3 MISRA 成果物追加 |
| 2.2 | 2026-09-21 | ソース検証済みの包括的改訂： |
| | | - §1.3：F-14 追加（セル単位 AI アクション）、§1.5 用語拡張 |
| | | - §2.1：validate サブシステム追加、§2.4.4 検証フロー追加 |
| | | - §3.2：`ActionStep`（3.2.5）、`TransitionRelation`（3.2.6）セクション追加、`RoleFunction` 注記更新 |
| | | - §3.3：`get_transitions_for_event` 追加 |
| | | - §3.5.1：12公開関数列挙 |
| | | - §3.5.4：`xml_io` 逆依存注記追加 |
| | | - §3.6：v2.2 Mermaid 追加事項文書化 |
| | | - §3.7：sample_data 件数修正（9ロール関数、4セルアクション、2セル関係） |
| | | - §4：モジュール一覧を23に拡張、§4.5–4.8 v2.2 追加事項文書化 |
| | | - §5：libcntrl セクション書き直し（5.1–5.5） |
| | | - §6：transition_editor_direct モジュール一覧を15に拡張、6.2–6.3 追加 |
| | | - §7.1：`code_templates.py` バージョン修正（v2.2.5）、`validate/` をモジュール17として追加 |
| | | - §7.2：出力ファイル数を14に修正 |
| | | - §7.4.4：抑制理由を全11ルールに拡張 |
| | | - §7.5：validate サブシステムセクション追加（7.5.1–7.5.3） |
| | | - §9.5：MISRA コマンド XML ファイル名を `cppcheck_raw.xml` に修正 |
| | | - §11.1：テスト件数を 537 PASS / 2 SKIP に更新 |
| | | - §11.2：v2.2.6 `_handled` 出力ルール追加 |
| | | - §11.5：検証サブシステムのテストギャップ追加 |
| | | - §12：C-22 から C-35 追加 |
| | | - §13：Commit / Tentative 追加 |
| | | - §14.1：ファイルツリーに `validate/` サブシステム追加 |
| | | - §14.2：ファイルサイズ調整 |
| | | - §14.3：XML ファイル名修正 |
| 2.3 | 2026-09-21 | 新規プロジェクト機能（F-15）： |
| | | - §1.3：F-15 追加（新規プロジェクト、Ctrl+N） |
| | | - §1.4：テストスイートを13、551 PASS / 2 SKIP に更新 |
| | | - §1.5：`windowModified` / `_maybe_save` / `dataModified` 用語追加 |
| | | - §2.4.5：新規プロジェクトフロー追加 |
| | | - §2.5：起動時サンプル維持を明記 |
| | | - §4.2：MainWindow の v2.3 追加メソッド・変更メソッド・保持/リセット対象・`_maybe_save()` 仕様を追加 |
| | | - §4.2.3：**決定#5 変更**：shared libraries を「保持」→「**クリア**」に変更（`open_project` との対称性確保） |
| | | - §4.2.5：v2.3 ショートカット方針（文字列ベース `"Ctrl+N"`、`QKeySequence` import 追加なし）を追加 |
| | | - §4.3：StateMachineTab の `dataModified` シグナル追加と接続方法を記述 |
| | | - §4.5：`transition_changed` シグナルの発火箇所を追記 |
| | | - §4.6：`settings_changed` シグナルの emit 箇所を追記 |
| | | - §8.2：テストジョブを13スイートに更新 |
| | | - §9.4：`test_v2_3_p1.py` を追加 |
| | | - §11.1：テストスイート表に v2.3 追加、合計を 551 PASS / 2 SKIP に更新 |
| | | - §11.3：`test_v2_3_p1.py` の内容（14テスト）追加。`test_new_project_clears_shared_libraries` に更新 |
| | | - §11.5：v2.3 検証ツール5種を追記 |
| | | - §11.6：v2.3 テストギャップ（ダイアログ編集）追加 |
| | | - §12：C-36〜C-39 追加（v2.3 スコープ限定事項） |
| | | - §13：`windowModified` / `_maybe_save` / `dataModified` を追加 |
| | | - §14.1：ファイルツリーに `test_v2_3_p1.py`、v2.3 検証ツール5種、`IMPLEMENTATION_PLAN_v2_3.md` を追加 |
| | | - §14.2：`main_window.py` を ~1,100 LOC に更新 |
| | | - §15：v2.3 改訂履歴（本エントリ） |

---

以上、`SPEC_OVERVIEW_ja.md` v2.3（決定#5 反映済み）の完全版です。
```

---

**決定#5 反映箇所**（v2.3 初版からの差分）：

| セクション | 変更 |
|-----------|------|
| §2.4.5 | 共有ライブラリを「保持」→「クリア」に |
| §4.2.3 | `shared libraries` を「保持」→「**クリア**」、背景説明を追記 |
| §11.3 | `test_new_project_keeps_shared_libraries` → `test_new_project_clears_shared_libraries` |
| §15 | v2.3 エントリに決定#5 変更を追記 |

「次」で `docs/SPEC_OVERVIEW_en.md`（v2.3 決定#5 反映済み完全版）を出力します。