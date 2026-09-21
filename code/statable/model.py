"""
statable/model.py
Data model for StaTable.

Version History
---------------
v1.0     - Initial data model.
v1.6     - Transition: kw_only=True. Prevents positional-argument
           field-order mistakes (see v1.4 §9.6 #67).
v2.2     - State.entry / State.exit: str -> List[str].
           ActionStep and TransitionRelation added.
v2.2.4   - ActionStep / TransitionRelation: kw_only=True.
v3.7     - Reserved-field annotations added:
             * State.do
             * RoleFunction.return_type / arg1_type / arg1_name
                                      / arg2_type / arg2_name
           These fields are not exposed in the GUI and not used by
           the code generator, but are retained in the data model
           and XML I/O for backward compatibility.
v3.8     - RoleFunction: added used_global_vars / used_events /
           used_literals. These mirror libcntrl.RoleFunction and
           enable the GUI dialog to track symbol references (see
           statable_gui/role_function_dialog.py v3.9). Persisted in
           XML (xml_io.py v3.8); not consumed by the code generator.
"""

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

    [v3.7 note]
      `do` is a **reserved field**. The code generator does not
      reference it, and it is not exposed in the GUI SettingsPanel
      (the "do function" column was removed in v3.7). It remains
      in the data model and in XML I/O for backward compatibility
      with projects created before v3.7.
    """
    name: str
    type: StateType = StateType.NORMAL
    parent: Optional[str] = None
    entry: List[str] = field(default_factory=list)
    exit: List[str] = field(default_factory=list)
    # [Reserved] Not exposed in UI / not used by codegen.
    # Persisted in XML for backward compatibility only.
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

    [v1.6 change] kw_only=True
      To structurally prevent positional-argument field-order accidents
      (v1.4 section 9.6 #67), only kw_only arguments are accepted.

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


@dataclass(kw_only=True)
class ActionStep:
    """Transition-independent action step (v2.2).

    [v2.2.4 change] kw_only=True
      To structurally prevent positional-argument field-order accidents
      (consistent with v1.5 RoleFunction / v1.6 Transition).

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


@dataclass(kw_only=True)
class TransitionRelation:
    """Relation between transitions in one cell (v2.2).

    [v2.2.4 change] kw_only=True
      To structurally prevent positional-argument field-order accidents
      (consistent with v1.5 RoleFunction / v1.6 Transition).

    kind:
      "sequential"  - evaluate members in order (default)
      "exclusive"   - at most one member fires; codegen enforces early return
      "group"       - logical grouping; shared_condition is hoisted
                      as an outer if (evaluated once)

    members: Transition.label values (e.g. ["T1", "T2"]).
    shared_condition: only used when kind == "group".

    [v2.2 §12-5] children: nested sub-relations (recursive).
    """
    kind: str = "sequential"
    members: List[str] = field(default_factory=list)
    shared_condition: str = ""
    note: str = ""
    children: List["TransitionRelation"] = field(default_factory=list)


@dataclass(kw_only=True)
class RoleFunction:
    """Role function (shared library / state machine local).

    [v3.7 note]
      The C signature generated for a role function is **fixed** to

          int RoleFunc_<NS>_<Name>(const Transition_t* transition,
                                   Context_t* ctx);

      by `codegen/role_function_generator.py`, which does not
      reference `return_type` / `arg1_*` / `arg2_*` at all.
      Those fields are therefore **reserved**:

        - They are not exposed in the GUI SettingsPanel or in
          RoleFunctionDialog (v3.7 / v3.8).
        - They are still serialized / deserialized by xml_io.py
          for backward compatibility with projects created
          before v3.7.
        - `SettingsPanel.apply_changes()` and `RoleFunctionDialog.
          get_role_function()` carry existing values forward so
          that an XML round-trip remains lossless.

      Do not remove these fields without a migration plan; old
      project files may rely on their presence.

    [v3.8 addition]
      used_global_vars / used_events / used_literals mirror the
      fields of libcntrl.RoleFunction. They let the RoleFunctionDialog
      track which symbols a role function references, without
      changing the generated C signature (which remains fixed as
      above). Persisted in XML; not consumed by the code generator.
    """
    name: str
    namespace: str = ""
    description: str = ""
    # [Reserved] Not exposed in UI / not used by codegen.
    # Persisted in XML for backward compatibility only.
    return_type: str = "void"
    # [Reserved] Not exposed in UI / not used by codegen.
    arg1_type: str = ""
    # [Reserved] Not exposed in UI / not used by codegen.
    arg1_name: str = ""
    # [Reserved] Not exposed in UI / not used by codegen.
    arg2_type: str = ""
    # [Reserved] Not exposed in UI / not used by codegen.
    arg2_name: str = ""
    title: str = ""
    # [v3.8] GUI symbol tracking (mirrors libcntrl.RoleFunction).
    # Persisted in XML; not consumed by codegen.
    used_global_vars: List[str] = field(default_factory=list)
    used_events: List[str] = field(default_factory=list)
    used_literals: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.title:
            self.title = f"Role function: {self.qualified_name}"
        # v3.8: defensive normalization
        if self.used_global_vars is None:
            self.used_global_vars = []
        if self.used_events is None:
            self.used_events = []
        if self.used_literals is None:
            self.used_literals = []

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