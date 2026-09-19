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
    """Event delivery method"""
    DIRECT = "direct"
    QUEUE = "queue"
    DOUBLE = "double"


class EventSourceLayer(Enum):
    """Event source layer"""
    DRIVER = "driver"
    MIDDLEWARE = "middleware"


@dataclass
class State:
    """State definition.

    [v2.2 change]
      entry / exit: str -> List[str]
        Multiple entry / exit actions are supported.
        For defensive compatibility, str / None are auto-normalized
        in __post_init__.
    """
    name: str
    type: StateType = StateType.NORMAL
    parent: Optional[str] = None
    entry: List[str] = field(default_factory=list)
    exit: List[str] = field(default_factory=list)
    do: str = ""
    description: str = ""

    def __post_init__(self):
        # v2.2: defensive normalization
        if self.entry is None:
            self.entry = []
        elif isinstance(self.entry, str):
            self.entry = [self.entry] if self.entry.strip() else []

        if self.exit is None:
            self.exit = []
        elif isinstance(self.exit, str):
            self.exit = [self.exit] if self.exit.strip() else []


@dataclass
class Event:
    """State transition event"""
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
            self.title = f"Event: {self.name}" if self.name else "Event: (completion)"


@dataclass(kw_only=True)
class Transition:
    """State transition definition.

    [v2.2 additions]
      early_return: bool = False
        - True  : "Commit"    - stop evaluating later transitions in the same cell
        - False : "Tentative" - later transitions may overwrite the target

      label: str = ""
        Stable identifier within a cell (e.g. "T1", "T2").
        Referenced by TransitionRelation.members.
        Persisted in XML.
    """
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

    def __post_init__(self):
        if not self.title:
            self.title = "(untitled transition)"


@dataclass
class ActionStep:
    """Transition-independent action step (v2.2).

    Represents an action that runs at a fixed phase of the cell,
    independent of any transition condition.

    trigger:
      "before_transitions" - runs just before evaluating transitions
      "after_transitions"  - runs at the end of the cell body

    Note: legacy "always" is silently mapped to "before_transitions"
    when loading old XML.
    """
    role_function: str = ""
    trigger: str = "before_transitions"
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = self.role_function or "(untitled action)"


@dataclass
class TransitionRelation:
    """Relation between transitions in one cell (v2.2).

    kind:
      "sequential"  - evaluate members in order (default)
      "exclusive"   - at most one member fires; codegen enforces early return
      "group"       - logical grouping; shared_condition is hoisted
                      as an outer if (evaluated once)

    members: Transition.label values (e.g. ["T1", "T2"]).
    shared_condition: only used when kind == "group".
    """
    kind: str = "sequential"
    members: List[str] = field(default_factory=list)
    shared_condition: str = ""
    note: str = ""


@dataclass(kw_only=True)
class RoleFunction:
    """Role function (shared library / state machine local)."""
    name: str
    namespace: str = ""
    description: str = ""
    return_type: str = "void"
    arg1_type: str = ""
    arg1_name: str = ""
    arg2_type: str = ""
    arg2_name: str = ""
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"Role function: {self.qualified_name}"

    @property
    def qualified_name(self) -> str:
        if self.namespace:
            return f"{self.namespace}.{self.name}"
        return self.name

    @classmethod
    def from_legacy_name(cls, legacy_name: str,
                         layer_names: Optional[List[str]] = None) -> 'RoleFunction':
        if not legacy_name:
            return cls(name="")
        if layer_names:
            for layer in layer_names:
                prefix = f"{layer}_"
                if legacy_name.startswith(prefix):
                    return cls(name=legacy_name[len(prefix):],
                               namespace=layer)
        return cls(name=legacy_name, namespace="")