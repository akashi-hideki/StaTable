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
    EventQueueDef, CustomTypeDef, StructMemberDef,
)


def create_sample_state_machine() -> StateMachine:
    sm = StateMachine()

    sm.add_state(State("Idle", entry="Idle_entry", description="初期状態"))
    sm.add_state(State("Active", do="Active_do", description="動作中"))
    sm.add_state(State("Error", entry="Error_entry", exit="Error_exit", description="エラー状態"))
    sm.add_state(State("Halt", type=StateType.FINAL, description="停止状態"))

    sm.add_event(Event(name="START", id=1, description="起動要求",
                       delivery_type=EventDeliveryType.DIRECT,
                       source_layer=EventSourceLayer.MIDDLEWARE,
                       title="起動要求"))
    sm.add_event(Event(name="STOP", id=2, description="停止要求",
                       delivery_type=EventDeliveryType.DIRECT,
                       source_layer=EventSourceLayer.MIDDLEWARE,
                       title="停止要求"))
    sm.add_event(Event(name="ERROR", id=3, description="エラー通知",
                       delivery_type=EventDeliveryType.QUEUE,
                       source_layer=EventSourceLayer.DRIVER,
                       data_type="uint8_t", data_name="err_code",
                       title="エラー通知"))
    sm.add_event(Event(name="TIMER0_OVERFLOW", id=4, description="1msタイマ満了",
                       delivery_type=EventDeliveryType.DOUBLE,
                       source_layer=EventSourceLayer.DRIVER,
                       title="タイマ満了"))
    sm.add_event(Event(name="", id=0, kind=EventKind.SIGNAL, description="完了遷移",
                       delivery_type=EventDeliveryType.DIRECT,
                       source_layer=EventSourceLayer.MIDDLEWARE,
                       title="完了遷移"))

    sm.set_initial("Idle")

    # ==================================================================
    # 【v1.5 修正】Transition 位置引数バグの根本修正（v1.4 §9.6 #67）
    #
    # 旧コード（v1.4 まで）:
    #   Transition("Idle", "START", "", "init()", "Active", title="起動")
    #     → 4 番目の "init()" が pre_actions（List[str]）に文字列で渡され、
    #       XML 保存時に 1 文字ずつ分解されるバグの原因。
    #
    # 新コード（v1.5）:
    #   全 kwarg + pre_actions を List[str] で明示。
    #   model.py の Transition は将来 kw_only 化予定のため、
    #   ここで kwarg 化しておくことで移行が安全になる。
    # ==================================================================
    sm.add_transition(Transition(
        source="Idle",
        event="START",
        condition="",
        pre_actions=["init()"],
        target="Active",
        title="起動",
    ))
    sm.add_transition(Transition(
        source="Active",
        event="STOP",
        condition="",
        pre_actions=["stop()"],
        target="Idle",
        title="停止",
    ))
    sm.add_transition(Transition(
        source="Active",
        event="ERROR",
        condition="err_code != 0",
        pre_actions=["log()"],
        target="Error",
        title="エラーへ",
    ))
    sm.add_transition(Transition(
        source="Error",
        event="",
        condition="retry_count < 3",
        pre_actions=["retry_count++"],
        target="Active",
        title="リトライ",
    ))
    sm.add_transition(Transition(
        source="Error",
        event="",
        condition="retry_count >= 3",
        pre_actions=[],
        target="Halt",
        title="停止へ",
    ))
    sm.add_transition(Transition(
        source="Active",
        event="ERROR",
        condition="err_code == 0",
        pre_actions=["ignore()"],
        target="Active",
        title="無視",
    ))

    sm.add_role_function(RoleFunction(
        name="Sensor_Init",
        namespace="",                       # ★ 明示（kw_only 対応）
        description="センサ初期化",
        return_type="int",
        arg1_type="uint8_t",
        arg1_name="channel",
        arg2_type="uint32_t",
        arg2_name="timeout_ms",
        title="センサ初期化",
    ))
    sm.add_role_function(RoleFunction(
        name="Error_Log",
        namespace="",
        description="エラーログ出力",
        return_type="void",
        arg1_type="int",
        arg1_name="err_code",
        arg2_type="int",
        arg2_name="level",
        title="エラーログ出力",
    ))

    return sm


def create_sample_global_defs() -> GlobalDefinitions:
    defs = GlobalDefinitions()

    # ユーザー定義型（構造体＋ビットフィールド＋配列）
    defs.custom_types.append(CustomTypeDef(
        name="SystemStatus_t",
        description="システムステータス構造体",
        title="システムステータス",
        members=[
            StructMemberDef(name="power_on", data_type="uint8_t", bit_width=1,
                            description="電源ONフラグ", title="電源ON"),
            StructMemberDef(name="mode", data_type="uint8_t", bit_width=3,
                            description="モード", title="モード"),
            StructMemberDef(name="status", data_type="uint8_t", bit_width=4,
                            description="ステータス", title="ステータス"),
        ]
    ))

    defs.custom_types.append(CustomTypeDef(
        name="DataPacket_t",
        description="データパケット構造体",
        title="データパケット",
        members=[
            StructMemberDef(name="data", data_type="uint8_t",
                            description="データ配列", title="データ配列",
                            array_size=64),
            StructMemberDef(name="length", data_type="uint16_t",
                            description="データ長", title="データ長"),
        ]
    ))

    # グローバル変数（配列対応）
    defs.variables.append(SystemVariable(name="battery_voltage", type="uint16_t", unit="mV",
                                         default_value="0", group="Power",
                                         description="バッテリ電圧", title="バッテリ電圧"))
    defs.variables.append(SystemVariable(name="payload", type="uint8_t", unit="bytes",
                                         default_value="", group="Communication",
                                         description="受信データバッファ", title="受信バッファ",
                                         array_size=64))
    defs.variables.append(SystemVariable(name="system_status", type="SystemStatus_t",
                                         group="System", description="システムステータス",
                                         title="システムステータス"))

    defs.flags.append(EventFlag(name="EVT_START_REQ", min_value=0, max_value=1,
                                group="SystemEvents", description="起動要求",
                                title="起動要求フラグ"))
    defs.flags.append(EventFlag(name="EVT_MODE", min_value=0, max_value=3,
                                group="SystemEvents", description="モード指示",
                                title="モード指示フラグ"))

    defs.interrupts.append(InterruptHandlerDef(
        name="TIMER0", description="1ms周期タイマ",
        event_names=["TIMER0_OVERFLOW"], is_timer=True,
        actions=[
            InterruptAction(condition="g_tick_100ms >= 5", action="StateMachine_EnqueueEvent(EVENT_TICK);"),
            InterruptAction(condition="", action="g_system_tick++;\nUpdateDerivedTimers();"),
        ],
        title="タイマ0割り込み"
    ))

    defs.placeholders.append(DevicePlaceholderDef(name="TIMER0_IRQ_FLAG",
                                                  description="タイマ0割り込みフラグクリア用レジスタ",
                                                  title="タイマ0 IRQフラグ"))

    defs.timer_base = TimerBaseDef(
        variable_name="g_system_tick", unit="1ms", data_type="volatile uint32_t",
        derived=[
            TimerDerivedDef(period_name="10ms", multiplier=10, variable_name="g_tick_10ms",
                            data_type="uint8_t", title="10msタイマ"),
            TimerDerivedDef(period_name="100ms", multiplier=100, variable_name="g_tick_100ms",
                            data_type="uint8_t", title="100msタイマ"),
            TimerDerivedDef(period_name="1s", multiplier=1000, variable_name="g_tick_1s",
                            data_type="uint16_t", title="1sタイマ"),
        ],
        title="システムタイマ基準",
        interrupt_name="TIMER0"
    )

    defs.extra_timers.append(TimerBaseDef(
        variable_name="g_high_speed_tick", unit="100us", data_type="volatile uint32_t",
        derived=[
            TimerDerivedDef(period_name="1ms", multiplier=10, variable_name="g_hs_1ms",
                            data_type="uint16_t", title="高速1msタイマ"),
        ],
        title="高速タイマ基準",
        interrupt_name="TIMER1"
    ))

    defs.event_queues.append(EventQueueDef(
        name="UartQueue", size=16, element_type="uint8_t",
        event_ids=["ERROR"], priority_enabled=False,
        interrupt_safe=True, rtos_enabled=False,
        description="UART受信キュー", title="UART受信キュー"
    ))

    # タイマ変数をグローバル変数として自動登録
    defs.add_timer_variables()

    return defs