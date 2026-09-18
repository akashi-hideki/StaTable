"""Global variables・Event flags・Interrupt handler, device resources,Timer設定・ユーザー定義Typeのデータモデル"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StructMemberDef:
    """Struct member definition"""
    name: str
    data_type: str
    bit_width: int = 0
    description: str = ""
    title: str = ""
    array_size: int = 0

    def __post_init__(self):
        if not self.title:
            if self.bit_width > 0:
                self.title = f"{self.name}:{self.bit_width}"
            elif self.array_size > 0:
                self.title = f"{self.name}[{self.array_size}]"
            else:
                self.title = f"メンバ: {self.name}"


@dataclass
class CustomTypeDef:
    """ユーザー定義Type（Structなど）"""
    name: str
    description: str = ""
    members: List[StructMemberDef] = field(default_factory=list)
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"型: {self.name}"


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
    array_size: int = 0

    def __post_init__(self):
        if not self.title:
            if self.array_size > 0:
                self.title = f"{self.name}[{self.array_size}]"
            else:
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
    """Interrupt handler definition

    used_role_functions: 使用Role functionの qualified_name リスト（自動抽出）
      - 例: ["Driver.Init", "Application.HandleTick"]
      - ISR の action Save時に更新
      - 生成Codeのコメントにも使用

    used_variables: 使用Global variables名のリスト（自動抽出）
      - 例: ["counter", "g_system_tick"]
    """
    name: str
    description: str = ""
    event_names: List[str] = field(default_factory=list)
    is_timer: bool = False
    actions: List[InterruptAction] = field(default_factory=list)
    title: str = ""
    # ★ Add: 使用記録
    used_role_functions: List[str] = field(default_factory=list)
    used_variables: List[str] = field(default_factory=list)

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
    interrupt_name: str = ""

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
    """Global variables・Event flags・Interrupt handler, device resources,Timer設定・EventQueue・ユーザー定義Typeの管理クラス"""

    def __init__(self):
        self.variables: List[SystemVariable] = []
        self.flags: List[EventFlag] = []
        self.interrupts: List[InterruptHandlerDef] = []
        self.placeholders: List[DevicePlaceholderDef] = []
        self.timer_base: TimerBaseDef = TimerBaseDef()
        self.extra_timers: List[TimerBaseDef] = []
        self.event_queues: List[EventQueueDef] = []
        self.custom_types: List[CustomTypeDef] = []

    def add_timer_variables(self):
        """Timer base variable・派生TimerVariableをGlobal variablesとして登録する。

        - 既存Variable（XML 読込 or GUI Edit済）は description / title を保持
        - type / unit のみTimer定義側と同期
        - 存在しないVariableのみ新規Add

        これにより round-trip で description / title がSaveされる。
        """
        existing_by_name = {v.name: v for v in self.variables}

        def _sync_or_add(name, type_, unit, default, group,
                         default_desc, default_title):
            if name in existing_by_name:
                v = existing_by_name[name]
                # Timer定義を正とする（Type・Unit）
                v.type = type_
                v.unit = unit
                # Preserve existing description / title
                if not v.description:
                    v.description = default_desc
                if not v.title:
                    v.title = default_title
                # GroupがNot setなら補完
                if not v.group:
                    v.group = group
            else:
                self.variables.append(SystemVariable(
                    name=name,
                    type=type_,
                    unit=unit,
                    default_value=default,
                    group=group,
                    description=default_desc,
                    title=default_title,
                ))

        all_timers = [self.timer_base] + self.extra_timers
        for timer in all_timers:
            # 基準TimerVariable
            _sync_or_add(
                name=timer.variable_name,
                type_=timer.data_type,
                unit=timer.unit,
                default="0",
                group="Timer",
                default_desc="Timer base variable",
                default_title=timer.title or f"タイマ基準: {timer.variable_name}",
            )
            # 派生TimerVariable
            for d in timer.derived:
                _sync_or_add(
                    name=d.variable_name,
                    type_=d.data_type,
                    unit=d.period_name,
                    default="0",
                    group="Timer",
                    default_desc=f"派生タイマ変数（{d.period_name}）",
                    default_title=d.title or f"タイマ: {d.variable_name}",
                )

    # Group名の取得
    def variable_groups(self) -> List[str]:
        return sorted({v.group for v in self.variables if v.group})

    def flag_groups(self) -> List[str]:
        return sorted({f.group for f in self.flags if f.group})

    def custom_type_names(self) -> List[str]:
        return sorted({t.name for t in self.custom_types})