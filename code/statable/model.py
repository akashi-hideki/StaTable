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
    name: str
    type: StateType = StateType.NORMAL
    parent: Optional[str] = None
    entry: str = ""
    exit: str = ""
    do: str = ""
    description: str = ""


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
            self.title = f"イベント: {self.name}" if self.name else "Event: (completion)"


@dataclass(kw_only=True)
class Transition:
    """
    State transition definition

    [v1.6 change] kw_only=True
      To structurally prevent positional-argument field-order accidents
      (v1.4 section 9.6 #67), only kw_only arguments are accepted.

    Old: Transition("Idle", "START", "", ["init()"], "Active")  <- positional args (dangerous)
    New: Transition(source="Idle", event="START", pre_actions=["init()"], ...)  <- kwargs only

    In v1.5, an AST audit confirmed that all 14 sites in sample_data.py /
    xml_io.py / dialogs.py / draft.py / change_applier.py use kwargs.

    [v2.0 known constraint: transition_type is a reserved field]
      - "external": normal transition (default, implemented)
      - "internal": executes only the action without leaving the state (**unimplemented / reserved**)
      - "local":    self transition (**unimplemented / reserved**)

      As of v1.9, internal / local are unimplemented. Generated code
      (codegen/transition_generator.py) does not reference transition_type,
      and always treats it as equivalent to external (transition to target).

      Impact:
        - GUI (matrix_table.py) does not display a transition-type column
        - Generated code does not call entry / exit separately
        - XML save / load preserves the value (round-trip maintained)

      Reservation reason:
        Entry / exit call control widely affects the state machine runner
        (c_code_generator.py / template group), so
        v2.0 freezes the spec and implements it incrementally in v2.x.

      Reference: v1.9 section 9.9 #93 (consistency check detected)
    """
    source: str
    event: str
    condition: str = ""                # Condition expression (symbol names)
    pre_actions: List[str] = field(default_factory=list)  # Pre-transition processing
    target: str = ""
    has_else: bool = True
    else_target: str = ""
    else_actions: List[str] = field(default_factory=list)  # elseAction
    action: str = ""                   # Old field (compatibility)
    transition_type: str = "external"  # Reserved fields
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = "(untitled transition)"


@dataclass(kw_only=True)
class RoleFunction:
    """
    Role function (implements state transition conditions and actions together)

    [v1.5 change] kw_only=True
      To structurally prevent positional-argument field-order accidents
      (v1.4 section 9.6 #76), only kw_only arguments are accepted.

    Old: RoleFunction(name, desc, ret, ...)  <- positional args (dangerous)
    New: RoleFunction(name=..., description=..., return_type=...)  <- kwargs only

    namespace: layer name or feature group name (e.g. "Driver")
      - Referenceable as `Driver.Init`
      - Empty string means no layer
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
        """For GUI display / ISR reference"""
        if self.namespace:
            return f"{self.namespace}.{self.name}"
        return self.name

    @classmethod
    def from_legacy_name(cls, legacy_name: str,
                         layer_names: Optional[List[str]] = None) -> 'RoleFunction':
        """\n        Old form 'Driver_Init' -> namespace='Driver', name='Init'\n"""
        if not legacy_name:
            return cls(name="")
        if layer_names:
            for layer in layer_names:
                prefix = f"{layer}_"
                if legacy_name.startswith(prefix):
                    return cls(name=legacy_name[len(prefix):],
                               namespace=layer)
        return cls(name=legacy_name, namespace="")