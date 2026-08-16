"""グローバル変数・イベントフラグ・割り込み処理・デバイスリソース・タイマ設定のデータモデル（GUI層リエクスポート）"""

from statable.global_defs import (
    SystemVariable,
    EventFlag,
    InterruptHandlerDef,
    InterruptAction,
    DevicePlaceholderDef,
    TimerBaseDef,
    TimerDerivedDef,
    GlobalDefinitions,
)

__all__ = [
    "SystemVariable",
    "EventFlag",
    "InterruptHandlerDef",
    "InterruptAction",
    "DevicePlaceholderDef",
    "TimerBaseDef",
    "TimerDerivedDef",
    "GlobalDefinitions",
]