"""Sample data generation (business logic layer)"""

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

    sm.add_state(State("Idle", entry="Idle_entry", description="Initial state"))
    sm.add_state(State("Active", do="Active_do", description="Running"))
    sm.add_state(State("Error", entry="Error_entry", exit="Error_exit", description="ErrorState"))
    sm.add_state(State("Halt", type=StateType.FINAL, description="Stopped state"))

    sm.add_event(Event(name="START", id=1, description="Startup request",
                       delivery_type=EventDeliveryType.DIRECT,
                       source_layer=EventSourceLayer.MIDDLEWARE,
                       title="Startup request"))
    sm.add_event(Event(name="STOP", id=2, description="Stop request",
                       delivery_type=EventDeliveryType.DIRECT,
                       source_layer=EventSourceLayer.MIDDLEWARE,
                       title="Stop request"))
    sm.add_event(Event(name="ERROR", id=3, description="Error通知",
                       delivery_type=EventDeliveryType.QUEUE,
                       source_layer=EventSourceLayer.DRIVER,
                       data_type="uint8_t", data_name="err_code",
                       title="Error通知"))
    sm.add_event(Event(name="TIMER0_OVERFLOW", id=4, description="1msTimer満了",
                       delivery_type=EventDeliveryType.DOUBLE,
                       source_layer=EventSourceLayer.DRIVER,
                       title="Timer満了"))
    sm.add_event(Event(name="", id=0, kind=EventKind.SIGNAL, description="Completion transition",
                       delivery_type=EventDeliveryType.DIRECT,
                       source_layer=EventSourceLayer.MIDDLEWARE,
                       title="Completion transition"))

    sm.set_initial("Idle")

    # ==================================================================
    # [v1.5 fix] Root fix for Transition positional arg bug
    # ==================================================================
    sm.add_transition(Transition(
        source="Idle",
        event="START",
        condition="",
        pre_actions=["init()"],
        target="Active",
        title="Startup",
    ))
    sm.add_transition(Transition(
        source="Active",
        event="STOP",
        condition="",
        pre_actions=["stop()"],
        target="Idle",
        title="Stop",
    ))
    sm.add_transition(Transition(
        source="Active",
        event="ERROR",
        condition="err_code != 0",
        pre_actions=["log()"],
        target="Error",
        title="Errorへ",
    ))
    sm.add_transition(Transition(
        source="Error",
        event="",
        condition="retry_count < 3",
        pre_actions=["retry_count++"],
        target="Active",
        title="Retry",
    ))
    sm.add_transition(Transition(
        source="Error",
        event="",
        condition="retry_count >= 3",
        pre_actions=[],
        target="Halt",
        title="To stop",
    ))
    sm.add_transition(Transition(
        source="Active",
        event="ERROR",
        condition="err_code == 0",
        pre_actions=["ignore()"],
        target="Active",
        title="Ignore",
    ))

    sm.add_role_function(RoleFunction(
        name="Sensor_Init",
        namespace="",
        description="Sensor initialization",
        return_type="int",
        arg1_type="uint8_t",
        arg1_name="channel",
        arg2_type="uint32_t",
        arg2_name="timeout_ms",
        title="Sensor initialization",
    ))
    sm.add_role_function(RoleFunction(
        name="Error_Log",
        namespace="",
        description="Errorログ出力",
        return_type="void",
        arg1_type="int",
        arg1_name="err_code",
        arg2_type="int",
        arg2_name="level",
        title="Errorログ出力",
    ))

    return sm


def create_sample_global_defs() -> GlobalDefinitions:
    defs = GlobalDefinitions()

    # ユーザー定義Type（Struct＋ビットフィールド＋Array）
    defs.custom_types.append(CustomTypeDef(
        name="SystemStatus_t",
        description="System status struct",
        title="System status",
        members=[
            StructMemberDef(name="power_on", data_type="uint8_t", bit_width=1,
                            description="Power ON flag", title="Power ON"),
            StructMemberDef(name="mode", data_type="uint8_t", bit_width=3,
                            description="Mode", title="Mode"),
            StructMemberDef(name="status", data_type="uint8_t", bit_width=4,
                            description="Status", title="Status"),
        ]
    ))

    defs.custom_types.append(CustomTypeDef(
        name="DataPacket_t",
        description="Data packet struct",
        title="Data packet",
        members=[
            StructMemberDef(name="data", data_type="uint8_t",
                            description="データArray", title="データArray",
                            array_size=64),
            StructMemberDef(name="length", data_type="uint16_t",
                            description="Data length", title="Data length"),
        ]
    ))

    # Global variables（ArrayCorresponds）
    defs.variables.append(SystemVariable(name="battery_voltage", type="uint16_t", unit="mV",
                                         default_value="0", group="Power",
                                         description="Battery voltage", title="Battery voltage"))
    defs.variables.append(SystemVariable(name="payload", type="uint8_t", unit="bytes",
                                         default_value="", group="Communication",
                                         description="Receive data buffer", title="Receive buffer",
                                         array_size=64))
    defs.variables.append(SystemVariable(name="system_status", type="SystemStatus_t",
                                         group="System", description="System status",
                                         title="System status"))

    defs.flags.append(EventFlag(name="EVT_START_REQ", min_value=0, max_value=1,
                                group="SystemEvents", description="Startup request",
                                title="Startup request flag"))
    defs.flags.append(EventFlag(name="EVT_MODE", min_value=0, max_value=3,
                                group="SystemEvents", description="Mode indication",
                                title="Mode indication flag"))

    defs.interrupts.append(InterruptHandlerDef(
        name="TIMER0", description="1ms周期Timer",
        event_names=["TIMER0_OVERFLOW"], is_timer=True,
        actions=[
            InterruptAction(condition="g_tick_100ms >= 5", action="StateMachine_EnqueueEvent(EVENT_TICK);"),
            InterruptAction(condition="", action="g_system_tick++;\nUpdateDerivedTimers();"),
        ],
        title="Timer0Interrupt"
    ))

    defs.placeholders.append(DevicePlaceholderDef(name="TIMER0_IRQ_FLAG",
                                                  description="Timer0InterruptFlagClear用レジスタ",
                                                  title="Timer0 IRQFlag"))

    defs.timer_base = TimerBaseDef(
        variable_name="g_system_tick", unit="1ms", data_type="volatile uint32_t",
        derived=[
            TimerDerivedDef(period_name="10ms", multiplier=10, variable_name="g_tick_10ms",
                            data_type="uint8_t", title="10msTimer"),
            TimerDerivedDef(period_name="100ms", multiplier=100, variable_name="g_tick_100ms",
                            data_type="uint8_t", title="100msTimer"),
            TimerDerivedDef(period_name="1s", multiplier=1000, variable_name="g_tick_1s",
                            data_type="uint16_t", title="1sTimer"),
        ],
        title="システムTimer基準",
        interrupt_name="TIMER0"
    )

    defs.extra_timers.append(TimerBaseDef(
        variable_name="g_high_speed_tick", unit="100us", data_type="volatile uint32_t",
        derived=[
            TimerDerivedDef(period_name="1ms", multiplier=10, variable_name="g_hs_1ms",
                            data_type="uint16_t", title="高速1msTimer"),
        ],
        title="高速Timer基準",
        interrupt_name="TIMER1"
    ))

    defs.event_queues.append(EventQueueDef(
        name="UartQueue", size=16, element_type="uint8_t",
        event_ids=["ERROR"], priority_enabled=False,
        interrupt_safe=True, rtos_enabled=False,
        description="UART receive queue", title="UART receive queue"
    ))

    # TimerVariableをGlobal variablesとして自動登録
    defs.add_timer_variables()

    return defs