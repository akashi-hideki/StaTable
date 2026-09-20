# S1成果物：データモデル層 API仕様ドラフト

`statable/model.py`, `statable/state_machine.py`, `statable/global_defs.py` を受領しました。H1中間引継ぎの前半として、§7データモデル章と§3コアAPI候補を作成します。

---

## 0. サマリ

| 項目 | 結果 |
|------|------|
| 解析対象 | 3ファイル、計22クラス（Enum 4 + Dataclass 16 + Container 2） |
| 公開API候補 | 22クラス全て |
| SPEC_OVERVIEW §3 との差分 | **5件のギャップ検出**（後述 §1） |
| S2への申し送り | 4件（後述 §5） |

---

## 1. SPEC_OVERVIEW_en.md との差分（重要）

| # | 差分 | 影響 | 対応 |
|---|------|------|------|
| D-01 | **`ActionStep`** がSPEC_OVERVIEW §3.2に記載なし | v2.2の中核概念。XMLでは §3.5.2 に記載あり | 本S1で正式にドラフト化（§3.5） |
| D-02 | **`TransitionRelation`** がSPEC_OVERVIEW §3.2に記載なし | v2.2の中核概念。`children` フィールド（再帰）は §12-5 のみ記載 | 本S1で正式にドラフト化（§3.6） |
| D-03 | `TransitionRelation.children` が `List["TransitionRelation"]` | 再帰的ネスト。仕様記述で明示要 | §3.6で明記 |
| D-04 | **`StateMachine.get_transitions_for_event`** がSPEC_OVERVIEW §3.3の表に記載なし | 全イベント横断検索API。公開判断要 | §4で公開候補として掲載 |
| D-05 | `State` / `Event` / `Transition` / `ActionStep` / `TransitionRelation` / `RoleFunction` の **`__post_init__` 挙動**がSPEC_OVERVIEWに未記載 | SDK利用時の暗黙変換（legacy migration、title自動生成） | 各クラスの「備考」に明記 |

---

## 2. §7 データモデル章ドラフト

### 2.1 列挙型（Enums）

#### 2.1.1 `StateType`

状態の種類を表す。

**シグネチャ**

```python
class StateType(Enum):
    NORMAL     = "normal"
    CONCURRENT = "concurrent"
    REGION     = "region"
    INITIAL    = "initial"
    FINAL      = "final"
    CHOICE     = "choice"
    JUNCTION   = "junction"
```

**値一覧**

| メンバ | 値 | 説明 |
|--------|-----|------|
| `NORMAL` | `"normal"` | 通常状態（デフォルト） |
| `CONCURRENT` | `"concurrent"` | 並行状態 |
| `REGION` | `"region"` | 並行リージョン |
| `INITIAL` | `"initial"` | 初期疑似状態 |
| `FINAL` | `"final"` | 終了状態 |
| `CHOICE` | `"choice"` | 選択疑似状態 |
| `JUNCTION` | `"junction"` | ジャンクション疑似状態 |

**備考**：文字列値はXML永続化で使用。SDK利用者はEnum経由で参照すること。

---

#### 2.1.2 `EventKind`

イベントの種類。

```python
class EventKind(Enum):
    SIGNAL = "signal"
    CALL   = "call"
    TIME   = "time"
    CHANGE = "change"
```

| メンバ | 値 | 説明 |
|--------|-----|------|
| `SIGNAL` | `"signal"` | シグナル（デフォルト） |
| `CALL` | `"call"` | 関数呼び出し |
| `TIME` | `"time"` | 時間トリガ |
| `CHANGE` | `"change"` | 変化トリガ |

---

#### 2.1.3 `EventDeliveryType`

イベント配送方式。

```python
class EventDeliveryType(Enum):
    DIRECT = "direct"
    QUEUE  = "queue"
    DOUBLE = "double"
```

| メンバ | 値 | 説明 |
|--------|-----|------|
| `DIRECT` | `"direct"` | 直接配送（デフォルト）。ISR内で即時処理 |
| `QUEUE` | `"queue"` | キュー配送。後で処理 |
| `DOUBLE` | `"double"` | 二重配送。DIRECTとQUEUEの両方 |

**備考**：ISR連携仕様（`interrupt_generator.py`）と関連。`statable_gui/event_delivery_settings_dialog.py` の自動変換機能の対象。

---

#### 2.1.4 `EventSourceLayer`

イベントの発生源レイヤ。

```python
class EventSourceLayer(Enum):
    DRIVER     = "driver"
    MIDDLEWARE = "middleware"
```

| メンバ | 値 | 説明 |
|--------|-----|------|
| `DRIVER` | `"driver"` | ドライバ層（デフォルト） |
| `MIDDLEWARE` | `"middleware"` | ミドルウェア層 |

---

### 2.2 `State`（dataclass）

状態定義。

**シグネチャ**

```python
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

**フィールド**

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | 状態名（`StateMachine.states` のキー） |
| `type` | `StateType` | – | `NORMAL` | 状態種別 |
| `parent` | `Optional[str]` | – | `None` | 親状態名（階層化用） |
| `entry` | `List[str]` | – | `[]` | エントリ時アクション（v2.2で `str` → `List[str]`） |
| `exit` | `List[str]` | – | `[]` | エグジット時アクション（同上） |
| `do` | `str` | – | `""` | doアクション |
| `description` | `str` | – | `""` | 説明文 |

**例外**

なし（`__post_init__` 内で正規化のみ）

**使用例**

```python
from statable import State, StateType

s = State(
    name="Idle",
    type=StateType.NORMAL,
    entry=["Driver.IdleEntry"],
    exit=["Driver.IdleExit"],
)
```

**備考**

- **v2.2変更**：`entry` / `exit` は `List[str]` に変更。旧XMLの `str` / `None` は `__post_init__` で自動正規化される
  - `None` → `[]`
  - `""` → `[]`
  - `"func"` → `["func"]`
  - `"a; b"` のような複数はGUI側（SettingsPanel）が `"; "` 区切りで分割
- `parent` は将来の階層化用で、v2.2時点ではコード生成に未反映の可能性あり（要確認）

---

### 2.3 `Event`（dataclass）

状態遷移イベント。

**シグネチャ**

```python
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

**フィールド**

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | イベント名。空文字列は完了遷移を意味する |
| `id` | `Optional[int]` | – | `None` | イベントID |
| `kind` | `EventKind` | – | `SIGNAL` | イベント種別 |
| `params` | `List[str]` | – | `[]` | パラメータ名リスト |
| `priority` | `int` | – | `0` | 優先度 |
| `description` | `str` | – | `""` | 説明文 |
| `delivery_type` | `EventDeliveryType` | – | `DIRECT` | 配送方式 |
| `source_layer` | `EventSourceLayer` | – | `DRIVER` | 発生源レイヤ |
| `data_type` | `str` | – | `""` | 付随データ型 |
| `data_name` | `str` | – | `""` | 付随データ名 |
| `title` | `str` | – | `""` | 表示名（未設定時は自動生成） |

**例外**

なし

**備考**

- `title` が空の場合、`__post_init__` で `f"Event: {name}"` または `"Event: (completion)"`（name空時）が自動設定される
- `name == ""` は完了遷移（completion transition）として扱われる。`StateMachine.get_transitions_for_cell(source, "")` で取得可能

---

### 2.4 `Transition`（dataclass, kw_only）

状態遷移定義。**キーワード引数のみ**受け付ける。

**シグネチャ**

```python
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

**フィールド**

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `source` | `str` | ○ | – | 遷移元状態名 |
| `event` | `str` | ○ | – | イベント名（`""` = 完了遷移） |
| `condition` | `str` | – | `""` | 条件式（C式） |
| `pre_actions` | `List[str]` | – | `[]` | 遷移前アクション |
| `target` | `str` | – | `""` | 遷移先状態名 |
| `has_else` | `bool` | – | `True` | else節の有無 |
| `else_target` | `str` | – | `""` | else時の遷移先 |
| `else_actions` | `List[str]` | – | `[]` | else時アクション |
| `early_return` | `bool` | – | `False` | **v2.2**：`True` = Commit（同セル内の後続遷移を評価しない） |
| `label` | `str` | – | `""` | **v2.2**：セル内識別子（`"T1"`, `"T2"` 等）。`TransitionRelation.members` から参照 |
| `action` | `str` | – | `""` | **レガシー**（未使用） |
| `transition_type` | `str` | – | `"external"` | 遷移種別 |
| `title` | `str` | – | `""` | 表示名 |

**例外**

なし（`StateMachine.add_transition` で検証）

**使用例**

```python
from statable import Transition

t = Transition(
    source="Idle",
    event="START",
    condition="mode == MODE_AUTO",
    pre_actions=["Driver.PreCheck"],
    target="Running",
    early_return=True,
    label="T1",
)
```

**備考**

- **v1.6変更**：`kw_only=True`。位置引数での誤用を防ぐ
- **v2.2追加**：`early_return` / `label`
  - `early_return=True` の遷移が発火した場合、同セル内の後続遷移は評価されない（Commit）
  - `label` は `TransitionRelation.members` の参照キー。XMLに永続化される
- `action` は旧バージョンの互換用。新規コードでは `pre_actions` を使用

---

### 2.5 `ActionStep`（dataclass, kw_only）★ SPEC未記載

セル独立アクション（v2.2）。遷移条件に依存せず、セル評価の前後に実行される。

**シグネチャ**

```python
@dataclass(kw_only=True)
class ActionStep:
    role_function: str = ""
    trigger: str = "before_transitions"
    title: str = ""
```

**フィールド**

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `role_function` | `str` | – | `""` | 呼び出すロール関数名（qualified_name） |
| `trigger` | `str` | – | `"before_transitions"` | 実行タイミング |
| `title` | `str` | – | `""` | 表示名 |

**`trigger` の値**

| 値 | 説明 |
|-----|------|
| `"before_transitions"` | 遷移評価の直前に実行 |
| `"after_transitions"` | セル本体の最後に実行 |

**例外**

なし

**備考**

- **v2.2.4変更**：`kw_only=True`
- 旧XMLの `"always"` は `"before_transitions"` に自動マッピング（legacy migration）
- `title` が空の場合、`role_function` または `"(untitled action)"` が自動設定される
- `StateMachine.get_actions_for_cell` / `set_actions_for_cell` で管理

---

### 2.6 `TransitionRelation`（dataclass, kw_only）★ SPEC未記載

セル内の遷移間関係（v2.2）。

**シグネチャ**

```python
@dataclass(kw_only=True)
class TransitionRelation:
    kind: str = "sequential"
    members: List[str] = field(default_factory=list)
    shared_condition: str = ""
    note: str = ""
    children: List["TransitionRelation"] = field(default_factory=list)
```

**フィールド**

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `kind` | `str` | – | `"sequential"` | 関係種別 |
| `members` | `List[str]` | – | `[]` | 対象遷移の `label` リスト |
| `shared_condition` | `str` | – | `""` | 共有条件式（`kind == "group"` 時のみ有効） |
| `note` | `str` | – | `""` | メモ |
| `children` | `List[TransitionRelation]` | – | `[]` | **v2.2 §12-5**：ネストされた子関係（再帰） |

**`kind` の値**

| 値 | 説明 |
|-----|------|
| `"sequential"` | メンバーを順に評価（デフォルト） |
| `"exclusive"` | 最大1つだけ発火。コード生成時に early return を強制 |
| `"group"` | 論理グループ。`shared_condition` を外側の `if` として巻き上げ |

**例外**

なし

**備考**

- **v2.2.4変更**：`kw_only=True`
- `members` は `Transition.label` を参照する
- `shared_condition` は `kind == "group"` の場合のみ使用
- `children` は再帰的にネスト可能（v2.2 §12-5）

---

### 2.7 `RoleFunction`（dataclass, kw_only）

ロール関数（`statable/` バージョン）。`statable_gui/libcntrl/` の同名クラスとは**別クラス**。

**シグネチャ**

```python
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

**フィールド**

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | 純粋名（`"Init"`） |
| `namespace` | `str` | – | `""` | 名前空間（`"Driver"`） |
| `description` | `str` | – | `""` | 説明文 |
| `return_type` | `str` | – | `"void"` | 戻り値型 |
| `arg1_type` | `str` | – | `""` | 引数1の型 |
| `arg1_name` | `str` | – | `""` | 引数1の名前 |
| `arg2_type` | `str` | – | `""` | 引数2の型 |
| `arg2_name` | `str` | – | `""` | 引数2の名前 |
| `title` | `str` | – | `""` | 表示名 |

**プロパティ**

| 名前 | 型 | 説明 |
|------|-----|------|
| `qualified_name` | `str` | `namespace.name` または `name` |

**クラスメソッド**

```python
RoleFunction.from_legacy_name(
    legacy_name: str,
    layer_names: Optional[List[str]] = None
) -> RoleFunction
```

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `legacy_name` | `str` | ○ | 旧形式名（`"Driver_Init"`） |
| `layer_names` | `Optional[List[str]]` | – | レイヤ名リスト。プレフィックス分離に使用 |

| 戻り値 | 説明 |
|--------|------|
| `RoleFunction` | 分離後のインスタンス |

**例外**

なし

**使用例**

```python
from statable import RoleFunction

rf = RoleFunction(name="Init", namespace="Driver")
print(rf.qualified_name)  # "Driver.Init"

# レガシー形式からの変換
rf2 = RoleFunction.from_legacy_name("Driver_Init", ["Driver", "App"])
print(rf2.namespace, rf2.name)  # "Driver" "Init"
```

**備考**

- `name == "Driver_Init"` で `layer_names=["Driver"]` の場合 → `namespace="Driver", name="Init"`
- `layer_names` に一致しない場合 → `namespace=""`, `name=legacy_name` そのまま
- **重要**：`statable_gui/libcntrl/role_function_library.py` にも同名 `RoleFunction` が存在（別クラス、`used_global_vars` 等のフィールド追加）。SDK仕様では**両者の使い分けを明記する必要あり**（S8で詳細化）

---

### 2.8 グローバル定義系 dataclass（10種）

#### 2.8.1 `StructMemberDef`

構造体メンバ定義。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | メンバ名 |
| `data_type` | `str` | ○ | – | 型 |
| `bit_width` | `int` | – | `0` | ビット幅（>0でビットフィールド） |
| `description` | `str` | – | `""` | 説明 |
| `title` | `str` | – | `""` | 表示名 |
| `array_size` | `int` | – | `0` | 配列サイズ（>0で配列） |

**`__post_init__`**：`title` 未設定時、`bit_width > 0` → `"{name}:{bit_width}"`、`array_size > 0` → `"{name}[{array_size}]"`、それ以外 → `"Member: {name}"`

---

#### 2.8.2 `CustomTypeDef`

ユーザ定義型（構造体等）。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | 型名 |
| `description` | `str` | – | `""` | 説明 |
| `members` | `List[StructMemberDef]` | – | `[]` | メンバ |
| `title` | `str` | – | `""` | 表示名 |

**`__post_init__`**：`title` 未設定時 `"Type: {name}"`

---

#### 2.8.3 `SystemVariable`

システム全体で共有されるグローバル変数。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | 変数名 |
| `type` | `str` | ○ | – | 型 |
| `unit` | `str` | – | `""` | 単位 |
| `default_value` | `str` | – | `""` | デフォルト値 |
| `group` | `str` | – | `""` | グループ |
| `description` | `str` | – | `""` | 説明 |
| `title` | `str` | – | `""` | 表示名 |
| `array_size` | `int` | – | `0` | 配列サイズ |

**`__post_init__`**：`title` 未設定時、`array_size > 0` → `"{name}[{array_size}]"`、それ以外 → `"Variable: {name}"`

---

#### 2.8.4 `EventFlag`

ビットフィールド管理されるイベントフラグ。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | フラグ名 |
| `min_value` | `int` | ○ | – | 最小値 |
| `max_value` | `int` | ○ | – | 最大値 |
| `group` | `str` | – | `""` | グループ |
| `description` | `str` | – | `""` | 説明 |
| `title` | `str` | – | `""` | 表示名 |

**プロパティ**

| 名前 | 型 | 説明 |
|------|-----|------|
| `bit_width` | `int` | `(max_value - min_value).bit_length()`。`max < min` の場合は `0` |

---

#### 2.8.5 `InterruptAction`

割り込みハンドラ内の条件付きアクション。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `condition` | `str` | – | `""` | 条件式 |
| `action` | `str` | – | `""` | アクション |

---

#### 2.8.6 `InterruptHandlerDef`

割り込みハンドラ定義。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | ハンドラ名 |
| `description` | `str` | – | `""` | 説明 |
| `event_names` | `List[str]` | – | `[]` | 関連イベント名 |
| `is_timer` | `bool` | – | `False` | タイマー割り込みか |
| `actions` | `List[InterruptAction]` | – | `[]` | アクション |
| `title` | `str` | – | `""` | 表示名 |
| `used_role_functions` | `List[str]` | – | `[]` | 使用ロール関数（自動抽出） |
| `used_variables` | `List[str]` | – | `[]` | 使用変数（自動抽出） |

**`__post_init__`**：`title` 未設定時 `"Interrupt: {name}"`

**備考**：`used_role_functions` / `used_variables` は保存時に自動抽出され、生成コードのコメントにも使用される

---

#### 2.8.7 `DevicePlaceholderDef`

デバイスリソースプレースホルダ定義。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | プレースホルダ名 |
| `description` | `str` | – | `""` | 説明 |
| `title` | `str` | – | `""` | 表示名 |

**`__post_init__`**：`title` 未設定時 `"Device: {name}"`

---

#### 2.8.8 `TimerDerivedDef`

派生タイマー変数定義。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `period_name` | `str` | ○ | – | 周期名（`"10ms"` 等） |
| `multiplier` | `int` | ○ | – | ベースタイマーへの乗数 |
| `variable_name` | `str` | ○ | – | 変数名 |
| `data_type` | `str` | – | `"uint8_t"` | 型 |
| `title` | `str` | – | `""` | 表示名 |

**`__post_init__`**：`title` 未設定時 `"Timer: {variable_name}"`

---

#### 2.8.9 `TimerBaseDef`

ベースタイマー定義。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `variable_name` | `str` | – | `"g_system_tick"` | ベース変数名 |
| `unit` | `str` | – | `"1ms"` | 単位 |
| `data_type` | `str` | – | `"volatile uint32_t"` | 型 |
| `derived` | `List[TimerDerivedDef]` | – | `[]` | 派生タイマー |
| `title` | `str` | – | `""` | 表示名 |
| `interrupt_name` | `str` | – | `""` | 関連割り込み名 |

**`__post_init__`**：`title` 未設定時 `"Timer base: {variable_name}"`

---

#### 2.8.10 `EventQueueDef`

イベントキューの定義。

| 名前 | 型 | 必須 | デフォルト | 説明 |
|------|-----|------|-----------|------|
| `name` | `str` | ○ | – | キュー名 |
| `size` | `int` | ○ | – | サイズ |
| `element_type` | `str` | ○ | – | 要素型 |
| `event_ids` | `List[str]` | – | `[]` | 対象イベントID |
| `priority_enabled` | `bool` | – | `False` | 優先度付きキュー |
| `interrupt_safe` | `bool` | – | `True` | 割り込み安全 |
| `rtos_enabled` | `bool` | – | `False` | RTOS対応 |
| `description` | `str` | – | `""` | 説明 |
| `title` | `str` | – | `""` | 表示名 |

**`__post_init__`**：`title` 未設定時 `"Queue: {name}"`

---

### 2.9 `GlobalDefinitions`（コンテナクラス）

グローバル定義の管理クラス。

**シグネチャ**

```python
class GlobalDefinitions:
    def __init__(self) -> None: ...
```

**属性**

| 名前 | 型 | デフォルト | 説明 |
|------|-----|-----------|------|
| `variables` | `List[SystemVariable]` | `[]` | グローバル変数 |
| `flags` | `List[EventFlag]` | `[]` | イベントフラグ |
| `interrupts` | `List[InterruptHandlerDef]` | `[]` | 割り込みハンドラ |
| `placeholders` | `List[DevicePlaceholderDef]` | `[]` | デバイスプレースホルダ |
| `timer_base` | `TimerBaseDef` | `TimerBaseDef()` | ベースタイマー |
| `extra_timers` | `List[TimerBaseDef]` | `[]` | 追加タイマー |
| `event_queues` | `List[EventQueueDef]` | `[]` | イベントキュー |
| `custom_types` | `List[CustomTypeDef]` | `[]` | ユーザ定義型 |

**メソッド**

#### `add_timer_variables()`

タイマー定義を `variables` に同期・登録する。

```python
def add_timer_variables(self) -> None
```

**動作**

- `timer_base` と `extra_timers` の各タイマーについて、ベース変数・派生変数を `variables` に登録
- 既存変数がある場合は `type` / `unit` のみ同期、`description` / `title` は保持
- 存在しない変数のみ新規追加

**使用例**

```python
from statable import GlobalDefinitions

gd = GlobalDefinitions()
gd.timer_base.variable_name = "g_tick"
gd.add_timer_variables()
# gd.variables に "g_tick" が SystemVariable として登録される
```

#### `variable_groups() -> List[str]`

変数グループ名のソート済みリストを返す。

```python
def variable_groups(self) -> List[str]
```

**戻り値**：`group` が空でない変数のユニークグループ名（昇順）

#### `flag_groups() -> List[str]`

フラググループ名のソート済みリストを返す。

```python
def flag_groups(self) -> List[str]
```

**戻り値**：`group` が空でないフラグのユニークグループ名（昇順）

#### `custom_type_names() -> List[str]`

ユーザ定義型名のソート済みリストを返す。

```python
def custom_type_names(self) -> List[str]
```

**戻り値**：`custom_types` の `name` 一覧（昇順）

---

## 3. §3 コアAPI候補：`StateMachine`

**シグネチャ**

```python
class StateMachine:
    def __init__(self) -> None: ...
```

**属性**

| 名前 | 型 | デフォルト | 説明 |
|------|-----|-----------|------|
| `states` | `Dict[str, State]` | `{}` | 状態辞書（キー: 状態名） |
| `events` | `Dict[str, Event]` | `{}` | イベント辞書（キー: イベント名） |
| `transitions` | `List[Transition]` | `[]` | 遷移リスト |
| `role_functions` | `Dict[str, RoleFunction]` | `{}` | ロール関数辞書（キー: `rf.name` = 純粋名） |
| `initial_state` | `Optional[str]` | `None` | 初期状態名 |
| `layer_priority` | `int` | `5` | レイヤ優先度（1〜9） |
| `layer_description` | `str` | `""` | レイヤ説明 |
| `layer_name` | `str` | `""` | レイヤ名 |
| `cell_actions` | `Dict[Tuple[str,str], List[ActionStep]]` | `{}` | v2.2：セルアクション |
| `cell_relations` | `Dict[Tuple[str,str], List[TransitionRelation]]` | `{}` | v2.2：セル関係 |

**注意**：`role_functions` のキーは `rf.name`（純粋名）。`Driver.Init` と `App.Init` は衝突する（SPEC_OVERVIEW §3.3 備考と一致）。

### 3.1 メソッド一覧（全17）

| # | メソッド | 種別 | SPEC_OVERVIEW記載 |
|---|---------|------|-------------------|
| 1 | `add_state` | 追加 | ○ |
| 2 | `add_event` | 追加 | ○ |
| 3 | `remove_event` | 削除 | ○ |
| 4 | `add_transition` | 追加 | ○ |
| 5 | `remove_transition` | 削除 | ○ |
| 6 | `set_initial` | 設定 | ○ |
| 7 | `add_role_function` | 追加 | ○ |
| 8 | `remove_role_function` | 削除 | ○ |
| 9 | `get_transitions_for_cell` | 取得 | ○ |
| 10 | `get_transitions_for_event` | 取得 | **×**（ギャップ D-04） |
| 11 | `get_actions_for_cell` | 取得（v2.2） | ○ |
| 12 | `set_actions_for_cell` | 設定（v2.2） | ○ |
| 13 | `get_relations_for_cell` | 取得（v2.2） | ○ |
| 14 | `set_relations_for_cell` | 設定（v2.2） | ○ |
| 15 | `get_cell_keys` | 取得（v2.2） | ○ |
| 16 | `remove_cell_metadata` | 削除（v2.2） | ○ |
| 17 | `remove_event` | （3と同一） | — |

### 3.2 各メソッド仕様

#### `add_state(state: State) -> None`

状態を追加する。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `state` | `State` | ○ | 追加する状態 |

**例外**

| 例外 | 条件 |
|------|------|
| `ValueError` | `state.name` が `self.states` に既存 |

---

#### `add_event(event: Event) -> None`

イベントを追加する。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `event` | `Event` | ○ | 追加するイベント |

**例外**

| 例外 | 条件 |
|------|------|
| `ValueError` | `event.name` が `self.events` に既存 |

---

#### `remove_event(name: str) -> None`

イベントと関連する遷移・セルメタデータを削除する。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | `str` | ○ | 削除するイベント名 |

**動作**

- `events[name]` を削除
- `transitions` から `t.event == name` の遷移を除外
- `cell_actions` / `cell_relations` から該当イベントのキーを削除（v2.2）

**例外**：なし（存在しない場合は何もしない）

---

#### `add_transition(trans: Transition) -> None`

遷移を追加する。追加前に参照整合性を検証。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `trans` | `Transition` | ○ | 追加する遷移 |

**例外**

| 例外 | 条件 |
|------|------|
| `ValueError` | `trans.source` が未定義の状態 |
| `ValueError` | `trans.target` が非空かつ未定義の状態 |
| `ValueError` | `trans.event` が非空かつ未定義のイベント |

**備考**：`target == ""`（完了遷移や未指定）および `event == ""`（完了遷移）は許容される

---

#### `remove_transition(trans: Transition) -> None`

遷移を削除する。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `trans` | `Transition` | ○ | 削除する遷移 |

**例外**：なし（存在しない場合は何もしない）

---

#### `set_initial(state_name: str) -> None`

初期状態を設定する。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `state_name` | `str` | ○ | 初期状態名 |

**例外**

| 例外 | 条件 |
|------|------|
| `ValueError` | `state_name` が未定義の状態 |

---

#### `add_role_function(rf: RoleFunction) -> None`

ロール関数を追加する。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `rf` | `RoleFunction` | ○ | 追加するロール関数 |

**例外**

| 例外 | 条件 |
|------|------|
| `ValueError` | `rf.name` が `self.role_functions` に既存 |

**備考**：キーは `rf.name`（純粋名）。名前空間が異なっても同名は衝突する（§3属性の注意参照）

---

#### `remove_role_function(name: str) -> None`

ロール関数を削除する。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | `str` | ○ | 削除するロール関数の純粋名 |

**例外**：なし

---

#### `get_transitions_for_cell(source: str, event: str) -> List[Transition]`

指定セルの遷移リストを返す。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `source` | `str` | ○ | 遷移元状態名 |
| `event` | `str` | ○ | イベント名（`""` = 完了遷移） |

**戻り値**：`List[Transition]` — 該当セルの遷移リスト（順序は `self.transitions` の登録順）

---

#### `get_transitions_for_event(event: str) -> List[Transition]` ★ SPEC未記載

指定イベントの全遷移を返す（状態横断）。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `event` | `str` | ○ | イベント名 |

**戻り値**：`List[Transition]` — 該当イベントの遷移リスト

**備考**：SPEC_OVERVIEW §3.3 の表に未記載。SDK公開判断要（ギャップ D-04）

---

#### `get_actions_for_cell(source: str, event: str) -> List[ActionStep]`

指定セルのアクションリストを返す（v2.2）。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `source` | `str` | ○ | 遷移元状態名 |
| `event` | `str` | ○ | イベント名 |

**戻り値**：`List[ActionStep]` — 未登録時は `[]`

---

#### `set_actions_for_cell(source: str, event: str, actions: List[ActionStep]) -> None`

指定セルのアクションを設定（v2.2）。

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `source` | `str` | ○ | 遷移元状態名 |
| `event` | `str` | ○ | イベント名 |
| `actions` | `List[ActionStep]` | ○ | アクションリスト |

**動作**：`actions` が空の場合は該当キーを削除（メモリ節約）

---

#### `get_relations_for_cell(source: str, event: str) -> List[TransitionRelation]`

指定セルの関係リストを返す（v2.2）。

**戻り値**：`List[TransitionRelation]` — 未登録時は `[]`

---

#### `set_relations_for_cell(source: str, event: str, relations: List[TransitionRelation]) -> None`

指定セルの関係を設定（v2.2）。

**動作**：`relations` が空の場合は該当キーを削除

---

#### `get_cell_keys() -> List[Tuple[str, str]]`

アクションまたは関係を持つ全セルキーを返す（v2.2）。

**戻り値**：`List[Tuple[str, str]]` — `(source, event)` のソート済みリスト

---

#### `remove_cell_metadata(source: str, event: str) -> None`

指定セルのアクション・関係を両方削除（v2.2）。

---

## 4. クイックスタート素材（S2で本文化）

```python
from statable import (
    StateMachine, State, Event, Transition, RoleFunction,
    GlobalDefinitions, SystemVariable,
)

# StateMachine構築
sm = StateMachine()
sm.layer_name = "Application"
sm.layer_priority = 5

sm.add_state(State(name="Idle", entry=["Driver.IdleEntry"]))
sm.add_state(State(name="Running"))
sm.add_event(Event(name="START"))
sm.add_event(Event(name="STOP"))

sm.add_role_function(RoleFunction(name="IdleEntry", namespace="Driver"))
sm.set_initial("Idle")

sm.add_transition(Transition(
    source="Idle", event="START", target="Running",
    condition="mode == MODE_AUTO", early_return=True, label="T1",
))
sm.add_transition(Transition(
    source="Running", event="STOP", target="Idle", label="T1",
))

# GlobalDefinitions
gd = GlobalDefinitions()
gd.variables.append(SystemVariable(name="mode", type="uint8_t", group="App"))
```

---

## 5. S2への申し送り

| # | 項目 | 内容 |
|---|------|------|
| S2-01 | `xml_io.py` はクラスなし（関数ベース） | `project_to_xml` / `project_from_xml` を関数APIとして仕様化 |
| S2-02 | `mermaid_gen.py` はクラスなし | `generate_mermaid(sm) -> str` の1関数 |
| S2-03 | `sample_data.py` はクラスなし | `create_sample_state_machine()` / `create_sample_global_defs()` の2関数 |
| S2-04 | **レガシー移行ロジックの所在確認** | `RoleFunction.from_legacy_name` の呼び出し元、`State.entry` の `str` → `List[str]` 正規化箇所を `xml_io.py` で確認要 |

---

## 6. H1中間引継ぎへの反映事項（前半）

| # | 反映先 | 内容 |
|---|--------|------|
| H1-01 | §7データモデル章 | 本ドラフトをそのまま採用 |
| H1-02 | §3コアAPI章 | `StateMachine` 全17メソッドを掲載 |
| H1-03 | §9制限事項 | `StateMachine.role_functions` の名前空間衝突（純粋名キー）を追記候補 |
| H1-04 | §9制限事項 | `RoleFunction` が `statable/` と `statable_gui/libcntrl/` に二重定義されている件 |
| H1-05 | §8エラーコード | `ValueError` の発生条件一覧を追加 |

---


S2完了後、**H1中間引継ぎ文書（S1+S2統合版）** を作成します。