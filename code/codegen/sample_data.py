# codegen/sample_data.py
"""
コード生成テスト用サンプルデータ
GUIとは独立したテストデータを提供する
"""

import sys
import os

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statable.model import State, Event, Transition, StateType, EventKind, RoleFunction
from statable.state_machine import StateMachine
from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    CustomTypeDef, StructMemberDef
)


class SampleDataGenerator:
    """サンプルデータ生成クラス"""
    
    def __init__(self):
        self.state_machine = None
        self.global_defs = None
    
    def create_sample_state_machine(self) -> StateMachine:
        """サンプルステートマシンを作成"""
        sm = StateMachine()
        
        # 状態定義（add_state メソッドを使用）
        sm.add_state(State(name="INIT", type=StateType.INITIAL, 
                          description="初期状態"))
        sm.add_state(State(name="IDLE", type=StateType.NORMAL,
                          description="アイドル状態"))
        sm.add_state(State(name="RUNNING", type=StateType.NORMAL,
                          description="実行状態"))
        sm.add_state(State(name="ERROR", type=StateType.NORMAL,
                          description="エラー状態"))
        
        # 初期状態設定
        sm.set_initial("INIT")
        
        # イベント定義（add_event メソッドを使用）
        sm.add_event(Event(name="POWER_ON", kind=EventKind.SIGNAL,
                          description="電源ONイベント"))
        sm.add_event(Event(name="START", kind=EventKind.SIGNAL,
                          description="開始イベント"))
        sm.add_event(Event(name="STOP", kind=EventKind.SIGNAL,
                          description="停止イベント"))
        sm.add_event(Event(name="ERROR_DETECTED", kind=EventKind.SIGNAL,
                          description="エラー検出イベント"))
        
        # 遷移定義（add_transition メソッドを使用）
        sm.add_transition(Transition(
            source="INIT", event="POWER_ON", target="IDLE",
            action="PowerOn", title="電源ON"
        ))
        sm.add_transition(Transition(
            source="IDLE", event="START", target="RUNNING",
            condition="StartOk", action="Start", title="開始"
        ))
        sm.add_transition(Transition(
            source="RUNNING", event="STOP", target="IDLE",
            action="Stop", title="停止"
        ))
        sm.add_transition(Transition(
            source="RUNNING", event="ERROR_DETECTED", target="ERROR",
            action="HandleError", title="エラー処理"
        ))
        
        # ロール関数定義（add_role_function メソッドを使用）
        sm.add_role_function(RoleFunction(
            name="PowerOn", return_type="void",
            description="電源ON処理"
        ))
        sm.add_role_function(RoleFunction(
            name="StartOk", return_type="bool",
            description="開始条件チェック"
        ))
        sm.add_role_function(RoleFunction(
            name="Start", return_type="void",
            description="開始処理"
        ))
        sm.add_role_function(RoleFunction(
            name="Stop", return_type="void",
            description="停止処理"
        ))
        sm.add_role_function(RoleFunction(
            name="HandleError", return_type="void",
            description="エラー処理"
        ))
        sm.add_role_function(RoleFunction(
            name="ProcessData", return_type="int",
            arg1_type="uint8_t*", arg1_name="data",
            arg2_type="uint16_t", arg2_name="len",
            description="データ処理"
        ))
        
        self.state_machine = sm
        return sm
    
    def create_sample_global_defs(self) -> GlobalDefinitions:
        """サンプルグローバル定義を作成"""
        gd = GlobalDefinitions()
        
        # グローバル変数（直接リストに代入）
        gd.variables = [
            SystemVariable(
                name="battery_voltage", type="uint16", unit="mV",
                group="Power", description="バッテリー電圧"
            ),
            SystemVariable(
                name="system_tick", type="uint32", unit="ms",
                group="Timer", description="システムタイマ"
            ),
            SystemVariable(
                name="temperature", type="int16", unit="0.1℃",
                group="Sensor", description="温度センサ値"
            ),
            SystemVariable(
                name="data_buffer", type="uint8", unit="",
                group="Data", description="データバッファ",
                array_size=64
            ),
        ]
        
        # イベントフラグ（直接リストに代入）
        gd.flags = [
            EventFlag(
                name="EVT_POWER_ON_REQ", min_value=0, max_value=1,
                group="System", description="電源ON要求"
            ),
            EventFlag(
                name="EVT_START_REQ", min_value=0, max_value=1,
                group="System", description="開始要求"
            ),
            EventFlag(
                name="EVT_STOP_REQ", min_value=0, max_value=1,
                group="System", description="停止要求"
            ),
            EventFlag(
                name="EVT_ERROR_FLAG", min_value=0, max_value=1,
                group="Error", description="エラーフラグ"
            ),
        ]
        
        # ユーザー定義型（直接リストに代入）
        gd.custom_types = [
            CustomTypeDef(
                name="SystemStatus", description="システム状態管理構造体",
                members=[
                    StructMemberDef(name="power_on", data_type="bool",
                                  bit_width=1, description="電源ON状態"),
                    StructMemberDef(name="initialized", data_type="bool",
                                  bit_width=1, description="初期化完了フラグ"),
                    StructMemberDef(name="error_code", data_type="uint8",
                                  description="エラーコード"),
                    StructMemberDef(name="mode", data_type="uint8",
                                  description="動作モード"),
                ]
            ),
            CustomTypeDef(
                name="SensorData", description="センサーデータ構造体",
                members=[
                    StructMemberDef(name="temperature", data_type="int16",
                                  description="温度値"),
                    StructMemberDef(name="humidity", data_type="uint8",
                                  description="湿度値"),
                    StructMemberDef(name="pressure", data_type="uint16",
                                  description="気圧値"),
                ]
            ),
        ]
        
        self.global_defs = gd
        return gd
    
    def get_sample_data(self) -> tuple:
        """サンプルデータを取得"""
        if self.state_machine is None:
            self.create_sample_state_machine()
        if self.global_defs is None:
            self.create_sample_global_defs()
        
        return self.state_machine, self.global_defs


# シングルトンインスタンス
_sample_data_instance = None


def get_sample_data_instance() -> SampleDataGenerator:
    """シングルトンインスタンスを取得"""
    global _sample_data_instance
    if _sample_data_instance is None:
        _sample_data_instance = SampleDataGenerator()
    return _sample_data_instance


def get_sample_state_machine() -> StateMachine:
    """サンプルステートマシンを取得"""
    return get_sample_data_instance().create_sample_state_machine()


def get_sample_global_defs() -> GlobalDefinitions:
    """サンプルグローバル定義を取得"""
    return get_sample_data_instance().create_sample_global_defs()


def get_sample_data() -> tuple:
    """サンプルデータを取得"""
    return get_sample_data_instance().get_sample_data()