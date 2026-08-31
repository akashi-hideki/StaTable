# codegen/sample_data.py
"""
コード生成テスト用サンプルデータ
GUIとは独立したテストデータを提供する
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import State, Event, Transition, StateType, EventKind, RoleFunction
from statable.state_machine import StateMachine
from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    CustomTypeDef, StructMemberDef,
    EventQueueDef, InterruptHandlerDef, InterruptAction,
    DevicePlaceholderDef, TimerBaseDef, TimerDerivedDef
)


class SampleDataGenerator:
    """サンプルデータ生成クラス"""
    
    def __init__(self):
        self.state_machine = None
        self.global_defs = None
    
    def create_sample_state_machine(self):
        sm = StateMachine()
        
        sm.add_state(State(name="INIT", type=StateType.INITIAL, description="初期状態"))
        sm.add_state(State(name="IDLE", type=StateType.NORMAL, description="アイドル状態"))
        sm.add_state(State(name="RUNNING", type=StateType.NORMAL, description="実行状態"))
        sm.add_state(State(name="ERROR", type=StateType.NORMAL, description="エラー状態"))
        sm.set_initial("INIT")
        
        sm.add_event(Event(name="POWER_ON", kind=EventKind.SIGNAL, description="電源ONイベント"))
        sm.add_event(Event(name="START", kind=EventKind.SIGNAL, description="開始イベント"))
        sm.add_event(Event(name="STOP", kind=EventKind.SIGNAL, description="停止イベント"))
        sm.add_event(Event(name="ERROR_DETECTED", kind=EventKind.SIGNAL, description="エラー検出イベント"))
        
        sm.add_transition(Transition(source="INIT", event="POWER_ON", target="IDLE", action="PowerOn", title="電源ON"))
        sm.add_transition(Transition(source="IDLE", event="START", target="RUNNING", condition="StartOk", action="Start", title="開始"))
        sm.add_transition(Transition(source="RUNNING", event="STOP", target="IDLE", action="Stop", title="停止"))
        sm.add_transition(Transition(source="RUNNING", event="ERROR_DETECTED", target="ERROR", action="HandleError", title="エラー処理"))
        
        sm.add_role_function(RoleFunction(name="PowerOn", return_type="void", description="電源ON処理"))
        sm.add_role_function(RoleFunction(name="StartOk", return_type="bool", description="開始条件チェック"))
        sm.add_role_function(RoleFunction(name="Start", return_type="void", description="開始処理"))
        sm.add_role_function(RoleFunction(name="Stop", return_type="void", description="停止処理"))
        sm.add_role_function(RoleFunction(name="HandleError", return_type="void", description="エラー処理"))
        sm.add_role_function(RoleFunction(name="ProcessData", return_type="int",
                                         arg1_type="uint8_t*", arg1_name="data",
                                         arg2_type="uint16_t", arg2_name="len",
                                         description="データ処理"))
        
        self.state_machine = sm
        return sm
    
    def create_sample_global_defs(self):
        gd = GlobalDefinitions()
        
        # グローバル変数
        gd.variables = [
            SystemVariable(name="battery_voltage", type="uint16", unit="mV", group="Power", description="バッテリー電圧"),
            SystemVariable(name="system_tick", type="uint32", unit="ms", group="Timer", description="システムタイマ"),
            SystemVariable(name="temperature", type="int16", unit="0.1℃", group="Sensor", description="温度センサ値"),
            SystemVariable(name="data_buffer", type="uint8", group="Data", description="データバッファ", array_size=64),
        ]
        
        # イベントフラグ
        gd.flags = [
            EventFlag(name="EVT_POWER_ON_REQ", min_value=0, max_value=1, group="System", description="電源ON要求"),
            EventFlag(name="EVT_START_REQ", min_value=0, max_value=1, group="System", description="開始要求"),
            EventFlag(name="EVT_STOP_REQ", min_value=0, max_value=1, group="System", description="停止要求"),
            EventFlag(name="EVT_ERROR_FLAG", min_value=0, max_value=1, group="Error", description="エラーフラグ"),
        ]
        
        # ユーザー定義型
        gd.custom_types = [
            CustomTypeDef(name="SystemStatus", description="システム状態管理構造体", members=[
                StructMemberDef(name="power_on", data_type="bool", bit_width=1, description="電源ON状態"),
                StructMemberDef(name="initialized", data_type="bool", bit_width=1, description="初期化完了フラグ"),
                StructMemberDef(name="error_code", data_type="uint8", description="エラーコード"),
                StructMemberDef(name="mode", data_type="uint8", description="動作モード"),
            ]),
            CustomTypeDef(name="SensorData", description="センサーデータ構造体", members=[
                StructMemberDef(name="temperature", data_type="int16", description="温度値"),
                StructMemberDef(name="humidity", data_type="uint8", description="湿度値"),
                StructMemberDef(name="pressure", data_type="uint16", description="気圧値"),
            ]),
        ]
        
        # ===== 追加: イベントキュー =====
        gd.event_queues = [
            EventQueueDef(
                name="MainEventQueue",
                size=16,
                element_type="EVENT_t",
                event_ids=["POWER_ON", "START", "STOP", "ERROR_DETECTED"],
                priority_enabled=False,
                interrupt_safe=True,
                rtos_enabled=False,
                description="メインイベントキュー"
            ),
            EventQueueDef(
                name="HighPriorityQueue",
                size=8,
                element_type="EVENT_t",
                event_ids=["ERROR_DETECTED"],
                priority_enabled=True,
                interrupt_safe=True,
                rtos_enabled=False,
                description="高優先度イベントキュー"
            ),
        ]
        
        # ===== 追加: 割り込み処理 =====
        gd.interrupts = [
            InterruptHandlerDef(
                name="UART_RX",
                description="UART受信割り込み",
                event_names=["START", "STOP"],
                is_timer=False,
                actions=[
                    InterruptAction(condition="", action="EVT_START_REQ = 1"),
                    InterruptAction(condition="ctx->data.battery_voltage > 3000", action="EVT_STOP_REQ = 1"),
                ]
            ),
            InterruptHandlerDef(
                name="TimerTick",
                description="タイマ割り込み",
                event_names=[],
                is_timer=True,
                actions=[
                    InterruptAction(condition="", action="ctx->data.system_tick++"),
                ]
            ),
        ]
        
        # ===== 追加: デバイスリソース =====
        gd.placeholders = [
            DevicePlaceholderDef(name="UART0", description="UART通信ポート"),
            DevicePlaceholderDef(name="ADC0", description="ADコンバータ"),
        ]
        
        # ===== 追加: タイマ設定 =====
        gd.timer_base = TimerBaseDef(
            variable_name="g_system_tick",
            unit="1ms",
            data_type="volatile uint32_t",
            interrupt_name="TimerTick",
            derived=[
                TimerDerivedDef(period_name="10ms", multiplier=10, variable_name="g_tick_10ms", data_type="uint8_t"),
                TimerDerivedDef(period_name="100ms", multiplier=100, variable_name="g_tick_100ms", data_type="uint8_t"),
            ]
        )
        
        gd.extra_timers = [
            TimerBaseDef(
                variable_name="g_high_speed_tick",
                unit="100us",
                data_type="volatile uint32_t",
                interrupt_name="HighSpeedTimerTick",
                derived=[
                    TimerDerivedDef(period_name="1ms", multiplier=10, variable_name="g_hs_tick_1ms", data_type="uint16_t"),
                ]
            ),
        ]
        
        self.global_defs = gd
        return gd
    
    def get_sample_data(self):
        if self.state_machine is None:
            self.create_sample_state_machine()
        if self.global_defs is None:
            self.create_sample_global_defs()
        return self.state_machine, self.global_defs


_sample_data_instance = None

def get_sample_data_instance():
    global _sample_data_instance
    if _sample_data_instance is None:
        _sample_data_instance = SampleDataGenerator()
    return _sample_data_instance

def get_sample_state_machine():
    return get_sample_data_instance().create_sample_state_machine()

def get_sample_global_defs():
    return get_sample_data_instance().create_sample_global_defs()

def get_sample_data():
    return get_sample_data_instance().get_sample_data()