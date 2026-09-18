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
        """タイマ基準変数・派生タイマ変数をグローバル変数として登録する。

        - 既存変数（XML 読込 or GUI 編集済）は description / title を保持
        - type / unit のみタイマ定義側と同期
        - 存在しない変数のみ新規追加

        これにより round-trip で description / title が保存される。
        """
        existing_by_name = {v.name: v for v in self.variables}

        def _sync_or_add(name, type_, unit, default, group,
                         default_desc, default_title):
            if name in existing_by_name:
                v = existing_by_name[name]
                # タイマ定義を正とする（型・単位）
                v.type = type_
                v.unit = unit
                # description / title は既存を尊重、空なら既定値
                if not v.description:
                    v.description = default_desc
                if not v.title:
                    v.title = default_title
                # グループが未設定なら補完
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
            # 基準タイマ変数
            _sync_or_add(
                name=timer.variable_name,
                type_=timer.data_type,
                unit=timer.unit,
                default="0",
                group="Timer",
                default_desc="タイマ基準変数",
                default_title=timer.title or f"タイマ基準: {timer.variable_name}",
            )
            # 派生タイマ変数
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

    # グループ名の取得
    def variable_groups(self) -> List[str]:
        return sorted({v.group for v in self.variables if v.group})

    def flag_groups(self) -> List[str]:
        return sorted({f.group for f in self.flags if f.group})

    def custom_type_names(self) -> List[str]:
        return sorted({t.name for t in self.custom_types})