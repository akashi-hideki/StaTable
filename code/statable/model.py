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
    """イベントの発生源レイヤ"""
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
            self.title = f"イベント: {self.name}" if self.name else "イベント: （完了）"


@dataclass
class Transition:
    """
    状態遷移定義

    【注意】本クラスは kw_only 化していません。
    sample_data.py の `Transition("Idle", "START", "", "init()", "Active", ...)`
    という位置引数バグ（v1.4 §9.6 #67）が残っているため、kw_only 化すると
    起動時に TypeError になります。sample_data.py の修正後に kw_only 化予定。
    """
    source: str
    event: str
    condition: str = ""                # 条件式（シンボル名で保持）
    pre_actions: List[str] = field(default_factory=list)  # 遷移直前処理
    target: str = ""
    has_else: bool = True
    else_target: str = ""
    else_actions: List[str] = field(default_factory=list)  # elseアクション
    action: str = ""                   # 旧フィールド（互換用・未使用）
    transition_type: str = "external"
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = "(無題遷移)"


@dataclass(kw_only=True)
class RoleFunction:
    """
    ロール関数（状態遷移条件・動作をまとめて実装する関数）

    【v1.5 変更】kw_only=True 化
      位置引数によるフィールド順序ずれ事故（v1.4 §9.6 #76）を
      構造的に防止するため、kw_only 引数のみ受け付ける。

    旧: RoleFunction(name, desc, ret, ...)  ← 位置引数（危険）
    新: RoleFunction(name=..., description=..., return_type=...)  ← kwarg のみ

    namespace: 層名や機能グループ名（例: "Driver"）
      - `Driver.Init` のように参照可能
      - 空文字の場合は層なし扱い
    """
    name: str                               # 純粋名（例: "Init"）
    namespace: str = ""                     # 名前空間（例: "Driver"）
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