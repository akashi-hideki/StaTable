"""グローバル変数・イベントフラグ・割り込み処理・デバイスリソース・タイマ設定のデータモデル"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SystemVariable:
    """システム全体で共有するグローバル変数"""
    name: str
    type: str
    unit: str = ""
    default_value: str = ""
    group: str = ""
    description: str = ""


@dataclass
class EventFlag:
    """ビットフィールドで扱うイベントフラグ"""
    name: str
    min_value: int
    max_value: int
    group: str = ""
    description: str = ""

    @property
    def bit_width(self) -> int:
        if self.max_value < self.min_value:
            return 0
        return (self.max_value - self.min_value).bit_length()


@dataclass
class InterruptAction:
    """割り込み処理内の条件付きアクション"""
    guard: str = ""        # ガード条件（空なら無条件）
    action: str = ""       # 動作コード


@dataclass
class InterruptHandlerDef:
    """割り込み処理定義"""
    name: str
    description: str = ""
    event_name: str = ""
    is_timer: bool = False
    actions: List[InterruptAction] = field(default_factory=list)


@dataclass
class DevicePlaceholderDef:
    """デバイスリソース仮定義"""
    name: str
    description: str = ""


@dataclass
class TimerDerivedDef:
    """派生タイマ変数定義"""
    period_name: str
    multiplier: int
    variable_name: str
    data_type: str = "uint8_t"


@dataclass
class TimerBaseDef:
    """タイマ刻み変数定義"""
    variable_name: str = "g_system_tick"
    unit: str = "1ms"
    data_type: str = "volatile uint32_t"
    derived: List[TimerDerivedDef] = field(default_factory=list)


@dataclass
class EventQueueDef:
    """イベントキュー定義"""
    name: str
    size: int
    element_type: str
    priority_enabled: bool = False
    interrupt_safe: bool = True
    rtos_enabled: bool = False
    description: str = ""


class GlobalDefinitions:
    """グローバル変数・イベントフラグ・割り込み処理・デバイスリソース・タイマ設定・イベントキューの管理クラス"""

    def __init__(self):
        self.variables: List[SystemVariable] = []
        self.flags: List[EventFlag] = []
        self.interrupts: List[InterruptHandlerDef] = []
        self.placeholders: List[DevicePlaceholderDef] = []
        self.timer_base: TimerBaseDef = TimerBaseDef()
        self.event_queues: List[EventQueueDef] = []   # ★ 追加

    def add_timer_variables(self):
        """タイマ基準変数・派生タイマ変数をグローバル変数として登録する"""
        # 既存のタイマ変数を一旦削除（グループ "Timer" として再登録）
        self.variables = [v for v in self.variables if v.group != "Timer"]

        # 基準変数
        self.variables.append(SystemVariable(
            name=self.timer_base.variable_name,
            type=self.timer_base.data_type,
            unit=self.timer_base.unit,
            default_value="0",
            group="Timer",
            description="タイマ基準変数"
        ))

        # 派生タイマ変数
        for d in self.timer_base.derived:
            self.variables.append(SystemVariable(
                name=d.variable_name,
                type=d.data_type,
                unit=d.period_name,
                default_value="0",
                group="Timer",
                description=f"派生タイマ変数（{d.period_name}）"
            ))

    # グループ名の取得
    def variable_groups(self) -> List[str]:
        return sorted({v.group for v in self.variables if v.group})

    def flag_groups(self) -> List[str]:
        return sorted({f.group for f in self.flags if f.group})