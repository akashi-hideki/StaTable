from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict


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
    name: str
    id: Optional[int] = None
    kind: EventKind = EventKind.SIGNAL
    params: List[str] = field(default_factory=list)  # e.g. ["uint8_t err_code"]
    priority: int = 0
    description: str = ""


@dataclass
class Transition:
    source: str          # 状態名（フルパス）
    event: str           # イベント名（空文字列は完了遷移）
    guard: str = ""      # C言語式（GUI上は「遷移条件」と表示）
    action: str = ""     # 動作
    target: str = ""     # 次状態（空なら内部遷移）
    transition_type: str = "external"  # external / internal / local