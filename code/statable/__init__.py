# statable package
"""
StaTable data model layer

Re-exports main classes for convenient external use.

[v1.5 added]
  - Re-export only lightweight-dependency modules to avoid circular imports
  - xml_io / sample_data are intentionally excluded
    (they have heavy dependencies and can cause circular references)
"""

# model.py (no dependencies) -- load first
from .model import (
    State,
    Event,
    Transition,
    StateType,
    EventKind,
    RoleFunction,
    EventDeliveryType,
    EventSourceLayer,
)

# state_machine.py (depends on model)
from .state_machine import StateMachine

# global_defs.py (no dependencies)
from .global_defs import (
    GlobalDefinitions,
    SystemVariable,
    EventFlag,
    InterruptHandlerDef,
    InterruptAction,
    DevicePlaceholderDef,
    TimerBaseDef,
    TimerDerivedDef,
    EventQueueDef,
    CustomTypeDef,
    StructMemberDef,
)

__all__ = [
    # model
    'State',
    'Event',
    'Transition',
    'StateType',
    'EventKind',
    'RoleFunction',
    'EventDeliveryType',
    'EventSourceLayer',
    # state_machine
    'StateMachine',
    # global_defs
    'GlobalDefinitions',
    'SystemVariable',
    'EventFlag',
    'InterruptHandlerDef',
    'InterruptAction',
    'DevicePlaceholderDef',
    'TimerBaseDef',
    'TimerDerivedDef',
    'EventQueueDef',
    'CustomTypeDef',
    'StructMemberDef',
]