from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


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
    """イベントの配送方法"""
    DIRECT = "direct"
    QUEUE = "queue"
    DOUBLE = "double"


class EventSourceLayer(Enum):
    """イベントのSourceレイヤ"""
    DRIVER = "driver"
    MIDDLEWARE = "middleware"


@dataclass
class State:
    name: str
    type: StateType = StateType.NORMAL
    parent: Optional[str] = None
    entry: str = ""
    exit: str = ""
    do: str = ""
    description: str = ""


@dataclass
class Event:
    """状態遷移イベント（ドライバ層・ミドル層から通知される）"""
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

    def __post_init__(self):
        if not self.title:
            self.title = f"イベント: {self.name}" if self.name else "イベント: (completion)"


@dataclass(kw_only=True)
class Transition:
    """
    状態遷移定義

    【v1.6 変更】kw_only=True 化
      位置引数によるフィールド順序ずれ事故（v1.4 §9.6 #67）を
      構造的に防止するため、kw_only 引数のみ受け付ける。

    旧: Transition("Idle", "START", "", ["init()"], "Active")  ← 位置引数（危険）
    新: Transition(source="Idle", event="START", pre_actions=["init()"], ...)  ← kwarg のみ

    v1.5 で sample_data.py / xml_io.py / dialogs.py / draft.py /
    change_applier.py の全 14 箇所が kwarg 済みであることを AST 監査でConfirm済み。

    【v2.0 既知の制約: transition_type は予約フィールド】
      - "external": 通常遷移（既定値、実装済み）
      - "internal": 状態を出ず action のみ実行（**未実装・予約**）
      - "local":    自己遷移（**未実装・予約**）

      v1.9 時点で internal / local は未実装。生成コード
      （codegen/transition_generator.py）は transition_type を参照せず、
      常に external 相当（target へ遷移）として扱う。

      影響:
        - GUI（matrix_table.py）に遷移種別列は表示されない
        - 生成コードで entry/exit 呼び分けは行われない
        - XML Save/読込では値が保持される（round-trip は維持）

      予約Reason:
        entry/exit 呼び出し制御は state machine runner
        （c_code_generator.py / テンプレート群）に広く影響するため、
        v2.0 では仕様を凍結し、v2.x で段階的に実装する。

      参照: v1.9 §9.9 #93（一貫性チェック検出）
    """
    source: str
    event: str
    condition: str = ""                # 条件式（シンボル名で保持）
    pre_actions: List[str] = field(default_factory=list)  # 遷移直前処理
    target: str = ""
    has_else: bool = True
    else_target: str = ""
    else_actions: List[str] = field(default_factory=list)  # elseAction
    action: str = ""                   # 旧フィールド（互換用・未使用）
    transition_type: str = "external"  # ★ 予約フィールド（上記 docstring 参照）
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = "(untitled transition)"


@dataclass(kw_only=True)
class RoleFunction:
    """
    Role function（State transition condition・動作をまとめて実装する関数）

    【v1.5 変更】kw_only=True 化
      位置引数によるフィールド順序ずれ事故（v1.4 §9.6 #76）を
      構造的に防止するため、kw_only 引数のみ受け付ける。

    旧: RoleFunction(name, desc, ret, ...)  ← 位置引数（危険）
    新: RoleFunction(name=..., description=..., return_type=...)  ← kwarg のみ

    namespace: 層名や機能Group名（例: "Driver"）
      - `Driver.Init` のように参照可能
      - 空文字の場合は層None扱い
    """
    name: str                               # Bare name (e.g., \"Init\")
    namespace: str = ""                     # Namespace (e.g., \"Driver\")
    description: str = ""
    return_type: str = "void"
    arg1_type: str = ""
    arg1_name: str = ""
    arg2_type: str = ""
    arg2_name: str = ""
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"ロール関数: {self.qualified_name}"

    @property
    def qualified_name(self) -> str:
        """GUI 表示・ISR 参照用: 'Driver.Init' または 'Init'"""
        if self.namespace:
            return f"{self.namespace}.{self.name}"
        return self.name

    @classmethod
    def from_legacy_name(cls, legacy_name: str,
                         layer_names: Optional[List[str]] = None) -> 'RoleFunction':
        """
        旧形式 'Driver_Init' → namespace='Driver', name='Init'
        レイヤ名リストに該当がなければ namespace=''
        """
        if not legacy_name:
            return cls(name="")
        if layer_names:
            for layer in layer_names:
                prefix = f"{layer}_"
                if legacy_name.startswith(prefix):
                    return cls(name=legacy_name[len(prefix):],
                               namespace=layer)
        return cls(name=legacy_name, namespace="")