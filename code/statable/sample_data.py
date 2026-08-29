"""サンプルデータ生成（ビジネスロジック層）"""

from .model import (
    State, Event, Transition, StateType, EventKind,
    RoleFunction, EventDeliveryType, EventSourceLayer,
)
from .state_machine import StateMachine
from .global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    InterruptHandlerDef, InterruptAction,
    DevicePlaceholderDef, TimerBaseDef, TimerDerivedDef,
    EventQueueDef,
)


def create_sample_state_machine() -> StateMachine:
    """サンプルの状態遷移マシンを作成する"""
    sm = StateMachine()

    # 状態定義
    sm.add_state(State("Idle", entry="Idle_entry", description="初期状態"))
    sm.add_state(State("Active", do="Active_do", description="動作中"))
    sm.add_state(State("Error", entry="Error_entry", exit="Error_exit", description="エラー状態"))
    sm.add_state(State("Halt", type=StateType.FINAL, description="停止状態"))

    # 状態遷移イベント定義
    sm.add_event(Event(
        name="START",
        id=1,
        description="起動要求",
        delivery_type=EventDeliveryType.DIRECT,
        source_layer=EventSourceLayer.MIDDLEWARE,
    ))
    sm.add_event(Event(
        name="STOP",
        id=2,
        description="停止要求",
        delivery_type=EventDeliveryType.DIRECT,
        source_layer=EventSourceLayer.MIDDLEWARE,
    ))
    sm.add_event(Event(
        name="ERROR",
        id=3,
        description="エラー通知",
        delivery_type=EventDeliveryType.QUEUE,
        source_layer=EventSourceLayer.DRIVER,
        data_type="uint8_t",
        data_name="err_code",
    ))
    sm.add_event(Event(
        name="TIMER0_OVERFLOW",
        id=4,
        description="1msタイマ満了",
        delivery_type=EventDeliveryType.DOUBLE,
        source_layer=EventSourceLayer.DRIVER,
    ))
    sm.add_event(Event(
        name="",
        id=0,
        kind=EventKind.SIGNAL,
        description="完了遷移",
        delivery_type=EventDeliveryType.DIRECT,
        source_layer=EventSourceLayer.MIDDLEWARE,
    ))

    # 初期状態
    sm.set_initial("Idle")

    # 遷移定義（状態遷移条件を condition で記述）
    sm.add_transition(Transition("Idle", "START", "", "init()", "Active"))
    sm.add_transition(Transition("Active", "STOP", "", "stop()", "Idle"))
    sm.add_transition(Transition("Active", "ERROR", "err_code != 0", "log()", "Error"))
    sm.add_transition(Transition("Error", "", "retry_count < 3", "retry_count++", "Active"))
    sm.add_transition(Transition("Error", "", "retry_count >= 3", "", "Halt"))
    sm.add_transition(Transition("Active", "ERROR", "err_code == 0", "ignore()", "Active"))

    # ロール関数
    sm.add_role_function(RoleFunction(
        name="Sensor_Init",
        description="センサ初期化",
        return_type="int",
        arg1_type="uint8_t", arg1_name="channel",
        arg2_type="uint32_t", arg2_name="timeout_ms"
    ))
    sm.add_role_function(RoleFunction(
        name="Error_Log",
        description="エラーログ出力",
        return_type="void",
        arg1_type="int", arg1_name="err_code",
        arg2_type="int", arg2_name="level"
    ))

    return sm


def create_sample_global_defs() -> GlobalDefinitions:
    """サンプルのグローバル変数・イベントフラグ・割り込み・デバイス・タイマ・イベントキュー設定を作成する"""
    defs = GlobalDefinitions()

    # グローバル変数
    defs.variables.append(SystemVariable(
        name="battery_voltage", type="uint16_t", unit="mV",
        default_value="0", group="Power", description="バッテリ電圧"
    ))
    defs.variables.append(SystemVariable(
        name="motor_current", type="int16_t", unit="mA",
        default_value="0", group="Motor", description="モータ電流"
    ))

    # イベントフラグ
    defs.flags.append(EventFlag(
        name="EVT_START_REQ", min_value=0, max_value=1,
        group="SystemEvents", description="起動要求"
    ))
    defs.flags.append(EventFlag(
        name="EVT_MODE", min_value=0, max_value=3,
        group="SystemEvents", description="モード指示"
    ))

    # 割り込み処理（複数イベント対応）
    defs.interrupts.append(InterruptHandlerDef(
        name="TIMER0",
        description="1ms周期タイマ",
        event_names=["TIMER0_OVERFLOW"],
        is_timer=True,
        actions=[
            InterruptAction(
                condition="g_tick_100ms >= 5",
                action="StateMachine_EnqueueEvent(EVENT_TICK);"
            ),
            InterruptAction(
                condition="",
                action="g_system_tick++;\nUpdateDerivedTimers();"
            ),
        ]
    ))

    # デバイスリソース仮定義
    defs.placeholders.append(DevicePlaceholderDef(
        name="TIMER0_IRQ_FLAG",
        description="タイマ0割り込みフラグクリア用レジスタ"
    ))

    # タイマ設定
    defs.timer_base = TimerBaseDef(
        variable_name="g_system_tick",
        unit="1ms",
        data_type="volatile uint32_t",
        derived=[
            TimerDerivedDef(period_name="10ms", multiplier=10, variable_name="g_tick_10ms", data_type="uint8_t"),
            TimerDerivedDef(period_name="100ms", multiplier=100, variable_name="g_tick_100ms", data_type="uint8_t"),
            TimerDerivedDef(period_name="1s", multiplier=1000, variable_name="g_tick_1s", data_type="uint16_t"),
        ]
    )

    # イベントキュー定義（イベントIDと関連付け）
    defs.event_queues.append(EventQueueDef(
        name="UartQueue",
        size=16,
        element_type="uint8_t",
        event_ids=["ERROR"],
        priority_enabled=False,
        interrupt_safe=True,
        rtos_enabled=False,
        description="UART受信キュー"
    ))

    # タイマ変数をグローバル変数として自動登録
    defs.add_timer_variables()

    return defs