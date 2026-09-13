"""グローバル変数・イベントフラグ・割り込み処理・デバイスリソース・タイマ設定・ユーザー定義型のデータモデル"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StructMemberDef:
    """構造体メンバ定義"""
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
    """ユーザー定義型（構造体など）"""
    name: str
    description: str = ""
    members: List[StructMemberDef] = field(default_factory=list)
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"型: {self.name}"


@dataclass
class SystemVariable:
    """システム全体で共有するグローバル変数"""
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
    """ビットフィールドで扱うイベントフラグ"""
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
    """割り込み処理内の条件付きアクション"""
    condition: str = ""
    action: str = ""


@dataclass
class InterruptHandlerDef:
    """割り込み処理定義

    used_role_functions: 使用ロール関数の qualified_name リスト（自動抽出）
      - 例: ["Driver.Init", "Application.HandleTick"]
      - ISR の action 保存時に更新
      - 生成コードのコメントにも使用

    used_variables: 使用グローバル変数名のリスト（自動抽出）
      - 例: ["counter", "g_system_tick"]
    """
    name: str
    description: str = ""
    event_names: List[str] = field(default_factory=list)
    is_timer: bool = False
    actions: List[InterruptAction] = field(default_factory=list)
    title: str = ""
    # ★ 追加: 使用記録
    used_role_functions: List[str] = field(default_factory=list)
    used_variables: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.title:
            self.title = f"割り込み: {self.name}"


@dataclass
class DevicePlaceholderDef:
    """デバイスリソース仮定義"""
    name: str
    description: str = ""
    title: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"デバイス: {self.name}"


@dataclass
class TimerDerivedDef:
    """派生タイマ変数定義"""
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
    """タイマ刻み変数定義"""
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
    """イベントキュー定義"""
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
    """グローバル変数・イベントフラグ・割り込み処理・デバイスリソース・タイマ設定・イベントキュー・ユーザー定義型の管理クラス"""

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
        """タイマ基準変数・派生タイマ変数をグローバル変数として登録する"""
        # 既存のタイマ変数を一旦削除（グループ "Timer" として再登録）
        self.variables = [v for v in self.variables if v.group != "Timer"]

        all_timers = [self.timer_base] + self.extra_timers
        # 基準変数
        for timer in all_timers:
            self.variables.append(SystemVariable(
                name=timer.variable_name,
                type=timer.data_type,
                unit=timer.unit,
                default_value="0",
                group="Timer",
                description="タイマ基準変数",
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

    # グループ名の取得
    def variable_groups(self) -> List[str]:
        return sorted({v.group for v in self.variables if v.group})

    def flag_groups(self) -> List[str]:
        return sorted({f.group for f in self.flags if f.group})

    def custom_type_names(self) -> List[str]:
        return sorted({t.name for t in self.custom_types})