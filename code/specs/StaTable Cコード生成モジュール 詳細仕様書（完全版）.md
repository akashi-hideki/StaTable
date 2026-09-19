了解しました。詳細版を **日本語版 → 英語版** の順に 2 回に分けて出力します。まず日本語版の詳細版をお届けします。

---

# ============================================
# FILE 1: 全体仕様書 v2.0（日本語版・詳細）
# ファイル名: `docs/SPEC_OVERVIEW_ja.md`
# ============================================

````markdown
# StaTable 全体仕様書 v2.0（日本語版・詳細）

版: 2.0
作成日: 2026-09-20
対象: StaTable プロジェクト全体
前提: ソースツリー取得済（`statable/`, `statable_gui/`, `codegen/`）

---

## 目次

1. プロジェクト概要
2. アーキテクチャ
3. データモデル層（`statable/`）
4. GUI 層（`statable_gui/`）
5. 共有ライブラリ（`libcntrl/`）
6. 遷移エディタ（`transition_editor_direct/`）
7. コード生成（`codegen/`）
8. CI/CD
9. 開発環境
10. コーディング規約
11. テスト方針
12. 既知の制約
13. 用語集
14. 付録

---

## 1. プロジェクト概要

### 1.1 目的

**StaTable** は、組み込みシステム向けの状態遷移設計から C コード生成までを一貫して支援する GUI ツールです。設計者は表形式で状態遷移を定義し、ドラッグ&ドロップで遷移条件・アクションを編集し、そのまま組み込み向けの C コードを生成できます。

### 1.2 対象ユーザー

| ユーザー種別 | 想定用途 |
|-------------|---------|
| 組み込みエンジニア | 状態遷移設計・C コード生成 |
| 設計レビュア | 生成された Mermaid 図・遷移表でのレビュー |
| テストエンジニア | 生成コードの単体テスト・CI 検証 |

### 1.3 機能一覧

| # | 機能 | 概要 |
|---|------|------|
| F-01 | 多層ステートマシン編集 | タブ単位で層を表現、優先度で実行順序を制御 |
| F-02 | 遷移表編集 | 行列 = (状態 × イベント) のセル編集 |
| F-03 | D&D フローエディタ | 遷移条件・pre/else アクションを視覚的に配置 |
| F-04 | ロール関数ライブラリ | 共有可能な関数定義、namespace 対応 |
| F-05 | 条件・リテラルライブラリ | 条件式テンプレート、リテラル化 |
| F-06 | グローバル定義 | 変数・フラグ・割り込み・タイマ・キュー |
| F-07 | Mermaid 図生成 | 状態遷移図の自動生成・プレビュー |
| F-08 | C コード生成 | 13 ファイル、マーカー付き |
| F-09 | ユーザーコード保持 | マージ機構で再生成時も保持 |
| F-10 | 検証・AI 診断 | 生成前の整合性チェック |
| F-11 | プロジェクト XML 保存 | 全体の永続化 |
| F-12 | CI 検証 | GitHub Actions による自動チェック |

### 1.4 非機能要件

| 項目 | 要件 |
|------|------|
| 対応 OS | Windows 10/11、Linux（Ubuntu 22.04+） |
| Python | 3.12 |
| GUI | PySide6（Qt 6） |
| 入出力 | XML（UTF-8）、C ソース（UTF-8） |
| 依存 | PySide6, pycparser（テスト時のみ） |
| 生成コード | C99 準拠、`static` 関数の活用 |
| テスト | 12 スイート（`tests/test_v2_2_p*.py`） |
| CI | GitHub Actions、`ubuntu-latest` |

### 1.5 用語定義

| 用語 | 定義 |
|------|------|
| 層（layer） | タブ名で識別される状態機械グループ。`sm.layer_name` |
| セル | (state, event) の組。遷移関数の最小単位 |
| セル関数 | 1 セル分の遷移を処理する `static` 関数 |
| ロール関数 | 遷移時・条件判定・ISR から呼ばれる関数 |
| namespace | ロール関数の所属層または明示名前空間 |
| qualified_name | `namespace.name` 形式の一意名（例: `Driver.Init`） |
| call_sites | ロール関数ごとの呼び出し元セル一覧 |
| transition_id | call_sites 内のインデックス。`0xFFFF` = 未一致 |
| スーパーインクルード | `statable_all.h`。全生成ヘッダを一括 include |
| スーパーループ | `{project}_run.c`。全層のメインループ |
| マーカー | ユーザーコード保持用のコメント（`[[STABLE_...]]`） |

---

## 2. アーキテクチャ

### 2.1 全体構成図

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
│  │  │ + 各編集ダイアログ                                │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────┐  ┌───────────────────┐   │  │
│  │  │ transition_editor_direct │  │ libcntrl/         │   │  │
│  │  │ (D&D エディタ)            │  │ (共有ライブラリ)   │   │  │
│  │  └──────────────────────────┘  └───────────────────┘   │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │ 呼び出し                         │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    codegen/                            │  │
│  │  CCodeGenerator + 15 サブジェネレータ                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │ 参照                             │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    statable/                           │  │
│  │  StateMachine, GlobalDefinitions, XML I/O              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 レイヤ構成

| レイヤ | パッケージ | 責務 | 依存先 |
|--------|-----------|------|-------|
| プレゼンテーション | `statable_gui/` | GUI 表示・ユーザー操作 | codegen, statable, libcntrl |
| D&D 編集 | `transition_editor_direct/` | セル単位の遷移編集 UI | statable_gui |
| 共有ライブラリ | `libcntrl/` | ロール関数等の共有管理 | （なし） |
| コード生成 | `codegen/` | C コード生成 | statable |
| データモデル | `statable/` | 状態機械・全体定義・XML | （なし） |

**依存方向**: `statable_gui` → `codegen` → `statable`。逆依存なし。

### 2.3 依存関係の詳細

```
statable_gui/main_window.py
  ├── statable.state_machine.StateMachine
  ├── statable.xml_io.project_to_xml / project_from_xml
  ├── statable.global_defs.GlobalDefinitions
  ├── statable.sample_data.create_sample_*
  ├── libcntrl.role_function_library.RoleFunctionLibrary
  ├── libcntrl.condition_library.ConditionLibrary
  ├── libcntrl.literal_library.LiteralLibrary
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
  ├── create_sample_state_machine()      # デモ状態機械
  ├── add_state_machine_tab("Application", sample_sm)
  └── 各タブは StateMachineTab を生成
       ├── MatrixTableWidget（遷移表）
       ├── MermaidWidget（図）
       └── SettingsPanel（状態・ロール関数）
```

#### 2.4.2 セル編集 → 保存

```
MatrixTableWidget.cellDoubleClicked(row, col)
  ├── sm.get_transitions_for_cell(state, event)
  ├── transition_to_flow_item(trans) で ActionDraft 構築
  ├── ActionEditorDialog を開く
  │    ├── PaletteWidget（左）
  │    ├── FlowCanvas（中央）
  │    └── CodeWidget（下）
  ├── D&D で flow_items を編集
  ├── OK → flow_item_to_transition(item) で Transition に戻す
  └── sm.transitions を更新 → populate() → 再描画
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
  └── QMessageBox で完了通知 + 警告表示
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
   ├── create_sample_state_machine() → role_functions を libcntrl に登録
   ├── QTabWidget 設定
   ├── create_menus() / create_toolbar()
   ├── TraceBallWidget 生成（非表示）
   └── add_state_machine_tab("Application", sample_sm)
4. app.exec() でイベントループ
```

---

## 3. データモデル層（`statable/`）

### 3.1 モジュール一覧

| # | モジュール | 行数目安 | 責務 |
|---|-----------|---------|------|
| 1 | `__init__.py` | - | 公開 API |
| 2 | `model.py` | 100 | データクラス・enum |
| 3 | `state_machine.py` | 60 | StateMachine コンテナ |
| 4 | `global_defs.py` | 200 | グローバル定義 |
| 5 | `xml_io.py` | 600 | XML 保存/読込 |
| 6 | `mermaid_gen.py` | 50 | Mermaid 図生成 |
| 7 | `sample_data.py` | 130 | サンプルデータ |
| 8 | `parser.py` | 3 | スタブ |

### 3.2 `model.py`

#### 3.2.1 enum 定義

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
    DIRECT = "direct"    # 直接配送
    QUEUE  = "queue"     # キュー配送
    DOUBLE = "double"    # 二重配送

class EventSourceLayer(Enum):
    DRIVER = "driver"
    MIDDLEWARE = "middleware"
```

#### 3.2.2 `State`

| フィールド | 型 | 既定 | 説明 |
|-----------|---|------|------|
| `name` | str | – | 状態名 |
| `type` | StateType | NORMAL | 状態種別 |
| `parent` | Optional[str] | None | 親状態（階層用） |
| `entry` | str | "" | entry アクション |
| `exit` | str | "" | exit アクション |
| `do` | str | "" | do アクション |
| `description` | str | "" | 説明 |

#### 3.2.3 `Event`

| フィールド | 型 | 既定 | 説明 |
|-----------|---|------|------|
| `name` | str | – | イベント名（空 = 完了遷移） |
| `id` | Optional[int] | None | イベント ID |
| `kind` | EventKind | SIGNAL | 種別 |
| `params` | List[str] | [] | パラメータ名 |
| `priority` | int | 0 | 優先度 |
| `description` | str | "" | 説明 |
| `delivery_type` | EventDeliveryType | DIRECT | 配送タイプ |
| `source_layer` | EventSourceLayer | DRIVER | 発生源層 |
| `data_type` | str | "" | 付随データ型 |
| `data_name` | str | "" | 付随データ名 |
| `title` | str | "" | 表示名（未設定時自動生成） |

#### 3.2.4 `Transition`

| フィールド | 型 | 既定 | 説明 |
|-----------|---|------|------|
| `source` | str | – | 遷移元状態 |
| `event` | str | – | イベント名 |
| `condition` | str | "" | 条件式 |
| `pre_actions` | List[str] | [] | 遷移直前処理 |
| `target` | str | "" | 遷移先 |
| `has_else` | bool | True | else 節の有無 |
| `else_target` | str | "" | else 遷移先 |
| `else_actions` | List[str] | [] | else アクション |
| `action` | str | "" | 旧フィールド（未使用） |
| `transition_type` | str | "external" | 遷移タイプ |
| `title` | str | "" | 表示名 |

#### 3.2.5 `RoleFunction`

| フィールド | 型 | 既定 | 説明 |
|-----------|---|------|------|
| `name` | str | – | 純粋名（`Init`） |
| `namespace` | str | "" | 名前空間（`Driver`） |
| `description` | str | "" | 説明 |
| `return_type` | str | "void" | 戻り型 |
| `arg1_type` | str | "" | 引数 1 型 |
| `arg1_name` | str | "" | 引数 1 名 |
| `arg2_type` | str | "" | 引数 2 型 |
| `arg2_name` | str | "" | 引数 2 名 |
| `title` | str | "" | 表示名 |

**プロパティ**:
- `qualified_name -> str`: `namespace.name` または `name`

**クラスメソッド**:
- `from_legacy_name(legacy_name, layer_names=None) -> RoleFunction`:
  - `"Driver_Init"` → `namespace="Driver", name="Init"`
  - `layer_names` に該当なしなら `namespace=""`

### 3.3 `state_machine.py`

#### 3.3.1 クラス `StateMachine`

**属性**

| 属性 | 型 | 既定 | 説明 |
|------|----|----|------|
| `states` | Dict[str, State] | {} | 状態辞書 |
| `events` | Dict[str, Event] | {} | イベント辞書 |
| `transitions` | List[Transition] | [] | 遷移リスト |
| `role_functions` | Dict[str, RoleFunction] | {} | ロール関数辞書 |
| `initial_state` | Optional[str] | None | 初期状態 |
| `layer_priority` | int | 5 | 層優先度（1〜9） |
| `layer_description` | str | "" | 層説明 |
| `layer_name` | str | "" | 層名 |

**メソッド**

| メソッド | 説明 | 例外 |
|---------|------|------|
| `add_state(state)` | 状態追加 | 重複で `ValueError` |
| `add_event(event)` | イベント追加 | 重複で `ValueError` |
| `remove_event(name)` | イベントと関連遷移を削除 | – |
| `add_transition(trans)` | 遷移追加 | source/target/event 未定義で `ValueError` |
| `remove_transition(trans)` | 遷移削除 | – |
| `set_initial(name)` | 初期状態設定 | 未定義で `ValueError` |
| `add_role_function(rf)` | ロール関数追加 | `rf.name` 重複で `ValueError` |
| `remove_role_function(name)` | ロール関数削除 | – |
| `get_transitions_for_cell(source, event) -> List[Transition]` | セル遷移取得 | – |
| `get_transitions_for_event(event) -> List[Transition]` | イベント別取得 | – |

**注意**: `add_role_function` は `rf.name`（純粋名）でキー管理。`Driver.Init` と `App.Init` は衝突します。

### 3.4 `global_defs.py`

#### 3.4.1 データクラス一覧

| クラス | 用途 |
|-------|------|
| `StructMemberDef` | 構造体メンバ |
| `CustomTypeDef` | ユーザー定義型 |
| `SystemVariable` | グローバル変数 |
| `EventFlag` | イベントフラグ |
| `InterruptAction` | 割り込みアクション |
| `InterruptHandlerDef` | 割り込みハンドラ |
| `DevicePlaceholderDef` | デバイスリソース仮定義 |
| `TimerDerivedDef` | 派生タイマ |
| `TimerBaseDef` | タイマ基準 |
| `EventQueueDef` | イベントキュー |

#### 3.4.2 `InterruptHandlerDef`

| フィールド | 型 | 既定 | 説明 |
|-----------|---|------|------|
| `name` | str | – | ハンドラ名 |
| `description` | str | "" | 説明 |
| `event_names` | List[str] | [] | 関連イベント |
| `is_timer` | bool | False | タイマ割り込みか |
| `actions` | List[InterruptAction] | [] | アクション |
| `title` | str | "" | 表示名 |
| `used_role_functions` | List[str] | [] | 使用ロール関数（自動抽出） |
| `used_variables` | List[str] | [] | 使用変数（自動抽出） |

#### 3.4.3 `GlobalDefinitions`

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
- `add_timer_variables()`: タイマ変数を `variables` に自動登録（`group="Timer"`）
- `variable_groups() -> List[str]`: 変数グループ一覧
- `flag_groups() -> List[str]`: フラググループ一覧
- `custom_type_names() -> List[str]`: カスタム型名一覧

### 3.5 `xml_io.py`

#### 3.5.1 公開関数

| 関数 | 説明 |
|------|------|
| `project_to_xml(tabs, gd, filepath, role_lib=None, cond_lib=None, lit_lib=None, project_settings=None)` | プロジェクト保存 |
| `project_from_xml(filepath) -> (tabs, gd, role_lib, cond_lib, lit_lib, project_settings)` | プロジェクト読込 |

#### 3.5.2 XML 構造

```xml
<Project name="MyProject">
  <ProjectSettings>
    <CodeGeneration
      project_name="MyProject"
      table_type="array"
      generation_style="table_driven"
      os_type="non_rtos"
      folder_structure="by_type"
      include_dir_name="include"
      source_dir_name="src"
      common_dir_name="common"
      project_dir_name="project"
      generate_super_include="true"
      super_include_file="statable_all.h"
      max_consecutive_pending_events="16"
      external_includes_in_super="true"
      external_includes_in_role="true"
      external_includes_in_transitions="false"
      external_includes_in_common="false">
      <ExternalIncludes>
        <Include name="..."/>
      </ExternalIncludes>
    </CodeGeneration>
  </ProjectSettings>
  <GlobalDefinitions>
    <CustomTypes>...</CustomTypes>
    <SystemVariables>...</SystemVariables>
    <EventFlags>...</EventFlags>
    <Interrupts>
      <Interrupt name="..." description="..." event_names="..." is_timer="..." title="...">
        <Action condition="..." action="..."/>
        <UsedRoleFunction ref="Driver.Init"/>
        <UsedVariable name="counter"/>
      </Interrupt>
    </Interrupts>
    <DevicePlaceholders>...</DevicePlaceholders>
    <TimerBase>
      <Timer variable_name="..." unit="..." data_type="..." title="..." interrupt_name="...">
        <Derived period_name="..." multiplier="..." variable_name="..." data_type="..." title="..."/>
      </Timer>
    </TimerBase>
    <ExtraTimers>...</ExtraTimers>
    <EventQueues>
      <Queue name="..." size="..." element_type="..." event_ids="..." ... />
    </EventQueues>
  </GlobalDefinitions>
  <SharedLibraries>
    <RoleFunctionLibrary>...</RoleFunctionLibrary>
    <ConditionLibrary>...</ConditionLibrary>
    <LiteralLibrary>...</LiteralLibrary>
  </SharedLibraries>
  <Tab name="Application">
    <StateMachine initial="..." layer_priority="5" layer_name="Application">
      <States>...</States>
      <Events>...</Events>
      <RoleFunctions>
        <RoleFunction name="Init" namespace="Driver" .../>
      </RoleFunctions>
      <Transitions>
        <Transition source="..." event="..." condition="..." target="..." has_else="true" else_target="...">
          <PreAction action="..."/>
          <ElseAction action="..."/>
        </Transition>
      </Transitions>
    </StateMachine>
  </Tab>
</Project>
```

#### 3.5.3 レガシー移行

`RoleFunction` の `namespace` 未設定 + `name` が `<layer>_` プレフィックス付きの場合、自動で namespace を分離。

#### 3.5.4 既知の制約

- `super_include_dir` は **保存されない**（読込時に既定値 `"common"` に戻る）
- `_normalize_actions` で 1 文字ずつに分解された古いデータを自動結合

### 3.6 `mermaid_gen.py`

| 関数 | 説明 |
|------|------|
| `generate_mermaid(sm) -> str` | StateMachine から `stateDiagram-v2` を生成 |
| `_truncate_condition(condition, max_chars=50) -> str` | 長い条件を省略 |

**出力形式**:
```
stateDiagram-v2
    direction LR
    [*] --> InitialState
    Source --> Target : Title (Event) [Condition]
    note right of State : internal: Title (Event)
```

### 3.7 `sample_data.py`

| 関数 | 説明 |
|------|------|
| `create_sample_state_machine() -> StateMachine` | 4 状態・5 イベント・6 遷移・2 ロール関数 |
| `create_sample_global_defs() -> GlobalDefinitions` | 変数 3・フラグ 2・型 2・割り込み 1・タイマ 2 系統・キュー 1 |

**注意**: `create_sample_state_machine` のロール関数は **レガシー形式**（`Sensor_Init`, `Error_Log`）。namespace 未使用。

---

## 4. GUI 層（`statable_gui/`）

### 4.1 モジュール一覧

| # | モジュール | 主クラス | 用途 |
|---|-----------|---------|------|
| 1 | `main_window.py` | `MainWindow` | メインウィンドウ |
| 2 | `widgets.py` | `StateMachineTab`, `SettingsPanel`, `MermaidWidget` | タブ |
| 3 | `matrix_table.py` | `MatrixTableWidget` | 遷移表 |
| 4 | `code_generation_dialog.py` | `CodeGenerationDialog`, `WarningCollector` | 生成 UI |
| 5 | `code_generation_settings_dialog.py` | `CodeGenerationSettingsDialog` | 設定 UI |
| 6 | `condition_builder_dialog.py` | `ConditionBuilderDialog`, `LiteralizationDialog` | 条件式ビルダー |
| 7 | `config.py` | – | 定数・リソースパス |
| 8 | `logger.py` | `StaTableLogger` | ログ |
| 9 | `preferences.py` | `Preferences` | アプリ設定 |
| 10 | `traceball.py` | `TraceBallWidget` | ログ表示 |
| 11 | `global_defs_dialog.py` | `GlobalDefinitionsDialog` | グローバル定義 |
| 12 | `event_definition_dialog.py` | `EventDefinitionDialog` | イベント定義 |
| 13 | `event_delivery_settings_dialog.py` | `EventDeliverySettingsDialog` | 配送設定 |
| 14 | `interrupt_handler_edit_dialog.py` | `InterruptHandlerEditDialog` | 割り込み編集 |
| 15 | `layer_settings_dialog.py` | `LayerSettingsDialog` | 層設定 |
| 16 | `validation_dialog.py` | `ValidationDialog` | 検証 |
| 17 | `common_widgets.py` | `TypeManagerDialog` | 型管理 |
| 18 | `action_edit_dialog.py` | `ActionEditDialog` | 旧 action 編集 |
| 19 | `role_function_dialog.py` | `RoleFunctionDialog` | 旧ロール関数編集 |
| 20 | `global_defs.py` | – | （再エクスポート推定） |

### 4.2 `MainWindow`

#### 4.2.1 主要属性

| 属性 | 型 | 説明 |
|------|----|----|
| `logger` | StaTableLogger | ロガー |
| `prefs` | Preferences | アプリ設定 |
| `config_manager` | ConfigManager | コード生成設定 |
| `global_defs` | GlobalDefinitions | グローバル定義 |
| `role_function_library` | RoleFunctionLibrary | 共有ライブラリ |
| `condition_library` | ConditionLibrary | 条件ライブラリ |
| `literal_library` | LiteralLibrary | リテラルライブラリ |
| `tab_widget` | QTabWidget | タブ |
| `traceball` | TraceBallWidget | ログ |

#### 4.2.2 主要メソッド

| メソッド | 説明 |
|---------|------|
| `create_toolbar()` | ツールバー生成 |
| `create_menus()` | メニュー生成 |
| `add_state_machine_tab(name, sm)` | タブ追加 |
| `close_tab(index)` | タブ閉じ |
| `rename_tab_at(index)` | タブ名変更 |
| `open_project()` | XML 読込 |
| `save_project()` | XML 保存 |
| `open_code_generation_dialog()` | 生成ダイアログ |
| `save_generated_code_direct()` | 直接保存 |
| `open_validation_dialog()` | 検証 |
| `_get_all_layers() -> List[(name, sm)]` | 全層収集（優先度順） |

### 4.3 `StateMachineTab`

| メソッド | 説明 |
|---------|------|
| `__init__(sm, gd, lib..., parent)` | 初期化 |
| `update_mermaid()` | 設定反映 + Mermaid 更新 |

**レイアウト**: QSplitter（左: MatrixTable + Mermaid、右: SettingsPanel）

### 4.4 `MatrixTableWidget`

| メソッド | 説明 |
|---------|------|
| `populate()` | 遷移表再構築 |
| `open_transition_dialog(row, col)` | D&D エディタ起動 |
| `keyPressEvent(event)` | Enter/F2: 編集、Delete: 削除 |
| `_find_transitions(state, event)` | セル遷移取得 |
| `_generate_cell_label(trans, event)` | セル表示文字列 |

### 4.5 `CodeGenerationDialog`

| メソッド | 説明 |
|---------|------|
| `_load_saved_settings()` | `codegen_settings.json` 読込 |
| `_save_settings()` | 4 項目のみ保存 |
| `_generate_code()` | 生成実行 |
| `_save_code()` | 保存実行 |
| `_show_warnings(records)` | 警告表示（重複除去） |
| `_update_preview()` | プレビュー更新 |

**属性 `all_layers`**: `MainWindow` から後付けされる。

### 4.6 `WarningCollector`

```python
class WarningCollector(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records: List[str] = []
    def emit(self, record):
        if record.levelno >= logging.WARNING:
            try:
                msg = record.getMessage()
            except Exception:
                msg = str(record.msg)
            self.records.append(msg)
```

### 4.7 `ConditionBuilderDialog`

| 引数 | 説明 |
|------|------|
| `condition` | 既存条件式 |
| `event_name` | イベント名 |
| `global_defs` | グローバル定義 |
| `state_machine` | 状態機械 |
| `literal_library` | リテラルライブラリ |
| `states` | 遷移先候補 |
| `target_state` | 現在の遷移先 |
| `else_target_state` | 現在の else 遷移先 |

| 取得メソッド | 説明 |
|------------|------|
| `get_condition_text()` | 条件式 |
| `get_event_name()` | イベント名 |
| `get_target_state()` | 遷移先 |
| `get_else_target_state()` | else 遷移先 |
| `get_c_code_text()` | C コードプレビュー |

---

## 5. 共有ライブラリ（`libcntrl/`）

### 5.1 モジュール一覧

| モジュール | 主クラス |
|-----------|---------|
| `role_function_library.py` | `RoleFunctionLibrary`, `RoleFunction` |
| `condition_library.py` | `ConditionLibrary`, `ConditionTemplate` |
| `literal_library.py` | `LiteralLibrary`, `LiteralDefinition` |
| `role_function_edit_dialog.py` | `RoleFunctionEditDialog` |
| `literal_management_dialog.py` | `LiteralManagementDialog`, `LiteralEditDialog` |

### 5.2 `RoleFunctionLibrary`

| メソッド | 説明 |
|---------|------|
| `_key(rf) -> str` | `rf.qualified_name` |
| `add(rf)` | 重複で `ValueError` |
| `remove(name)` | qualified / 純粋名両対応 |
| `get(name) -> Optional[RoleFunction]` | qualified / 純粋名両対応 |
| `list_all() -> List[RoleFunction]` | 全件 |

### 5.3 `RoleFunction`（libcntrl 版）

| フィールド | 型 | 既定 |
|-----------|---|------|
| `name` | str | – |
| `namespace` | str | "" |
| `description` | str | "" |
| `title` | str | "" |
| `used_global_vars` | List[str] | [] |
| `used_events` | List[str] | [] |
| `used_literals` | List[str] | [] |

**プロパティ**: `qualified_name -> str`

**注意**: `statable.RoleFunction` とは別クラス。`namespace` は両方にあるが、キー管理が異なる。

---

## 6. 遷移エディタ（`transition_editor_direct/`）

### 6.1 モジュール一覧

| モジュール | 主クラス | 用途 |
|-----------|---------|------|
| `draft.py` | `ActionDraft`, `FlowItem`, `SystemGlobal`, `TransitionParams` | モデル |
| `dialog.py` | `ActionEditorDialog` | エントリポイント |
| `palette_widget.py` | `PaletteWidget`, `PaletteListWidget` | パレット |
| `canvas_widget.py` | `FlowCanvas`, `FlowNodeItem` | キャンバス |
| `code_widget.py` | `CodeWidget` | コードプレビュー |
| `system_global_dialog.py` | `SystemGlobalDialog` | グローバル編集 |
| `flow_widget.py` | `FlowWidget`, `FlowListWidget` | **レガシー** |
| `edit_dialogs.py` | `FunctionEditDialog`, `TransitionEditDialog` | **レガシー** |

### 6.2 MIME プロトコル

```
MIME_TYPE = "application/x-flow-item"
Payload   = {"item_type": "function"|"transition", "name": str}
```

### 6.3 ドロップ規則

| ドロップ先 | `item_type=function` の扱い |
|-----------|---------------------------|
| `transition` | 親 transition の `pre_actions` に追加 |
| `pre_action` | 親 transition の `pre_actions` に追加 |
| `else` | 親 transition の `else_actions` に追加 |
| `else_action` | 親 transition の `else_actions` に追加 |
| それ以外 | 単独 `function` ノードとして追加 |

`item_type=transition` は常に新規 transition ノードとして追加。

### 6.4 `ActionDraft`

| フィールド | 型 | 説明 |
|-----------|---|------|
| `source` | str | 遷移元状態 |
| `event` | str | イベント名 |
| `flow_items` | List[FlowItem] | フロー |
| `default_target` | str | 既定遷移先 |
| `system_globals` | List[SystemGlobal] | システムグローバル |
| `generated_code` | str | 生成コード |
| `role_func_map` | Dict[str, str] | ロール関数名マップ |
| `user_code` | Dict[str, str] | ユーザーコード |

### 6.5 `FlowItem`

| フィールド | 型 | 説明 |
|-----------|---|------|
| `item_type` | str | `function` / `transition` / `pre_action` / `else` / `else_action` |
| `name` | str | 名前 |
| `edited_text` | str | 編集後テキスト |
| `params` | Dict | パラメータ |
| `pos_x`, `pos_y` | Optional[float] | 位置 |

**メソッド**: `display_text() -> str`

### 6.6 変換関数

| 関数 | 説明 |
|------|------|
| `ensure_list(value) -> List[str]` | 文字列/None/リストを正規化 |
| `transition_to_flow_item(trans) -> FlowItem` | Transition → FlowItem |
| `flow_item_to_transition(item, source, event) -> Transition` | FlowItem → Transition |

**注意**: `transition_to_flow_item` で空イベントは `"NewEvent"` に変換される（バグ）。

---

## 7. コード生成（`codegen/`）

詳細は別途 **成果物② 詳細仕様書 v3.0** を参照。要約のみ。

### 7.1 モジュール一覧（16）

`c_code_generator.py`, `code_merger.py`, `code_templates.py`, `transition_generator.py`, `role_function_generator.py`, `struct_generator.py`, `enum_generator.py`, `variable_generator.py`, `event_queue_generator.py`, `interrupt_generator.py`, `timer_generator.py`, `osal_generator.py`, `type_mapper.py`, `naming_convention.py`, `config.py`, `sample_data.py`

### 7.2 出力ファイル（13）

`statable_types.h`, `statable_transitions.h/.c`, `statable_role_functions.h/.c`, `statable_init.c`, `statable_event_queue.c`, `statable_interrupt.c`, `statable_timer.c`, `osal.h/.c`, `statable_all.h`, `{project}_run.c`

### 7.3 フォルダ構成

| 構成 | 配置 |
|------|------|
| `flat` | 全ファイルを 1 ディレクトリ |
| `by_type` | `include/` / `src/` / `common/` |
| `by_layer` | 層別サブディレクトリ + 共通をルートに |

---

## 8. CI/CD

### 8.1 ワークフロー

`.github/workflows/check.yml`（リポジトリルート）

### 8.2 ジョブ構成

| ジョブ | 依存 | 目的 |
|-------|------|------|
| `no-japanese` | – | 非 ASCII 検出 |
| `syntax` | – | compileall |
| `tests` | syntax | 12 テストスイート |
| `generated-code` | syntax | C コード生成検証 |

### 8.3 環境変数

| 変数 | 値 | 用途 |
|------|-----|------|
| `QT_QPA_PLATFORM` | `offscreen` | GUI ヘッドレス |
| `STATABLE_DISABLE_MERMAID` | `1` | Mermaid 抑止 |
| `PYTHONIOENCODING` | `utf-8` | 文字化け防止 |

### 8.4 Qt システムライブラリ

```
libegl1, libgl1, libglib2.0-0, libdbus-1-3,
libxkbcommon0, libxkbcommon-x11-0,
libxcb-icccm4, libxcb-image0, libxcb-keysyms1,
libxcb-randr0, libxcb-render-util0, libxcb-shape0,
libxcb-xinerama0, libxcb-xfixes0, libxcb-cursor0,
libfontconfig1, libfreetype6
```

---

## 9. 開発環境

### 9.1 必須

| 項目 | バージョン |
|------|-----------|
| Python | 3.12 |
| PySide6 | 最新 |
| Git | 最新 |
| OS | Windows 10/11 or Ubuntu 22.04+ |

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
# ... 他 11 スイート
```

---

## 10. コーディング規約

### 10.1 Python

| 項目 | 規約 |
|------|------|
| インデント | スペース 4 |
| 文字列 | ダブルクォート優先 |
| 型ヒント | 公開 API には必須 |
| docstring | モジュール先頭 + 公開クラス/メソッド |
| 命名 | `snake_case`（関数・変数）、`PascalCase`（クラス） |

### 10.2 コメント言語

- **コード内コメント・docstring**: 英語推奨（CI の `no-japanese` ジョブで検出）
- **仕様書**: 日本語版・英語版を分離

### 10.3 C コード

- C99 準拠
- `static` 関数の積極活用
- 生成ファイル冒頭に `@file` / `@brief` / `@note` / `@date`

---

## 11. テスト方針

### 11.1 テストスイート

| ファイル | 対象 |
|---------|------|
| `test_v2_2_p1.py` | 基本データモデル |
| `test_v2_2_p2.py` | StateMachine |
| `test_v2_2_p3.py` | GUI ヘルパー |
| `test_v2_2_p4a.py` | コード生成（基本） |
| `test_v2_2_p4b.py` | コード生成（詳細） |
| `test_v2_2_p12_2.py` | Stage 2 機能 |
| `test_v2_2_p12_5.py` | Stage 5 機能 |
| `test_v2_2_p12_6.py` | Stage 6 機能 |
| `test_v2_2_p12_7.py` | Stage 7 機能 |
| `test_v2_2_p12_8.py` | Stage 8 機能 |
| `test_v2_2_p12_9.py` | Stage 9 機能 |
| `test_v2_2_p12_10.py` | Stage 10 機能 |

### 11.2 実行環境

- ローカル: Windows でも実行可
- CI: `ubuntu-latest` + `QT_QPA_PLATFORM=offscreen`

### 11.3 検証ツール

- `tools/find_all_japanese.py`: 非 ASCII 検出
- `tools/verify_generated_code.py`: 生成 C コードの構文・構造検証

---

## 12. 既知の制約

| # | 項目 | 状態 | 影響範囲 |
|---|------|------|---------|
| 1 | `generation_style` / `table_type` GUI 切替 | 未実装（強制固定） | 設定 UI |
| 2 | `switch_case` 生成 | 未実装（フォールバック） | `transition_generator` |
| 3 | `switch` / `dictionary` テーブル | 未実装（フォールバック） | `transition_generator` |
| 4 | `external_includes_in_role/transitions/common` | 未実装 | `c_code_generator` |
| 5 | FreeRTOS / ThreadX OSAL | include のみ | `osal_generator` |
| 6 | `super_include_dir` XML 未保存 | 未保存（既定に戻る） | `xml_io` / `main_window` |
| 7 | ロール関数一意性の不一致 | qualified 名 vs 純粋名 | `statable` / `libcntrl` |
| 8 | 空イベント → `"NewEvent"` | バグ | `draft.transition_to_flow_item` |
| 9 | `palette_widget._add_function` import | フォールバックなし | `palette_widget` |
| 10 | `project_dir_name` | 予約のみ未使用 | `config` |
| 11 | `flow_widget.py` / `edit_dialogs.py` | レガシー | `transition_editor_direct` |
| 12 | `statable_gui/global_defs.py` | 実体不明 | `statable_gui` |

---

## 13. 用語集

| 用語 | 説明 |
|------|------|
| 層 | タブ単位の状態機械グループ |
| セル | (state, event) の組 |
| セル関数 | セル単位の `static` 遷移関数 |
| ロール関数 | 条件判定・アクション用関数 |
| namespace | ロール関数の名前空間 |
| qualified_name | `namespace.name` |
| call_sites | ロール関数呼び出し元一覧 |
| transition_id | call_sites インデックス |
| スーパーインクルード | `statable_all.h` |
| スーパーループ | `{project}_run.c` |
| マーカー | ユーザーコード保持コメント |
| ISR | 割り込みサービスルーチン |
| D&D | ドラッグ&ドロップ |
| MIME | ドラッグデータの形式識別子 |

---

## 14. 付録

### 14.1 ファイル木構成

```
StaTable/
├── .github/
│   └── workflows/
│       └── check.yml
├── code/
│   ├── statable/
│   ├── statable_gui/
│   │   ├── transition_editor_direct/
│   │   └── libcntrl/
│   ├── codegen/
│   ├── tests/
│   └── tools/
├── docs/
│   ├── SPEC_OVERVIEW_ja.md
│   ├── SPEC_OVERVIEW_en.md
│   └── SPEC_CODEGEN_v3.md
└── README.md
```

### 14.2 主要ファイルサイズ目安

| ファイル | 行数目安 |
|---------|---------|
| `codegen/c_code_generator.py` | ~1,400 |
| `codegen/role_function_generator.py` | ~900 |
| `codegen/code_templates.py` | ~700 |
| `statable_gui/main_window.py` | ~1,000 |
| `statable_gui/code_generation_dialog.py` | ~400 |
| `transition_editor_direct/canvas_widget.py` | ~450 |

---

## 15. 改訂履歴

| 版 | 日付 | 内容 |
|----|------|------|
| 1.0 | 2026-09-20 | 初版（要約） |
| 2.0 | 2026-09-20 | 詳細化（モジュール別記述、データフロー追加） |
````

---

# 続けて英語版を出力します

上記日本語版 v2.0 の内容を、英語で同等の詳細度で出力します。**次のメッセージで** `docs/SPEC_OVERVIEW_en.md` として完成版をお届けします。

## ご確認ください

1. **この粒度でよいか**：
   - もっと細かく（メソッド単位の引数・戻り値まで）
   - これくらいで十分（章立てと概要が分かれば OK）
2. **追加したい章**：
   - 画面遷移図（GUI の操作フロー）
   - シーケンス図（コード生成の詳細ステップ）
   - エラー処理方針
3. **ファイル分割**：
   - 1 ファイルだと長すぎる → 章ごとに分割（`docs/01_overview_ja.md` など）

教えていただければ、英語版をその方針で出力します。**このままでよければ「進めて」とお知らせください。**