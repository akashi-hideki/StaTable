# statable package
"""
StaTable データモデル層

主要クラスを再エクスポートし、外部からの利用を簡便にする。

【v1.5 Add】
  - 循環インポート回避のため、依存の軽いモジュールのみ再エクスポート
  - xml_io / sample_data は意図的に除外
    （これらは重い依存を持ち、循環参照の原因になるため）
"""

# model.py（依存None）— 最初にロードすべき
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

# state_machine.py（model に依存）
from .state_machine import StateMachine

# global_defs.py（依存None）
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