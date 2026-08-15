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
    params: List[str] = field(default_factory=list)
    priority: int = 0
    description: str = ""


@dataclass
class Transition:
    source: str
    event: str
    guard: str = ""
    action: str = ""
    target: str = ""
    transition_type: str = "external"
    title: str = ""   # ★ 表示タイトル（省略時は自動生成）


@dataclass
class RoleFunction:
    name: str
    description: str = ""
    return_type: str = "int"
    arg1_type: str = "int"
    arg1_name: str = "arg1"
    arg2_type: str = "int"
    arg2_name: str = "arg2"