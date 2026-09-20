```markdown
# StaTable SDK API リファレンス

Version: 1.1（日本語版 / レビュー済み）
Date: 2026-09-21
対象: ツールベンダー開発者
ライセンス: MIT / Apache 2.0
対象バージョン: StaTable v2.2.9 / v2.6.1

---

## 目次

1. [概要](#1-概要)
2. [クイックスタート](#2-クイックスタート)
3. [データモデル（コアAPI）](#3-データモデルコアapi)
4. [コード生成API](#4-コード生成api)
5. [検証API](#5-検証api)
6. [MISRA連携API](#6-misra連携api)
7. [ユーティリティAPI](#7-ユーティリティapi)
8. [エラーコード](#8-エラーコード)
9. [制限事項](#9-制限事項)
10. [付録](#10-付録)

---

## 1. 概要

### 1.1 目的

StaTable SDK は、StaTable GUI アプリケーションが使用する状態遷移設計・C コード生成エンジンへのプログラム的アクセスを提供する。ツールベンダーは以下を実現できる：

- 独自の状態機械設計ツールの構築
- 状態遷移モデルからの組み込み向け C コード生成
- 生成前のモデル検証（11カテゴリ、35ルール）
- MISRA C:2012 チェックの情報提供目的での統合
- マーカー方式マージによる再生成時のユーザコード保持

### 1.2 対象読者

| ユーザー種別 | 想定用途 |
|-------------|---------|
| ツールベンダー開発者 | StaTable エンジンを商用ツールに統合 |
| 組み込みツールチェーン提供者 | 既存 IDE への状態機械コード生成追加 |
| フレームワーク開発者 | StaTable 上へのドメイン特化モデリング層の構築 |

### 1.3 機能一覧

| # | 機能 | SDKエントリポイント |
|---|------|-------------------|
| F-01 | ステートマシン構築 | §3 `StateMachine` |
| F-02 | グローバル定義 | §3 `GlobalDefinitions` |
| F-03 | プロジェクト XML 永続化 | §7 `project_to_xml` / `project_from_xml` |
| F-04 | Mermaid 図生成 | §7 `generate_mermaid` |
| F-05 | C コード生成（14ファイル） | §4 `CCodeGenerator` |
| F-06 | マーカー方式ユーザコード保持 | §4 `CodeMerger`（`save_generated_code_with_merge` 経由） |
| F-07 | モデル検証（35ルール） | §5 `CodeGenerationValidator` |
| F-08 | AI 支援変更適用 | §5 `ChangeApplier` |
| F-09 | MISRA C:2012 情報提供チェック | §6 CLI ツール |
| F-10 | セル単位アクション・関係（v2.2） | §3 `ActionStep`, `TransitionRelation` |

### 1.4 非機能要件

| 項目 | 要件 |
|------|------|
| Python | 3.12 |
| OS | Windows 10/11、Linux（Ubuntu 22.04+） |
| 外部依存 | PySide6（GUI モジュールのみ。コア SDK は GUI 非依存） |
| MISRA チェッカー | cppcheck 2.x + MISRA addon（オプション、CLI のみ） |
| ライセンス | MIT / Apache 2.0 |

### 1.5 用語集

| 用語 | 定義 |
|------|------|
| 層（Layer） | タブ名で識別されるステートマシン群（`sm.layer_name`） |
| セル（Cell） | (状態, イベント) の組。遷移関数の最小単位 |
| セル関数 | 1つのセルを処理する `static` C 関数 |
| セルアクション | v2.2：セルに付属する遷移非依存の `ActionStep` |
| セル関係 | v2.2：セル内遷移間の `TransitionRelation` |
| ロール関数 | 遷移・条件・ISR から呼ばれる C 関数 |
| 名前空間（namespace） | ロール関数の所属層または明示的名前空間 |
| qualified_name | `namespace.name` 形式の一意名（例：`Driver.Init`） |
| call_sites | 各ロール関数の呼び出しセル一覧 |
| transition_id | call_sites 内のインデックス。`0xFFFF` = 一致なし |
| スーパー include | `statable_all.h`。全生成ヘッダを集約 |
| スーパーループ | `{project}_run.c`。全層のメインループ |
| マーカー | ユーザコード保持用コメント（`[[STABLE_...]]`） |
| Commit | v2.2：`early_return=True`（同セル内の後続遷移評価を停止） |
| Tentative | v2.2：`early_return=False`（後続遷移が上書き可能） |
| MISRA 抑制 | MISRA C:2012 からの文書化された意図的逸脱 |

---

## 2. クイックスタート

### 2.1 最小例

```python
from statable import StateMachine, State, Event, Transition, GlobalDefinitions
from codegen.c_code_generator import CCodeGenerator
from codegen.config import CodeGenerationConfig

# 1. StateMachine を構築
sm = StateMachine()
sm.layer_name = "Application"
sm.layer_priority = 5

sm.add_state(State(name="Idle", entry=["Driver.IdleEntry"]))
sm.add_state(State(name="Running"))
sm.add_event(Event(name="START"))
sm.set_initial("Idle")

sm.add_transition(Transition(
    source="Idle", event="START", target="Running",
    condition="mode == MODE_AUTO", early_return=True, label="T1",
))

# 2. GlobalDefinitions を構築
gd = GlobalDefinitions()

# 3. コード生成を設定
config = CodeGenerationConfig(
    project_name="Demo",
    folder_structure="by_type",
    output_directory="./output",
)
gen = CCodeGenerator(config=config)

# 4. 全層を生成
files = gen.generate_all_layers(
    layers=[("Application", sm)],
    global_defs=gd,
)

# 5. マーカー方式マージで保存
saved = gen.save_generated_code_with_merge(files, "./output")
print(f"{len(saved)} files saved")
```

### 2.2 多層の例

```python
layers = [
    ("Application", sm_app),
    ("Driver", sm_driver),
    ("Middleware", sm_mw),
]
files = gen.generate_all_layers(layers, gd)
# 層は layer_priority の昇順で内部ソートされる
```

### 2.3 検証付きの例

```python
from codegen.validate.validator import CodeGenerationValidator

validator = CodeGenerationValidator()
result = validator.validate(sm, gd)

if not result.passed:
    for issue in result.get_errors():
        print(f"[{issue.category}] {issue.code}: {issue.message}")
```

### 2.4 XML ラウンドトリップ

```python
from statable.xml_io import project_to_xml, project_from_xml

project_to_xml(
    tabs=[("Application", sm)],
    global_defs=gd,
    filepath="project.xml",
    project_settings={"project_name": "Demo"},
)

tabs, gd2, role_lib, cond_lib, lit_lib, settings = project_from_xml("project.xml")
```

### 2.5 GUI 統合

```python
from statable_gui.code_generation_dialog import CodeGenerationDialog

dialog = CodeGenerationDialog(
    state_machine=sm,
    global_defs=gd,
    role_function_library=role_lib,
)
dialog.all_layers = [("Application", sm)]
dialog.exec()
files = dialog.get_generated_files()
```

**注意**：GUI モジュールは PySide6 が必要。コア SDK（§3、§4、§5、§6、§7）は PySide6 非依存。

---

## 3. データモデル（コアAPI）

### 3.1 列挙型

#### 3.1.1 `StateType`

```python
from statable import StateType

class StateType(Enum):
    NORMAL     = "normal"
    CONCURRENT = "concurrent"
    REGION     = "region"
    INITIAL    = "initial"
    FINAL      = "final"
    CHOICE     = "choice"
    JUNCTION   = "junction"
```

| メンバ | 値 | 説明 |
|--------|-----|------|
| `NORMAL` | `"normal"` | 通常状態（デフォルト） |
| `CONCURRENT` | `"concurrent"` | 並行状態 |
| `REGION` | `"region"` | 並行リージョン |
| `INITIAL` | `"initial"` | 初期疑似状態 |
| `FINAL` | `"final"` | 終了状態 |
| `CHOICE` | `"choice"` | 選択疑似状態 |
| `JUNCTION` | `"junction"` | ジャンクション疑似状態 |

#### 3.1.2 `EventKind`

```python
from statable import EventKind

class EventKind(Enum):
    SIGNAL = "signal"
    CALL   = "call"
    TIME   = "time"
    CHANGE = "change"
```

| メンバ | 値 |
|--------|-----|
| `SIGNAL` | `"signal"` |
| `CALL` | `"call"` |
| `TIME` | `"time"` |
| `CHANGE` | `"change"` |

#### 3.1.3 `EventDeliveryType`

```python
from statable import EventDeliveryType

class EventDeliveryType(Enum):
    DIRECT = "direct"
    QUEUE  = "queue"
    DOUBLE = "double"
```

| メンバ | 値 | 説明 |
|--------|-----|------|
| `DIRECT` | `"direct"` | 直接配送（デフォルト） |
| `QUEUE` | `"queue"` | キュー配送 |
| `DOUBLE` | `"double"` | 直接 + キューの両方 |

#### 3.1.4 `EventSourceLayer`

```python
from statable import EventSourceLayer

class EventSourceLayer(Enum):
    DRIVER     = "driver"
    MIDDLEWARE = "middleware"
```

### 3.2 `State`（dataclass）

```python
from statable import State, StateType

@dataclass
class State:
    name: str
    type: StateType = StateType.NORMAL
    parent: Optional[str] = None
    entry: List[str] = field(default_factory=list)
    exit: List[str] = field(default_factory=list)
    do: str = ""
    description: str = ""
```

| フィールド | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `name` | `str` | ○ | – | 状態名（`StateMachine.states` のキー） |
| `type` | `StateType` | – | `NORMAL` | 状態種別 |
| `parent` | `Optional[str]` | – | `None` | 親状態（階層化用） |
| `entry` | `List[str]` | – | `[]` | エントリ時アクション（v2.2で `str` → `List[str]`） |
| `exit` | `List[str]` | – | `[]` | エグジット時アクション（v2.2） |
| `do` | `str` | – | `""` | do アクション |
| `description` | `str` | – | `""` | 説明 |

**`__post_init__` 挙動**：自動正規化
- `None` → `[]`
- `""` → `[]`
- `"func"` → `["func"]`
- `List` → 保持

### 3.3 `Event`（dataclass）

```python
from statable import Event, EventKind, EventDeliveryType, EventSourceLayer

@dataclass
class Event:
    name: str
    id: Optional[int] = None
    kind: EventKind = EventKind.SIGNAL
    params: List[str] = field(default_factory=list)
    priority: int = 0
    description: str = ""
    delivery_type: EventDeliveryType = EventDeliveryType.DIRECT
    source_layer: EventSourceLayer = EventSourceLayer.DRIVER
    data_type: str = ""
    data_name: str = ""
    title: str = ""
```

| フィールド | 型 | 必須 | デフォルト |
|-----------|-----|------|-----------|
| `name` | `str` | ○ | – |
| `id` | `Optional[int]` | – | `None` |
| `kind` | `EventKind` | – | `SIGNAL` |
| `params` | `List[str]` | – | `[]` |
| `priority` | `int` | – | `0` |
| `description` | `str` | – | `""` |
| `delivery_type` | `EventDeliveryType` | – | `DIRECT` |
| `source_layer` | `EventSourceLayer` | – | `DRIVER` |
| `data_type` | `str` | – | `""` |
| `data_name` | `str` | – | `""` |
| `title` | `str` | – | `""` |

**注意**：`name == ""` は完了遷移を表す。

### 3.4 `Transition`（dataclass, kw_only）

```python
from statable import Transition

@dataclass(kw_only=True)
class Transition:
    source: str
    event: str
    condition: str = ""
    pre_actions: List[str] = field(default_factory=list)
    target: str = ""
    has_else: bool = True
    else_target: str = ""
    else_actions: List[str] = field(default_factory=list)
    early_return: bool = False
    label: str = ""
    action: str = ""
    transition_type: str = "external"
    title: str = ""
```

| フィールド | 型 | 必須 | デフォルト | 説明 |
|-----------|-----|------|-----------|------|
| `source` | `str` | ○ | – | 遷移元状態名 |
| `event` | `str` | ○ | – | イベント名（`""` = 完了） |
| `condition` | `str` | – | `""` | C 条件式 |
| `pre_actions` | `List[str]` | – | `[]` | 遷移前アクション |
| `target` | `str` | – | `""` | 遷移先状態 |
| `has_else` | `bool` | – | `True` | else 節の有無 |
| `else_target` | `str` | – | `""` | else 時の遷移先 |
| `else_actions` | `List[str]` | – | `[]` | else 時アクション |
| `early_return` | `bool` | – | `False` | v2.2：True = Commit |
| `label` | `str` | – | `""` | v2.2：セル内ラベル（T1, T2, ...） |
| `action` | `str` | – | `""` | レガシーフィールド（未使用） |
| `transition_type` | `str` | – | `"external"` | 遷移種別 |
| `title` | `str` | – | `""` | 表示名 |

**v1.6 変更**：`kw_only=True`。
**v2.2 追加**：`early_return`、`label`。

### 3.5 `ActionStep`（dataclass, kw_only, v2.2）

```python
from statable import ActionStep

@dataclass(kw_only=True)
class ActionStep:
    role_function: str = ""
    trigger: str = "before_transitions"
    title: str = ""
```

| フィールド | 型 | 必須 | デフォルト |
|-----------|-----|------|-----------|
| `role_function` | `str` | – | `""` |
| `trigger` | `str` | – | `"before_transitions"` |
| `title` | `str` | – | `""` |

**`trigger` の値**：`"before_transitions"` / `"after_transitions"`。

**`__post_init__`**：`title` が空の場合、`role_function`（空の場合は `"(untitled action)"`）で自動設定。

### 3.6 `TransitionRelation`（dataclass, kw_only, v2.2）

```python
from statable import TransitionRelation

@dataclass(kw_only=True)
class TransitionRelation:
    kind: str = "sequential"
    members: List[str] = field(default_factory=list)
    shared_condition: str = ""
    note: str = ""
    children: List["TransitionRelation"] = field(default_factory=list)
```

| フィールド | 型 | 必須 | デフォルト |
|-----------|-----|------|-----------|
| `kind` | `str` | – | `"sequential"` |
| `members` | `List[str]` | – | `[]` |
| `shared_condition` | `str` | – | `""` |
| `note` | `str` | – | `""` |
| `children` | `List[TransitionRelation]` | – | `[]` |

**`kind` の値**：`"sequential"` / `"exclusive"` / `"group"`。

### 3.7 `RoleFunction`（dataclass, kw_only）

```python
from statable import RoleFunction

@dataclass(kw_only=True)
class RoleFunction:
    name: str
    namespace: str = ""
    description: str = ""
    return_type: str = "void"
    arg1_type: str = ""
    arg1_name: str = ""
    arg2_type: str = ""
    arg2_name: str = ""
    title: str = ""
```

| フィールド | 型 | 必須 | デフォルト |
|-----------|-----|------|-----------|
| `name` | `str` | ○ | – |
| `namespace` | `str` | – | `""` |
| `description` | `str` | – | `""` |
| `return_type` | `str` | – | `"void"` |
| `arg1_type` | `str` | – | `""` |
| `arg1_name` | `str` | – | `""` |
| `arg2_type` | `str` | – | `""` |
| `arg2_name` | `str` | – | `""` |
| `title` | `str` | – | `""` |

**プロパティ**

| 名前 | 型 | 説明 |
|------|-----|------|
| `qualified_name` | `str` | `namespace.name` または `name` |

**クラスメソッド**：`from_legacy_name(legacy_name, layer_names=None) -> RoleFunction`

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `legacy_name` | `str` | ○ | 例：`"Driver_Init"` |
| `layer_names` | `Optional[List[str]]` | – | プレフィックス分離用の層名 |

**例**：

```python
rf = RoleFunction.from_legacy_name("Driver_Init", ["Driver", "App"])
# rf.namespace == "Driver", rf.name == "Init"
```

**`__post_init__` 挙動**：`title` が空の場合、`f"Role function: {qualified_name}"` で自動設定される。

**注意**：本クラスは `statable_gui.libcntrl.role_function_library.RoleFunction` とは別クラス（§5.3 および §7.5.2 参照）。

### 3.8 `GlobalDefinitions`

#### 3.8.1 Dataclass 一覧

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

#### 3.8.2 `GlobalDefinitions` クラス

```python
from statable import GlobalDefinitions

class GlobalDefinitions:
    def __init__(self) -> None: ...

    # 属性
    variables: List[SystemVariable]
    flags: List[EventFlag]
    interrupts: List[InterruptHandlerDef]
    placeholders: List[DevicePlaceholderDef]
    timer_base: TimerBaseDef
    extra_timers: List[TimerBaseDef]
    event_queues: List[EventQueueDef]
    custom_types: List[CustomTypeDef]

    # メソッド
    def add_timer_variables(self) -> None: ...
    def variable_groups(self) -> List[str]: ...
    def flag_groups(self) -> List[str]: ...
    def custom_type_names(self) -> List[str]: ...
```

**`add_timer_variables`**：タイマー定義を `variables` に同期。既存変数は `description` / `title` を保持し、`type` / `unit` のみ上書き。

### 3.9 `StateMachine`

```python
from statable import StateMachine

class StateMachine:
    def __init__(self) -> None: ...

    # 属性
    states: Dict[str, State]
    events: Dict[str, Event]
    transitions: List[Transition]
    role_functions: Dict[str, RoleFunction]
    initial_state: Optional[str]
    layer_priority: int
    layer_description: str
    layer_name: str
    cell_actions: Dict[Tuple[str, str], List[ActionStep]]
    cell_relations: Dict[Tuple[str, str], List[TransitionRelation]]
```

#### メソッド

| メソッド | シグネチャ | 例外 |
|---------|-----------|------|
| `add_state` | `(state: State) -> None` | 名前重複時 `ValueError` |
| `add_event` | `(event: Event) -> None` | 名前重複時 `ValueError` |
| `remove_event` | `(name: str) -> None` | – |
| `add_transition` | `(trans: Transition) -> None` | source/target/event 未定義時 `ValueError` |
| `remove_transition` | `(trans: Transition) -> None` | – |
| `set_initial` | `(state_name: str) -> None` | 未定義時 `ValueError` |
| `add_role_function` | `(rf: RoleFunction) -> None` | `rf.name` 重複時 `ValueError` |
| `remove_role_function` | `(name: str) -> None` | – |
| `get_transitions_for_cell` | `(source: str, event: str) -> List[Transition]` | – |
| `get_transitions_for_event` | `(event: str) -> List[Transition]` | – |
| `get_actions_for_cell` | `(source: str, event: str) -> List[ActionStep]` | – |
| `set_actions_for_cell` | `(source: str, event: str, actions: List[ActionStep]) -> None` | – |
| `get_relations_for_cell` | `(source: str, event: str) -> List[TransitionRelation]` | – |
| `set_relations_for_cell` | `(source: str, event: str, relations: List[TransitionRelation]) -> None` | – |
| `get_cell_keys` | `() -> List[Tuple[str, str]]` | – |
| `remove_cell_metadata` | `(source: str, event: str) -> None` | – |

**重要**：`add_role_function` は `rf.name`（純粋名）でキー管理。`Driver.Init` と `App.Init` は衝突する。§9 L-24 参照。

---

## 4. コード生成API

### 4.1 `CCodeGenerator`

モジュールバージョン：**v2.2.9**。

```python
from codegen.c_code_generator import CCodeGenerator

class CCodeGenerator:
    def __init__(self, config: Optional[CodeGenerationConfig] = None) -> None: ...
```

#### クラス定数

| 定数 | 型 | 説明 |
|------|-----|------|
| `FILE_STEPS` | `Dict[str, List[Dict]]` | ファイル別ステップテーブル |
| `STRUCT_KIND_DISPATCH` | `Dict[str, str]` | 構造体種別 → 生成メソッド |
| `FILE_DISPATCH` | `Dict[str, str]` | ファイル → 生成メソッド |
| `FILE_CATEGORY` | `Dict[str, str]` | ファイル → カテゴリ（`include` / `src` / `common`） |
| `FOLDER_STRUCTURE_RESOLVERS` | `Dict[str, str]` | 構成 → パス解決 |
| `LAYER_SPECIFIC_FILES` | `Set[str]` | 5ファイル（層別サフィックス） |
| `COMMON_FILES` | `Set[str]` | 8ファイル（共有） |

**`LAYER_SPECIFIC_FILES`**：`statable_types.h`、`statable_transitions.h`、`statable_transitions.c`、`statable_role_functions.h`、`statable_role_functions.c`。

#### 公開メソッド

| メソッド | シグネチャ |
|---------|-----------|
| `get_config` | `() -> CodeGenerationConfig` |
| `set_config` | `(config: CodeGenerationConfig) -> None` |
| `update_config` | `(**kwargs) -> None` |
| `reset_config` | `() -> None` |
| `generate_all` | `(state_machine, global_defs, role_function_library=None) -> Dict[str, str]` |
| `generate_file` | `(filename, state_machine, global_defs, role_function_library=None) -> str` |
| `generate_all_layers` | `(layers, global_defs, role_function_library=None) -> Dict[str, str]` |
| `save_generated_code` | `(generated_files: Dict[str, str], output_dir: str, layer_name: str = '') -> List[str]` |
| `save_generated_code_with_merge` | `(generated_files, output_dir, layer_name='') -> List[str]` |
| `get_merge_summary` | `(generated_files, output_dir, layer_name='') -> Dict[str, Dict[str, int]]` |
| `get_generated_file_list` | `() -> List[str]` |

**例外**

| 例外 | 条件 |
|------|------|
| `ValueError` | `generate_file` に未知のファイル名 |
| `OSError` | `save_generated_code` の書込み失敗 |

### 4.2 `CodeGenerationConfig`

```python
from codegen.config import CodeGenerationConfig

@dataclass
class CodeGenerationConfig:
    generation_style: str = "table_driven"
    table_type: str = "array"
    os_type: str = "non_rtos"
    naming_prefix: str = ""
    state_prefix: str = "STATE"
    event_prefix: str = "EVENT"
    flag_prefix: str = "FLAG"
    enable_debug_logs: bool = True
    enable_info_logs: bool = True
    enable_error_logs: bool = True
    enable_comments: bool = True
    enable_doxygen: bool = True
    enable_user_markers: bool = True
    output_directory: str = ""
    save_with_merge: bool = True
    project_name: str = "MyProject"
    folder_structure: str = "by_type"
    include_dir_name: str = "include"
    source_dir_name: str = "src"
    common_dir_name: str = "common"
    project_dir_name: str = "project"
    generate_super_include: bool = True
    super_include_file: str = "statable_all.h"
    super_include_dir: str = "common"
    external_includes: List[str] = field(default_factory=list)
    external_includes_in_super: bool = True
    external_includes_in_role: bool = True
    external_includes_in_transitions: bool = False
    external_includes_in_common: bool = False
    max_consecutive_pending_events: int = 16
```

**メソッド**

| メソッド | 説明 |
|---------|------|
| `to_dict() -> Dict` | シリアライズ |
| `from_dict(data: Dict) -> CodeGenerationConfig` | デシリアライズ（未知キーは無視） |

### 4.3 `ConfigManager`

```python
from codegen.config import ConfigManager

class ConfigManager:
    def __init__(self) -> None: ...
    def get_config(self) -> CodeGenerationConfig: ...
    def set_config(self, config: CodeGenerationConfig) -> None: ...
    def update(self, **kwargs) -> None: ...
    def reset(self) -> None: ...
    def get_available_styles(self) -> Dict[str, str]: ...
    def get_available_table_types(self) -> Dict[str, str]: ...
    def get_available_os_types(self) -> Dict[str, str]: ...
    def get_available_folder_structures(self) -> Dict[str, str]: ...
```

### 4.4 出力ファイル（14）

| # | ファイル | カテゴリ | 層別 |
|---|---------|---------|------|
| 1 | `statable_types_common.h` | include | – |
| 2 | `statable_types.h` | include | ○ |
| 3 | `statable_transitions.h` | include | ○ |
| 4 | `statable_transitions.c` | src | ○ |
| 5 | `statable_role_functions.h` | include | ○ |
| 6 | `statable_role_functions.c` | src | ○ |
| 7 | `statable_init.c` | src | – |
| 8 | `statable_event_queue.c` | src | – |
| 9 | `statable_interrupt.c` | src | – |
| 10 | `statable_timer.c` | src | – |
| 11 | `osal.h` | common | – |
| 12 | `osal.c` | common | – |
| 13 | `statable_all.h` | common | – |
| 14 | `{project_name}_run.c` | src | – |

### 4.5 フォルダ構成

| 構成 | レイアウト |
|------|-----------|
| `flat` | 全ファイルを1ディレクトリに配置 |
| `by_type` | `include/` / `src/` / `common/` |
| `by_layer` | `<layer_name>/` 層別 + ルート直下に common |

### 4.6 `CodeTemplates`

テンプレート辞書クラス（サブクラス化でカスタマイズ）。

| 辞書 | 型 | 用途 |
|------|-----|------|
| `STRINGS` | `Dict[str, str]` | 基本文字列（セクション行、ログマクロ） |
| `SECTION_HEADERS` | `Dict[str, str]` | 25種のセクションヘッダ名 |
| `STRUCT_COMMENTS` | `Dict[str, Dict]` | 構造体コメント |
| `ENUM_COMMENTS` | `Dict[str, Dict]` | Enum コメント |
| `TYPE_NAMES` | `Dict[str, str]` | 型名（`STATE_t`, `EVENT_t`, `FLAG_t`） |
| `FUNCTION_NAMES` | `Dict[str, str]` | 関数名プレフィックス |
| `MACRO_NAMES` | `Dict[str, str]` | マクロ名 |
| `FORMATS` | `Dict[str, str]` | フォーマット文字列 |
| `LAYER_TEMPLATES` | `Dict[str, str]` | 層別ファイル用 |
| `COMMON_TYPES_TEMPLATES` | `Dict[str, str]` | `SystemContext_t` 等 |
| `ISR_TEMPLATES` | `Dict[str, str]` | ISR 用 |
| `DEBUG_MESSAGES` | `Dict[str, str]` | ログメッセージテンプレート |
| `OSAL` | `Dict` | OSAL テンプレート（os_types, header, source） |
| `SUPER_INCLUDE_TEMPLATES` | `Dict[str, str]` | `statable_all.h` |
| `SUPER_LOOP_TEMPLATES` | `Dict[str, str]` | スーパーループ |

### 4.7 `RoleFunctionGenerator`

内部サブジェネレータ。モジュールバージョン：**v3.3**。

| メソッド | シグネチャ |
|---------|-----------|
| `set_layer` | `(layer_name: str) -> None` |
| `generate_none_define` | `() -> str` |
| `generate_entry_struct` | `() -> str` |
| `generate_transition_id_prototype` | `() -> str` |
| `generate_transition_id_function` | `() -> str` |
| `generate_call_sites_table` | `(func, call_sites) -> str` |
| `generate_tail_user_section` | `() -> str` |
| `generate_declaration` | `(func) -> str` |
| `generate_implementation` | `(func, global_defs=None, call_sites=None, include_transition_id=True) -> str` |
| `generate_call` | `(func_name: str) -> str` |
| `generate_all_declarations` | `(role_functions: List) -> str` |
| `generate_all_implementations` | `(role_functions, state_machine=None, global_defs=None) -> str` |

### 4.8 `TransitionGenerator`

内部サブジェネレータ。モジュールバージョン：**v2.6**。

| メソッド | シグネチャ |
|---------|-----------|
| `set_layer` | `(layer_name: str) -> None` |
| `generate_transition_cell_functions` | `(state_machine) -> str` |
| `generate_transition_cell_prototypes` | `(state_machine) -> str` |
| `generate_transition_table` | `(state_machine, table_type=None) -> str` |
| `generate_transition_table_header` | `(state_machine) -> str` |
| `generate_function_dictionary` | `(state_machine) -> str` |
| `generate_process_function` | `(state_machine, generation_style=None) -> str` |
| `generate_get_next_event_function` | `(state_machine) -> str` |
| `generate_all` | `(state_machine) -> Dict[str, str]` |
| `generate_all_transitions` | `(state_machine, table_type='array', process_type='table_driven') -> str` |

**ロール関数呼び出しの2形式（MISRA 17.7）**：

| 形式 | 用途 | 出力 |
|------|------|------|
| 条件 | `Transition.condition`、`Relation.shared_condition` | `RoleFunc_X(transition, ctx)` |
| アクション | `pre_actions`、`else_actions`、セルアクション、entry/exit | `(void)RoleFunc_X(transition, ctx)` |

### 4.9 内部サブジェネレータ（SDK非公開）

以下の7クラスは `CCodeGenerator` 内部で使用される。SDK利用者は**直接呼び出さない**こと。

| クラス | モジュール | 用途 |
|--------|-----------|------|
| `CStructGenerator` | `struct_generator.py` | 構造体生成（v2.2.1） |
| `CEnumGenerator` | `enum_generator.py` | Enum 生成（v1.5） |
| `VariableGenerator` | `variable_generator.py` | 変数マクロ + `SystemContext_Init`（v2.0） |
| `EventQueueGenerator` | `event_queue_generator.py` | イベントキュー |
| `InterruptGenerator` | `interrupt_generator.py` | ISR 生成（H3） |
| `TimerGenerator` | `timer_generator.py` | タイマー構造体 / Init / Update（v2.2） |
| `OSALGenerator` | `osal_generator.py` | OSAL ヘッダ / ソース（v2.2） |

### 4.10 補助API

#### 4.10.1 `CTypeMapper`

全メソッドが classmethod。

```python
from codegen.type_mapper import CTypeMapper

CTypeMapper.map_type("uint32")           # -> "uint32_t"
CTypeMapper.get_type_category("uint32")  # -> "integer"
CTypeMapper.get_required_headers(["uint32", "bool"])
# -> ["#include <stdbool.h>", "#include <stdint.h>"]
```

#### 4.10.2 `CNamingConvention`

全メソッドが classmethod。モジュールバージョン：**v2.2.5**。

| メソッド | 説明 |
|---------|------|
| `to_snake_case(name, upper=False)` | – |
| `to_upper_snake(name)` | `"myEvent"` → `"MY_EVENT"` |
| `to_lower_snake(name)` | `"MyEvent"` → `"my_event"` |
| `to_camel_case(name)` | `"my_event"` → `"myEvent"` |
| `to_pascal_case(name)` | `"my_event"` → `"MyEvent"` |
| `sanitize_identifier(name)` | C 予約語のエスケープ、記号の置換 |
| `create_type_name(name)` | 冪等な `_t` サフィックス |
| `create_enum_value(prefix, name)` | – |
| `create_function_name(module, action)` | – |
| `create_variable_name(name)` | – |
| `create_macro_name(name)` | – |

**`create_type_name` の冪等性**：
```
create_type_name("SystemStatus")     # -> "SystemStatus_t"
create_type_name("SystemStatus_t")   # -> "SystemStatus_t"
create_type_name("sensor_data")      # -> "SensorData_t"
create_type_name("")                 # -> "Unknown_t"
```

#### 4.10.3 `CodeMerger`

マーカー方式マージ。モジュールバージョン：**v2.0**。

| カテゴリ | メソッド |
|---------|---------|
| 抽出 | `extract_file_user_code`、`extract_func_user_code`、`extract_all_func_user_codes`、`extract_file_tail_user_code` |
| 注入 | `inject_file_user_code`、`inject_func_user_code`、`inject_file_tail_user_code` |
| マージ | `merge_file`、`merge_all_files` |
| 照会 | `has_user_code`、`has_func_user_code`、`get_user_code_summary` |

マーカー仕様は §7.4 参照。

---

## 5. 検証API

### 5.1 `CodeGenerationValidator`

```python
from codegen.validate.validator import CodeGenerationValidator

class CodeGenerationValidator:
    VALIDATORS: Dict[str, Type] = {...}  # 11エントリ

    def __init__(self) -> None: ...
    def validate(self, state_machine, global_defs) -> ValidationResult: ...
    def validate_category(self, category, state_machine, global_defs) -> List[ValidationIssue]: ...
    def get_categories(self) -> List[str]: ...
```

**登録バリデータ（11）**

| カテゴリ | クラス |
|---------|--------|
| `state` | `StateValidator` |
| `event` | `EventValidator` |
| `transition` | `TransitionValidator` |
| `role_function` | `RoleFunctionValidator` |
| `variable` | `VariableValidator` |
| `flag` | `FlagValidator` |
| `queue` | `QueueValidator` |
| `interrupt` | `InterruptValidator` |
| `timer` | `TimerValidator` |
| `custom_type` | `CustomTypeValidator` |
| `cell` | `CellValidator`（v2.2） |

**挙動**：各バリデータは挿入順に実行される。カテゴリ単位の例外は捕捉され `logger.error` で記録され、処理は継続する。

### 5.2 データモデル

#### 5.2.1 `ValidationSeverity`

```python
class ValidationSeverity(Enum):
    ERROR   = "error"
    WARNING = "warning"
    INFO    = "info"

    @classmethod
    def from_string(cls, value: str) -> 'ValidationSeverity'
```

**`from_string`**：大文字小文字を吸収。未知値 → `INFO`。

#### 5.2.2 `ValidationIssue`

| フィールド | 型 | 必須 | デフォルト |
|-----------|-----|------|-----------|
| `category` | `str` | ○ | – |
| `code` | `str` | ○ | – |
| `message` | `str` | ○ | – |
| `severity` | `ValidationSeverity` | ○ | – |
| `target` | `str` | – | `""` |
| `suggestion` | `str` | – | `""` |
| `details` | `Dict[str, Any]` | – | `{}` |

**メソッド**：`to_dict`、`from_dict`、`__str__`。

#### 5.2.3 `ValidationResult`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `issues` | `List[ValidationIssue]` | 全課題 |

**プロパティ**：`passed`（`error_count == 0` で True）、`error_count`、`warning_count`、`info_count`。

**メソッド**：`get_errors`、`get_warnings`、`get_infos`、`get_by_category`、`to_dict`、`from_dict`。

**注意**：`passed` に影響するのは `ERROR` のみ。Warning と Info は影響しない。

#### 5.2.4 `ValidationContext`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `state_machine` | `Any` | 対象 `StateMachine` または `None` |
| `global_defs` | `Any` | 対象 `GlobalDefinitions` または `None` |

**プロキシプロパティ**（`None` の場合は空を返す）：

- SM 経由：`states`、`events`、`transitions`、`role_functions`、`initial_state`
- GD 経由：`variables`、`flags`、`event_queues`、`interrupts`、`custom_types`、`timer_base`、`extra_timers`

**注意**：`cell_actions` / `cell_relations` のプロキシは未実装。`CellValidator` は `state_machine` に直接アクセスする。

### 5.3 `BaseValidator`

```python
from codegen.validate.items.base_validator import BaseValidator

class BaseValidator:
    category: str = ""
    rules: Dict[str, Callable] = {}

    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        ...
```

**サブクラス規約**：

```python
class MyValidator(BaseValidator):
    category = "my_category"
    rules = {
        "MY_CODE_1": _check_1,
        "MY_CODE_2": _check_2,
    }
```

**コードベースで観察された2つの実装パターン**：

- **パターンA（10バリデータ）**：`validate()` をオーバーライドしてルール単位の `try/except` を実装。`_create_issue(code, **kwargs)` で `VALIDATION_RULES` から `message` / `severity` / `suggestion` を取得。
- **パターンB（1バリデータ：`CellValidator`）**：`validate()` をオーバーライド**しない**。`_make_issue(code, message, target)` を使用し、メッセージをハードコード。`suggestion` は設定されない。§9 L-21 参照。

### 5.4 個別バリデータ（35ルール）

| カテゴリ | ルール |
|---------|--------|
| `state` | `STATE_NO_INITIAL`、`STATE_UNREACHABLE`、`STATE_NO_TRANSITION`、`STATE_DUPLICATE` |
| `event` | `EVENT_UNUSED`、`EVENT_NO_TRANSITION` |
| `transition` | `TRANSITION_TARGET_UNDEFINED`、`TRANSITION_EVENT_UNDEFINED`、`TRANSITION_SOURCE_UNDEFINED`、`TRANSITION_DUPLICATE`、`TRANSITION_SELF_LOOP` |
| `role_function` | `ROLE_FUNC_NO_RETURN_TYPE`、`ROLE_FUNC_ARG_MISMATCH`、`ROLE_FUNC_UNUSED` |
| `variable` | `VAR_DUPLICATE_NAME`、`VAR_INVALID_TYPE`、`VAR_INVALID_ARRAY_SIZE` |
| `flag` | `FLAG_DUPLICATE_NAME`、`FLAG_INVALID_RANGE` |
| `queue` | `QUEUE_INVALID_SIZE`、`QUEUE_UNDEFINED_EVENT` |
| `interrupt` | `INTERRUPT_DUPLICATE_NAME`、`INTERRUPT_UNDEFINED_EVENT` |
| `timer` | `TIMER_DUPLICATE_VARIABLE`、`TIMER_INVALID_MULTIPLIER` |
| `custom_type` | `TYPE_DUPLICATE_NAME`、`TYPE_NO_MEMBERS` |
| `cell` | `CELL_EMPTY_CONDITION`、`CELL_DUPLICATE_LABEL`、`CELL_DANGLING_RELATION`、`CELL_UNREACHABLE_TRANSITION`、`CELL_OVERLAP_POSSIBLE`、`CELL_DUPLICATE_TARGET`、`CELL_EXCLUSIVE_NO_RETURN`、`CELL_EMPTY_TARGET` |

**`ROLE_FUNC_UNUSED` に関する注意**：実装は `Transition.action` と `Transition.condition` のみをチェックする（文字列完全一致）。v2.2 では `pre_actions` / `else_actions` / セルアクションは**考慮されない**ため、v2.2 のアクションフィールドのみを使用している場合に偽陽性が発生する可能性がある。§9 L-23 参照。

### 5.5 重大度分布

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

### 5.6 AI 診断

#### 5.6.1 `AIPromptGenerator`

```python
from codegen.validate.prompt_generator import AIPromptGenerator

class AIPromptGenerator:
    def __init__(self) -> None: ...
    def generate_diagnosis_prompt(self, sm, gd, validation_result=None) -> str: ...
```

#### 5.6.2 `AIResponseParser`

```python
from codegen.validate.response_parser import AIResponseParser

class AIResponseParser:
    ACTION_MAPPING: Dict[str, ChangeActionType]  # legacy 10アクションのみ

    def parse(self, text: str) -> List[ChangeRequest]: ...
    def parse_json_response(self, text: str) -> List[ChangeRequest]: ...
    def parse_text_response(self, text: str) -> List[ChangeRequest]: ...
```

**制限**：v2.2 セル単位アクションは**解析されない**。§9 L-18 参照。

### 5.7 変更適用

#### 5.7.1 `ChangeActionType`（17種）

**レガシー（10）**：`SET_INITIAL`、`ADD_TRANSITION`、`ADD_STATE`、`ADD_EVENT`、`REMOVE_TRANSITION`、`UPDATE_TRANSITION`、`ADD_ROLE_FUNCTION`、`REMOVE_ROLE_FUNCTION`、`ADD_VARIABLE`、`ADD_FLAG`。

**v2.2 セル単位（7）**：`ADD_CELL`、`REMOVE_CELL`、`ADD_ACTION_STEP`、`REMOVE_ACTION_STEP`、`ADD_TRANSITION_RELATION`、`REMOVE_TRANSITION_RELATION`、`SET_EARLY_RETURN`。

#### 5.7.2 `ChangeRequest`

| フィールド | 型 | デフォルト |
|-----------|-----|-----------|
| `action` | `ChangeActionType` | – |
| `params` | `Dict[str, Any]` | `{}` |
| `reason` | `str` | `""` |
| `source` | `str` | `"ai"` |

#### 5.7.3 `ChangeApplier`

```python
from codegen.validate.change_applier import ChangeApplier

class ChangeApplier:
    def __init__(self, sm, gd) -> None: ...
    def apply(self, change: ChangeRequest) -> Tuple[bool, str]: ...
    def apply_all(self, changes: List[ChangeRequest]) -> Dict: ...
```

**`apply_all` の戻り値**：

```python
{
    'total': int,
    'applied': int,
    'failed': int,
    'results': List[{'change': ChangeRequest, 'success': bool, 'message': str}],
}
```

**制限**：`_add_variable` と `_add_flag` は重複チェックを行わない。§9 L-19 参照。

---

## 6. MISRA連携API

### 6.1 概要

MISRA チェックは、**`cppcheck` + MISRA addon** を外部プロセスとして呼び出すことで実行される。StaTable は cppcheck とリンクしない。

| 項目 | 値 |
|------|-----|
| チェッカー | `cppcheck` 2.x + `--addon=misra` |
| 出力形式 | XML（`--xml --xml-version=2`） |
| 実行方式 | CLI ツール（Python 3.12） |
| ビルド失敗 | しない（情報提供のみ） |
| 前提条件 | `cppcheck` が `PATH` にあること |

**重要**：`cppcheck + MISRA addon` は**公認の MISRA チェッカーではない**。StaTable は「対応」「評価」という表現を使用し、「準拠」とは主張しない。

### 6.2 CLIツール1：`tools/run_misra_check.py`

```bash
python tools/run_misra_check.py --root <DIR> --out <DIR> [--suppressions <FILE>]
```

**引数**

| 引数 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `--root` | `str` | ○ | – | 生成 `.c` ファイルのルートディレクトリ |
| `--out` | `str` | ○ | – | 出力ディレクトリ |
| `--suppressions` | `str` | – | `misra/suppressions.txt` | 抑制リスト |

**出力**

| ファイル | 内容 |
|---------|------|
| `summary.md` | MISRA ルール別件数 + 非 MISRA 警告 + Next Steps |
| `cppcheck_raw.xml` | cppcheck stdout（XML） |
| `cppcheck_stderr.txt` | cppcheck stderr（XML を含む場合あり） |

**終了コード**

| コード | 条件 |
|--------|------|
| 0 | 正常終了（違反があっても0） |
| 1 | ルート不在 / cppcheck 不在 / タイムアウト |

### 6.3 CLIツール2：`tools/analyze_misra_impact.py`

```bash
python tools/analyze_misra_impact.py --xml <FILE> --out <FILE> [--csv <FILE>]
```

**出力**

| ファイル | 内容 |
|---------|------|
| `<out>` | 影響分析 Markdown |
| `<csv>` | `codegen_source,rule_id,count` の CSV |

**マッピング規則**（生成ファイル → 責任 codegen ソース）：

| 生成ファイルパターン | 責任 codegen |
|-------------------|-------------|
| `statable_role_functions` | `role_function_generator.py`、`code_templates.py` |
| `statable_transitions` | `transition_generator.py`、`code_templates.py` |
| `statable_types` | `struct_generator.py`、`enum_generator.py`、`variable_generator.py`、`code_templates.py` |
| `statable_init` | `variable_generator.py`、`c_code_generator.py` |
| `statable_event_queue` | `event_queue_generator.py` |
| `statable_interrupt` | `interrupt_generator.py` |
| `statable_timer` | `timer_generator.py` |
| `osal` | `osal_generator.py`、`code_templates.py` |
| `statable_all` | `c_code_generator.py` |
| `_run.c` | `c_code_generator.py` |

### 6.4 抑制リスト

ファイル：`misra/suppressions.txt`。1行1ルールID。

現在のリスト（11ルール）：

```
misra-c2012-2.3
misra-c2012-2.4
misra-c2012-2.5
misra-c2012-5.9
misra-c2012-8.4
misra-c2012-8.7
misra-c2012-8.9
misra-c2012-11.5
misra-c2012-15.5
misra-c2012-15.7
misra-c2012-18.4
```

**抑制理由**（全11ルール）：

| ルール | 理由 |
|-------|------|
| `2.3` | 未使用型宣言（予約型） |
| `2.4` | 未使用タグ（構造体タグ） |
| `2.5` | 未使用マクロ（将来用に予約） |
| `5.9` | 内部リンケージ識別子の重複（層別ファイル） |
| `8.4` | 層別 extern 可視性。層間協調を維持する設計判断 |
| `8.7` | 外部リンケージ関数の参照（層間協調） |
| `8.9` | 単一翻訳単位でのオブジェクト定義（設計判断） |
| `11.5` | ベアメタル OSAL が `memcpy` 回避のため `void *` + `uint8_t *` キャストを使用 |
| `15.5` | 単一 exit point を使用しない（可読性優先） |
| `15.7` | `_handled` パターン：各 `if` は独立ガード |
| `18.4` | OSAL キューのポインタ演算（`11.5` と同様） |

### 6.5 現行ベースライン（v2.6.1）

| 指標 | 値 |
|------|----:|
| MISRA ヒット数 | 10 |
| 異なる MISRA ルール数 | 4 |
| 非 MISRA 警告数 | 9 |

**MISRA ヒット（全て設計上抑制）**：

| ルール | 件数 |
|-------|-----:|
| `8.4` | 3 |
| `11.5` | 4 |
| `18.4` | 2 |
| `15.7` | 1 |

### 6.6 ベースラインファイル

`misra/baseline.md` に記録される項目：
- 記録日
- StaTable バージョン
- 対象 XML
- MISRA ヒット数 / 異なるルール数
- 頻出ルール
- アクション項目

**現状**：テンプレートのみ（実測値未記録）。§9 L-13 参照。

---

## 7. ユーティリティAPI

### 7.1 `XmlIO`（関数群）

モジュール：`statable/xml_io.py`。**関数ベース**（クラスなし）。

| 関数 | シグネチャ |
|------|-----------|
| `project_to_xml` | `(tabs, global_defs, filepath, role_function_library=None, condition_library=None, literal_library=None, project_settings=None) -> None` |
| `project_from_xml` | `(filepath) -> Tuple[List[Tuple[str, StateMachine]], GlobalDefinitions, Optional[RoleFunctionLibrary], Optional[ConditionLibrary], Optional[LiteralLibrary], dict]` |
| `state_machine_to_element` | `(sm: StateMachine) -> ET.Element` |
| `state_machine_from_element` | `(elem: ET.Element) -> StateMachine` |
| `global_defs_to_element` | `(gd: GlobalDefinitions) -> ET.Element` |
| `global_defs_from_element` | `(elem: ET.Element) -> GlobalDefinitions` |
| `role_function_library_to_element` | `(lib) -> Optional[ET.Element]` |
| `role_function_library_from_element` | `(elem) -> Optional[RoleFunctionLibrary]` |
| `condition_library_to_element` | `(lib) -> Optional[ET.Element]` |
| `condition_library_from_element` | `(elem) -> Optional[ConditionLibrary]` |
| `literal_library_to_element` | `(lib) -> Optional[ET.Element]` |
| `literal_library_from_element` | `(elem) -> Optional[LiteralLibrary]` |

**`project_settings` のキー**：

| キー | 型 | デフォルト |
|------|-----|-----------|
| `project_name` | `str` | `"MyProject"` |
| `table_type` | `str` | `"array"` |
| `generation_style` | `str` | `"table_driven"` |
| `os_type` | `str` | `"non_rtos"` |
| `folder_structure` | `str` | `"by_type"` |
| `include_dir_name` | `str` | `"include"` |
| `source_dir_name` | `str` | `"src"` |
| `common_dir_name` | `str` | `"common"` |
| `project_dir_name` | `str` | `"project"` |
| `generate_super_include` | `bool` | `True` |
| `super_include_file` | `str` | `"statable_all.h"` |
| `external_includes` | `List[str]` | `[]` |
| `external_includes_in_super` | `bool` | `True` |
| `external_includes_in_role` | `bool` | `True` |
| `external_includes_in_transitions` | `bool` | `False` |
| `external_includes_in_common` | `bool` | `False` |
| `max_consecutive_pending_events` | `int` | `16` |

**注意**：`super_include_dir` は**永続化されない**。§9 L-05 参照。

**XML スキーマ**：XML 構造全体（`<Project>`、`<StateMachine>`、`<Cells>` 等）については、`SPEC_OVERVIEW_ja.md` §3.5.2 を参照。本セクションは Python API の表層のみを記述する。

### 7.2 `MermaidGenerator`（関数）

モジュール：`statable/mermaid_gen.py`。

```python
from statable.mermaid_gen import generate_mermaid

mermaid: str = generate_mermaid(sm)
```

**出力形式**：

```
stateDiagram-v2
    direction LR
    [*] --> InitialState
    Source --> Target : Title (Event) [Condition] [Commit]
    Source --> ElseTarget : (Event) else [Commit]
    note right of State : internal: Title (Event)
```

**ラベル規則**：

| 要素 | 条件 | 出力 |
|------|------|------|
| Title | `title` が `"(untitled transition)"` 以外 | `Startup` |
| Target | `title` 空 | `Active` |
| `(internal)` | 両方空 | `(internal)` |
| `(Event)` | `event` 非空 | `(START)` |
| `[Condition]` | `condition` 非空（50文字に切詰め） | `[err_code != 0]` |
| ` [Commit]` | `early_return == True` | – |

**サニタイズ**：`:` → `-`、`[` → `(`、`]` → `)`、`"` → `'`、バッククォート → `'`、改行 → スペース。

### 7.3 `SampleData`（関数群）

モジュール：`statable/sample_data.py`。

| 関数 | 説明 |
|------|------|
| `create_sample_state_machine() -> StateMachine` | 4状態、5イベント、6遷移、9ロール関数、4セルアクション、2セル関係 |
| `create_sample_global_defs() -> GlobalDefinitions` | 4変数、2フラグ、2型、1割り込み、2タイマーグループ、1キュー |

### 7.4 マーカー方式マージ仕様

モジュール：`codegen/code_merger.py`（`CodeMerger` クラス）。

#### 7.4.1 マーカー種別（4）

| # | マーカー | 用途 | 配置 |
|---|---------|------|------|
| 1 | `[[STABLE_USER_CODE_START]]` / `END` | ファイル先頭ユーザ領域 | include 直後 |
| 2 | `[[STABLE_USER_CODE_START:<name>]]` / `END:<name>` | 関数内ユーザ領域 | 各ロール関数 / ISR 内 |
| 3 | `[[STABLE_USER_CODE_TAIL_START]]` / `END` | ファイル末尾ユーザ領域 | ファイル末尾 |
| 4 | `[[STABLE_AUTO_GENERATED_START]]` / `END` | 自動生成領域（予約） | – |

#### 7.4.2 関数内マーカーの命名

| 関数 | マーカー名 |
|------|-----------|
| `RoleFunc_<NS>_<Name>` | `<NS>_<Name>` |
| `RoleFunc_<Name>`（NS なし） | `<Name>` |
| `ISR_<Name>` | `<Name>`（層なし） |

**抽出パターン**：

```python
FUNC_NAME_PATTERNS = [
    r'RoleFunc_(\w+)\s*\(',
    r'ISR_(\w+)\s*\(',
]
```

#### 7.4.3 マージフロー

```
merge_file(generated_content, existing_content)
  ├── existing_content が None/空：generated_content を返す
  ├── 1. ユーザコード抽出
  │   ├── extract_file_user_code()
  │   ├── extract_all_func_user_codes()
  │   └── extract_file_tail_user_code()
  ├── 2. 生成コードへ注入
  │   ├── inject_file_user_code()
  │   ├── inject_func_user_code()（関数ごと）
  │   └── inject_file_tail_user_code()
  └── 3. マージ済みコンテンツを返す
```

**`inject_file_user_code`（v2.0）**：既存ブロックがある場合は**内容のみ置換**（新規挿入しない）。存在しない場合は最後の `#include` の後に挿入。

#### 7.4.4 `merge_all_files`

```python
def merge_all_files(
    self,
    generated_files: Dict[str, str],
    existing_dir: str,
    path_resolver: Optional[Callable] = None,
    layer_name: str = '',
) -> Dict[str, str]
```

`path_resolver(filename, layer_name) -> rel_path` は `CCodeGenerator._resolve_output_path` から渡される。

### 7.5 共有ライブラリ（`statable_gui/libcntrl/`）

**注意**：PySide6 が必要。

#### 7.5.1 `RoleFunctionLibrary`

| メソッド | シグネチャ |
|---------|-----------|
| `_key` | `(rf) -> str`（`rf.qualified_name` を返す） |
| `add` | `(rf: RoleFunction) -> None`（重複時 `ValueError`） |
| `remove` | `(name: str) -> None` |
| `get` | `(name: str) -> Optional[RoleFunction]` |
| `list_all` | `() -> List[RoleFunction]` |
| `to_dict` | `() -> dict` |
| `from_dict` | `(data: dict) -> RoleFunctionLibrary` |

#### 7.5.2 `RoleFunction`（libcntrl 版）

| フィールド | 型 | デフォルト |
|-----------|-----|-----------|
| `name` | `str` | – |
| `namespace` | `str` | `""` |
| `description` | `str` | `""` |
| `title` | `str` | `""` |
| `used_global_vars` | `List[str]` | `[]` |
| `used_events` | `List[str]` | `[]` |
| `used_literals` | `List[str]` | `[]` |

**プロパティ**：`qualified_name`。

**注意**：`statable.RoleFunction` とは別クラス。§9 L-28 参照。

#### 7.5.3 `ConditionLibrary` / `ConditionTemplate`

| メソッド | シグネチャ |
|---------|-----------|
| `add` | `(ct: ConditionTemplate) -> None` |
| `remove` | `(name: str) -> None` |
| `get` | `(name: str) -> Optional[ConditionTemplate]` |
| `list_all` | `() -> List[ConditionTemplate]` |
| `to_dict` / `from_dict` | – |

#### 7.5.4 `LiteralLibrary` / `LiteralDefinition`

`ConditionLibrary` と同じ API パターン。

---

## 8. エラーコード

### 8.1 例外

| # | 例外 | 発生箇所 | 条件 |
|---|------|---------|------|
| 1 | `ValueError` | `StateMachine.add_state` | 状態名重複 |
| 2 | `ValueError` | `StateMachine.add_event` | イベント名重複 |
| 3 | `ValueError` | `StateMachine.add_transition` | source/target/event 未定義 |
| 4 | `ValueError` | `StateMachine.set_initial` | 未定義状態 |
| 5 | `ValueError` | `StateMachine.add_role_function` | `rf.name` 重複 |
| 6 | `ValueError` | `RoleFunctionLibrary.add` | `qualified_name` 重複 |
| 7 | `ValueError` | `ConditionLibrary.add` | `name` 重複 |
| 8 | `ValueError` | `LiteralLibrary.add` | `name` 重複 |
| 9 | `ValueError` | `CCodeGenerator.generate_file` | 未知のファイル名 |
| 10 | `ValueError` | `CStructGenerator.generate_struct` | 未知の struct_type |
| 11 | `ValueError` | `VariableGenerator.generate_variable` | 未知の var_type |
| 12 | `FileNotFoundError` | `project_from_xml` | ファイル不在 |
| 13 | `ET.ParseError` | `project_from_xml` | XML 不正 |
| 14 | `OSError` | `save_generated_code` | 書込み失敗 |
| 15 | `ImportError` | モジュールインポート | 依存不足（フォールバックあり） |

### 8.2 検証課題コード

全35コードは §5.4 参照。プレフィックス一覧：

| プレフィックス | カテゴリ |
|--------------|---------|
| `STATE_` | 状態 |
| `EVENT_` | イベント |
| `TRANSITION_` | 遷移 |
| `ROLE_FUNC_` | ロール関数 |
| `VAR_` | 変数 |
| `FLAG_` | フラグ |
| `QUEUE_` | キュー |
| `INTERRUPT_` | 割り込み |
| `TIMER_` | タイマー |
| `TYPE_` | カスタム型 |
| `CELL_` | セル（v2.2） |

### 8.3 ログレベル

| レベル | 用途 |
|--------|------|
| `DEBUG` | 内部トレース |
| `INFO` | 正常完了 |
| `WARNING` | 非致命的問題（重複、未知型） |
| `ERROR` | 失敗（バリデータ例外、XML 解析） |

---

## 9. 制限事項

### 9.1 コード生成

| # | 制限 |
|---|------|
| L-01 | `generation_style="switch_case"` は実質無効（`table_driven` 固定） |
| L-02 | `table_type="switch"/"dictionary"` は実質無効（`array` 固定） |
| L-03 | `project_dir_name` 予約、未使用 |
| L-04 | `external_includes_in_role/transitions/common` 未実装 |
| L-05 | `super_include_dir` は XML 非永続 |
| L-06 | 多層 `by_type` は1ファイルにマージ（層分離不可視） |
| L-07 | `generate_all` は単一ステートマシン向け。複数層には `generate_all_layers` を使用 |

### 9.2 マーカー方式マージ

| # | 制限 |
|---|------|
| L-08 | マーカー改変時は抽出失敗（警告のみ、データロス） |
| L-09 | `inject_func_user_code` はマーカー不在時に新規挿入しない |
| L-10 | 同名関数が複数ファイルにある場合、最初の一致のみ使用 |

### 9.3 MISRA 連携

| # | 制限 |
|---|------|
| L-11 | `cppcheck + MISRA addon` は公認チェッカーではない |
| L-12 | `SUPPRESSED_RULES`（`analyze_misra_impact.py`）と `suppressions.txt` が不一致 |
| L-13 | `baseline.md` は空（実測値未記録） |
| L-14 | 出力 XML ファイル名 `cppcheck_raw.xml` が SPEC の `cppcheck_stderr.txt` と異なる |
| L-15 | 抑制理由は本 SDK リファレンス（§6.4）で全11ルールを文書化済みだが、`SPEC_OVERVIEW_ja.md` §7.4.4 では11ルール中4件のみ記載 |
| L-16 | cppcheck 依存（PATH 必須、600秒タイムアウト） |

### 9.4 検証

| # | 制限 |
|---|------|
| L-17 | `codegen/validate/` は S7 時点で未共有 |
| L-18 | `AIResponseParser` は v2.2 セル単位7アクションを解析しない |
| L-19 | `ChangeApplier._add_variable/_add_flag` は重複チェックなし |
| L-20 | `AIPromptGenerator._format_data` は v2.2 `pre_actions` 等を出力しない |
| L-21 | `CellValidator` は設計が異なる（`validate()` オーバーライドなし、`suggestion` なし） |
| L-22 | `EventValidator` の `EVENT_UNUSED` と `EVENT_NO_TRANSITION` は意味重複 |
| L-23 | `RoleFunctionValidator.ROLE_FUNC_UNUSED` は `Transition.action` / `.condition` の文字列完全一致のみ。v2.2 `pre_actions` / `else_actions` / セルアクションは未考慮 |

### 9.5 データモデル

| # | 制限 |
|---|------|
| L-24 | `StateMachine.role_functions` は純粋名キー → 名前空間間で衝突 |
| L-25 | `StateMachine` のロール関数キーと `RoleFunctionLibrary` のキーが異なる（純粋名 vs qualified） |

### 9.6 構造

| # | 制限 |
|---|------|
| L-26 | `TransitionContext_t` と `TransitionContext_<Layer>_t` が両方出力される（同一レイアウト） |
| L-27 | `statable/xml_io.py` が `statable_gui.libcntrl` に逆依存（try/except フォールバック） |
| L-28 | 2つの別々の `RoleFunction` クラス（`statable.model` vs `libcntrl`） |
| L-29 | 2つの別々の `GlobalDefinitions` クラス（`statable` vs `statable_gui`） |

---

## 10. 付録

### 10.1 ファイルツリー（`code/` 起点）

```
code/
├── statable/
│   ├── __init__.py
│   ├── model.py
│   ├── state_machine.py
│   ├── global_defs.py
│   ├── xml_io.py
│   ├── mermaid_gen.py
│   ├── sample_data.py
│   └── parser.py
├── codegen/
│   ├── __init__.py
│   ├── c_code_generator.py
│   ├── config.py
│   ├── code_templates.py
│   ├── code_merger.py
│   ├── type_mapper.py
│   ├── naming_convention.py
│   ├── struct_generator.py
│   ├── enum_generator.py
│   ├── transition_generator.py
│   ├── role_function_generator.py
│   ├── variable_generator.py
│   ├── event_queue_generator.py
│   ├── interrupt_generator.py
│   ├── timer_generator.py
│   ├── osal_generator.py
│   ├── sample_data.py
│   └── validate/
│       ├── __init__.py
│       ├── validator.py
│       ├── models.py
│       ├── change_actions.py
│       ├── change_applier.py
│       ├── prompt_generator.py
│       ├── response_parser.py
│       ├── clipboard_manager.py
│       ├── validation_dialog.py
│       ├── logger.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── validation_rules.py
│       │   ├── prompt_templates.py
│       │   ├── action_definitions.py
│       │   └── keywords.py
│       └── items/
│           ├── __init__.py
│           ├── base_validator.py
│           ├── state_validator.py
│           ├── event_validator.py
│           ├── transition_validator.py
│           ├── role_function_validator.py
│           ├── variable_validator.py
│           ├── flag_validator.py
│           ├── queue_validator.py
│           ├── interrupt_validator.py
│           ├── timer_validator.py
│           ├── custom_type_validator.py
│           └── cell_validator.py
├── statable_gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── widgets.py
│   ├── matrix_table.py
│   ├── dialogs.py
│   ├── code_generation_dialog.py
│   ├── code_generation_settings_dialog.py
│   ├── validation_dialog.py
│   ├── condition_builder_dialog.py
│   ├── condition_edit_dialog.py
│   ├── global_defs_dialog.py
│   ├── event_definition_dialog.py
│   ├── event_delivery_settings_dialog.py
│   ├── event_queue_dialog.py
│   ├── interrupt_handler_edit_dialog.py
│   ├── layer_settings_dialog.py
│   ├── common_widgets.py
│   ├── action_edit_dialog.py
│   ├── role_function_dialog.py
│   ├── symbol_picker.py
│   ├── logger.py
│   ├── preferences.py
│   ├── preference_keys.py
│   ├── config.py
│   ├── traceball.py
│   ├── sample_data.py
│   ├── global_defs.py
│   ├── libcntrl/
│   │   ├── __init__.py
│   │   ├── role_function_library.py
│   │   ├── condition_library.py
│   │   ├── literal_library.py
│   │   ├── role_function_edit_dialog.py
│   │   └── literal_management_dialog.py
│   └── transition_editor_direct/
│       ├── __init__.py
│       ├── dialog.py
│       ├── draft.py
│       ├── palette_widget.py
│       ├── canvas_widget.py
│       ├── code_widget.py
│       ├── system_global_dialog.py
│       ├── transitions_tab.py
│       ├── actions_tab.py
│       ├── relations_tab.py
│       ├── relations_edit_dialog.py
│       ├── transition_actions_dialog.py
│       ├── overview_tab.py
│       ├── coverage_analyzer.py
│       ├── flow_widget.py       (legacy)
│       └── edit_dialogs.py      (legacy)
├── tools/
│   ├── run_misra_check.py
│   ├── analyze_misra_impact.py
│   ├── find_all_japanese.py
│   └── verify_generated_code.py
├── misra/
│   ├── suppressions.txt
│   └── baseline.md
├── tests/
│   ├── test_v2_2_p1.py
│   ├── test_v2_2_p2.py
│   ├── test_v2_2_p3.py
│   ├── test_v2_2_p4a.py
│   ├── test_v2_2_p4b.py
│   ├── test_v2_2_p12_2.py
│   ├── test_v2_2_p12_5.py
│   ├── test_v2_2_p12_6.py
│   ├── test_v2_2_p12_7.py
│   ├── test_v2_2_p12_8.py
│   ├── test_v2_2_p12_9.py
│   └── test_v2_2_p12_10.py
└── sdk_doc_tools/
    ├── class_index.py
    ├── class_index.json
    └── class_index.md
```

### 10.2 テストスイート

| # | スイート | 対象 | 期待結果 |
|---|---------|------|---------|
| 1 | `test_v2_2_p1.py` | データモデル | 94 PASS |
| 2 | `test_v2_2_p2.py` | コード生成 | 67 PASS |
| 3 | `test_v2_2_p3.py` | 表示層 | 37 PASS |
| 4 | `test_v2_2_p4a.py` | 編集UI | 82 PASS |
| 5 | `test_v2_2_p4b.py` | Overview | 30 PASS |
| 6 | `test_v2_2_p12_2.py` | Stage 2 | 31 PASS |
| 7 | `test_v2_2_p12_5.py` | Stage 5 | 37 PASS |
| 8 | `test_v2_2_p12_6.py` | Stage 6 | 55 PASS |
| 9 | `test_v2_2_p12_7.py` | Stage 7 | 9 PASS |
| 10 | `test_v2_2_p12_8.py` | Stage 8 | 25 PASS |
| 11 | `test_v2_2_p12_9.py` | Stage 9 | 41 PASS |
| 12 | `test_v2_2_p12_10.py` | Stage 10 | 29 PASS / 2 SKIP |
| **合計** | | | **537 PASS / 2 SKIP** |

### 10.3 環境変数

| 変数 | 値 | 用途 |
|------|-----|------|
| `QT_QPA_PLATFORM` | `offscreen` | GUI ヘッドレス |
| `STATABLE_DISABLE_MERMAID` | `1` | Mermaid 抑制 |
| `PYTHONIOENCODING` | `utf-8` | エンコーディング問題防止 |

### 10.4 MISRA 成果物

| 成果物 | パス |
|--------|------|
| 抑制リスト | `misra/suppressions.txt` |
| ベースライン | `misra/baseline.md` |
| cppcheck 出力（stdout） | `misra_report/cppcheck_raw.xml` |
| cppcheck 出力（stderr） | `misra_report/cppcheck_stderr.txt` |
| サマリ | `misra_report/summary.md` |
| 影響分析 | `misra_report/impact.md` |
| 影響 CSV | `misra_report/impact.csv` |

### 10.5 バージョン一覧

| コンポーネント | バージョン |
|---------------|-----------|
| StaTable | 2.2 |
| `c_code_generator.py` | 2.2.9 |
| `role_function_generator.py` | 3.3 |
| `transition_generator.py` | 2.6 |
| `code_templates.py` | 2.2.5 |
| `struct_generator.py` | 2.2.1 |
| `enum_generator.py` | 1.5 |
| `variable_generator.py` | 2.0 |
| `timer_generator.py` | 2.2 |
| `osal_generator.py` | 2.2 |
| `naming_convention.py` | 2.2.5 |
| `code_merger.py` | 2.0 |

### 10.6 改訂履歴

| バージョン | 日付 | 内容 |
|-----------|------|------|
| 1.0 | 2026-09-21 | 英語版マスター初版 |
| 1.1 | 2026-09-21 | レビュー修正（R-1〜R-7）： |
| | | - R-1：§7.5.2 クロスリファレンス修正（§9 L-35 → §9 L-28） |
| | | - R-2：§5.4 `ROLE_FUNC_UNUSED` の v2.2 挙動注記追加 |
| | | - R-3：§3.5 / §3.7 `__post_init__` 挙動を文書化 |
| | | - R-4：§9 L-15 を SDK参考書と SPEC_OVERVIEW の文書化範囲を区別するよう書き換え |
| | | - R-5：§10.1 ファイルツリー完成（全 GUI / libcntrl ファイルを列挙） |
| | | - R-6：§7.1 XML スキーマ参照（`SPEC_OVERVIEW_ja.md` §3.5.2）を追加 |
| | | - R-7：§5.3 `BaseValidator` のパターンA/B の差異を明記 |

---

