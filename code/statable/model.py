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
    source: str
    event: str
    condition: str = ""
    action: str = ""
    target: str = ""
    transition_type: str = "external"
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = "(無題遷移)"


@dataclass
class RoleFunction:
    """ロール関数（状態遷移条件・動作をまとめて実装する関数）"""
    name: str
    description: str = ""
    return_type: str = "int"
    arg1_type: str = "int"
    arg1_name: str = "arg1"
    arg2_type: str = "int"
    arg2_name: str = "arg2"
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"ロール関数: {self.name}"