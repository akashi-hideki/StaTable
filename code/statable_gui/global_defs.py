"""Data model for global variables, event flags, interrupt handlers, device resources, and timer settings"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SystemVariable:
    """Global variables shared across the system"""
    name: str
    type: str
    unit: str = ""
    default_value: str = ""
    group: str = ""
    description: str = ""
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"変数: {self.name}"


@dataclass
class EventFlag:
    """Event flags managed as bit fields"""
    name: str
    min_value: int
    max_value: int
    group: str = ""
    description: str = ""
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"フラグ: {self.name}"

    @property
    def bit_width(self) -> int:
        if self.max_value < self.min_value:
            return 0
        return (self.max_value - self.min_value).bit_length()


@dataclass
class InterruptAction:
    """Conditional actions inside an interrupt handler"""
    condition: str = ""
    action: str = ""


@dataclass
class InterruptHandlerDef:
    """割り込み処理定義"""
    name: str
    description: str = ""
    event_names: List[str] = field(default_factory=list)
    is_timer: bool = False
    actions: List[InterruptAction] = field(default_factory=list)
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"割り込み: {self.name}"


@dataclass
class DevicePlaceholderDef:
    """Device resource placeholder definition"""
    name: str
    description: str = ""
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"デバイス: {self.name}"


@dataclass
class TimerDerivedDef:
    """Derived timer variable definition"""
    period_name: str
    multiplier: int
    variable_name: str
    data_type: str = "uint8_t"
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"タイマ: {self.variable_name}"


@dataclass
class TimerBaseDef:
    """Timer tick variable definition"""
    variable_name: str = "g_system_tick"
    unit: str = "1ms"
    data_type: str = "volatile uint32_t"
    derived: List[TimerDerivedDef] = field(default_factory=list)
    title: str = ""
    interrupt_name: str = ""   # ★ このTimerを駆動するInterrupt name

    def __post_init__(self):
        if not self.title:
            self.title = f"タイマ基準: {self.variable_name}"


@dataclass
class EventQueueDef:
    """Event queue definition"""
    name: str
    size: int
    element_type: str
    event_ids: List[str] = field(default_factory=list)
    priority_enabled: bool = False
    interrupt_safe: bool = True
    rtos_enabled: bool = False
    description: str = ""
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"キュー: {self.name}"


class GlobalDefinitions:
    """Management class for global variables, event flags, interrupt handlers, device resources, timer settings, and event queues"""

    def __init__(self):
        self.variables: List[SystemVariable] = []
        self.flags: List[EventFlag] = []
        self.interrupts: List[InterruptHandlerDef] = []
        self.placeholders: List[DevicePlaceholderDef] = []
        self.timer_base: TimerBaseDef = TimerBaseDef()
        self.extra_timers: List[TimerBaseDef] = []   # ★ AddTimer基準
        self.event_queues: List[EventQueueDef] = []

    def add_timer_variables(self):
        """Register all timer base variables and derived timer variables as global variables"""
        self.variables = [v for v in self.variables if v.group != "Timer"]

        all_timers = [self.timer_base] + self.extra_timers
        for timer in all_timers:
            self.variables.append(SystemVariable(
                name=timer.variable_name,
                type=timer.data_type,
                unit=timer.unit,
                default_value="0",
                group="Timer",
                description="Timer base variable",
                title=timer.title,
            ))
            for d in timer.derived:
                self.variables.append(SystemVariable(
                    name=d.variable_name,
                    type=d.data_type,
                    unit=d.period_name,
                    default_value="0",
                    group="Timer",
                    description=f"派生タイマ変数（{d.period_name}）",
                    title=d.title,
                ))

    def variable_groups(self) -> List[str]:
        return sorted({v.group for v in self.variables if v.group})

    def flag_groups(self) -> List[str]:
        return sorted({f.group for f in self.flags if f.group})