"""Sample data generation (business logic layer)."""

from .model import (
    State, Event, Transition, StateType, EventKind,
    RoleFunction, EventDeliveryType, EventSourceLayer,
    ActionStep, TransitionRelation,
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

    # ==================================================================
    # States (v2.2: entry / exit are List[str])
    # ==================================================================
    sm.add_state(State("Idle",
                       entry=["Idle_Entry"],
                       description="Initial state"))
    sm.add_state(State("Active",
                       do="Active_Do",
                       description="Running"))
    sm.add_state(State("Error",
                       entry=["Error_Entry"],
                       exit=["Error_Exit"],
                       description="Error state"))
    sm.add_state(State("Halt",
                       type=StateType.FINAL,
                       description="Stopped state"))

    sm.set_initial("Idle")

    # ==================================================================
    # Events
    # ==================================================================
    sm.add_event(Event(name="START", id=1, description="Startup request",
                       delivery_type=EventDeliveryType.DIRECT,
                       source_layer=EventSourceLayer.MIDDLEWARE,
                       title="Startup request"))
    sm.add_event(Event(name="STOP", id=2, description="Stop request",
                       delivery_type=EventDeliveryType.DIRECT,
                       source_layer=EventSourceLayer.MIDDLEWARE,
                       title="Stop request"))
    sm.add_event(Event(name="ERROR", id=3, description="Error notification",
                       delivery_type=EventDeliveryType.QUEUE,
                       source_layer=EventSourceLayer.DRIVER,
                       data_type="uint8_t", data_name="err_code",
                       title="Error notification"))
    sm.add_event(Event(name="TIMER0_OVERFLOW", id=4,
                       description="1ms timer expired",
                       delivery_type=EventDeliveryType.DOUBLE,
                       source_layer=EventSourceLayer.DRIVER,
                       title="Timer expired"))
    sm.add_event(Event(name="", id=0, kind=EventKind.SIGNAL,
                       description="Completion transition",
                       delivery_type=EventDeliveryType.DIRECT,
                       source_layer=EventSourceLayer.MIDDLEWARE,
                       title="Completion transition"))

    # ==================================================================
    # Role functions (all valid identifiers)
    # ==================================================================
    sm.add_role_function(RoleFunction(
        name="Sensor_Init",
        namespace="",
        description="Sensor initialization",
        return_type="int",
        arg1_type="uint8_t", arg1_name="channel",
        arg2_type="uint32_t", arg2_name="timeout_ms",
        title="Sensor initialization",
    ))
    sm.add_role_function(RoleFunction(
        name="Error_Log",
        namespace="",
        description="Error log output",
        return_type="void",
        arg1_type="int", arg1_name="err_code",
        arg2_type="int", arg2_name="level",
        title="Error log output",
    ))
    sm.add_role_function(RoleFunction(
        name="Start_Init",
        namespace="",
        description="Startup initialization",
        return_type="void",
        title="Startup initialization",
    ))
    sm.add_role_function(RoleFunction(
        name="Stop_Cleanup",
        namespace="",
        description="Stop cleanup",
        return_type="void",
        title="Stop cleanup",
    ))
    sm.add_role_function(RoleFunction(
        name="Retry_Increment",
        namespace="",
        description="Increment retry counter",
        return_type="void",
        title="Increment retry counter",
    ))
    sm.add_role_function(RoleFunction(
        name="Ignore_Event",
        namespace="",
        description="Ignore the current event",
        return_type="void",
        title="Ignore the current event",
    ))
    sm.add_role_function(RoleFunction(
        name="Idle_Entry",
        namespace="",
        description="Idle state entry action",
        return_type="void",
        title="Idle entry",
    ))
    sm.add_role_function(RoleFunction(
        name="Error_Entry",
        namespace="",
        description="Error state entry action",
        return_type="void",
        title="Error entry",
    ))
    sm.add_role_function(RoleFunction(
        name="Error_Exit",
        namespace="",
        description="Error state exit action",
        return_type="void",
        title="Error exit",
    ))

    # ==================================================================
    # Transitions
    # ==================================================================

    # Idle --START--> Active
    sm.add_transition(Transition(
        source="Idle",
        event="START",
        condition="",
        pre_actions=["Start_Init"],
        target="Active",
        has_else=False,
        early_return=True,
        label="T1",
        title="Startup",
    ))

    # Active --STOP--> Idle
    sm.add_transition(Transition(
        source="Active",
        event="STOP",
        condition="",
        pre_actions=["Stop_Cleanup"],
        target="Idle",
        has_else=False,
        early_return=True,
        label="T1",
        title="Stop",
    ))

    # Active --ERROR--> Error (err_code != 0)
    sm.add_transition(Transition(
        source="Active",
        event="ERROR",
        condition="err_code != 0",
        pre_actions=["Error_Log"],
        target="Error",
        has_else=False,
        early_return=True,
        label="T1",
        title="To error",
    ))

    # Active --ERROR--> Active (err_code == 0)  [Tentative]
    sm.add_transition(Transition(
        source="Active",
        event="ERROR",
        condition="err_code == 0",
        pre_actions=["Ignore_Event"],
        target="Active",
        has_else=False,
        early_return=False,
        label="T2",
        title="Ignore",
    ))

    # Error --(Completion)--> Active (retry)
    sm.add_transition(Transition(
        source="Error",
        event="",
        condition="retry_count < 3",
        pre_actions=["Retry_Increment"],
        target="Active",
        has_else=False,
        early_return=True,
        label="T1",
        title="Retry",
    ))

    # Error --(Completion)--> Halt (give up)
    sm.add_transition(Transition(
        source="Error",
        event="",
        condition="retry_count >= 3",
        pre_actions=[],
        target="Halt",
        has_else=False,
        early_return=True,
        label="T2",
        title="Give up",
    ))

    # ==================================================================
    # Cell actions (v2.2)
    # ==================================================================

    # Idle + START: sensor init before condition check
    sm.set_actions_for_cell("Idle", "START", [
        ActionStep(role_function="Sensor_Init",
                   trigger="before_transitions",
                   title="Initialize sensor on startup"),
    ])

    # Active + ERROR: log before and after
    sm.set_actions_for_cell("Active", "ERROR", [
        ActionStep(role_function="Error_Log",
                   trigger="before_transitions",
                   title="Log before evaluating error"),
        ActionStep(role_function="Error_Log",
                   trigger="after_transitions",
                   title="Log after evaluating error"),
    ])

    # Error + (Completion): log before retry evaluation
    sm.set_actions_for_cell("Error", "", [
        ActionStep(role_function="Error_Log",
                   trigger="before_transitions",
                   title="Log before retry evaluation"),
    ])

    # Active + STOP: cleanup after stop
    sm.set_actions_for_cell("Active", "STOP", [
        ActionStep(role_function="Stop_Cleanup",
                   trigger="after_transitions",
                   title="Cleanup after stop"),
    ])

    # ==================================================================
    # Cell relations (v2.2)
    # ==================================================================

    # Active + ERROR: T1 and T2 evaluated sequentially
    sm.set_relations_for_cell("Active", "ERROR", [
        TransitionRelation(
            kind="sequential",
            members=["T1", "T2"],
            shared_condition="",
            note="T1 (error) first, then T2 (ignore)",
        ),
    ])

    # Error + (Completion): T1 and T2 mutually exclusive
    sm.set_relations_for_cell("Error", "", [
        TransitionRelation(
            kind="exclusive",
            members=["T1", "T2"],
            shared_condition="",
            note="At most one fires (retry or halt)",
        ),
    ])

    return sm


def create_sample_global_defs() -> GlobalDefinitions:
    defs = GlobalDefinitions()

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
                            description="Data array", title="Data array",
                            array_size=64),
            StructMemberDef(name="length", data_type="uint16_t",
                            description="Data length", title="Data length"),
        ]
    ))

    defs.variables.append(SystemVariable(
        name="battery_voltage", type="uint16_t", unit="mV",
        default_value="0", group="Power",
        description="Battery voltage", title="Battery voltage"))
    defs.variables.append(SystemVariable(
        name="payload", type="uint8_t", unit="bytes",
        default_value="", group="Communication",
        description="Receive data buffer", title="Receive buffer",
        array_size=64))
    defs.variables.append(SystemVariable(
        name="system_status", type="SystemStatus_t",
        group="System", description="System status",
        title="System status"))
    defs.variables.append(SystemVariable(
        name="retry_count", type="uint8_t", unit="",
        default_value="0", group="Error",
        description="Retry counter", title="Retry counter"))

    defs.flags.append(EventFlag(
        name="EVT_START_REQ", min_value=0, max_value=1,
        group="SystemEvents", description="Startup request",
        title="Startup request flag"))
    defs.flags.append(EventFlag(
        name="EVT_MODE", min_value=0, max_value=3,
        group="SystemEvents", description="Mode indication",
        title="Mode indication flag"))

    defs.interrupts.append(InterruptHandlerDef(
        name="TIMER0", description="1ms period timer",
        event_names=["TIMER0_OVERFLOW"], is_timer=True,
        actions=[
            InterruptAction(condition="g_tick_100ms >= 5",
                            action="StateMachine_EnqueueEvent(EVENT_TICK);"),
            InterruptAction(condition="",
                            action="g_system_tick++;\nUpdateDerivedTimers();"),
        ],
        title="Timer0Interrupt"
    ))

    defs.placeholders.append(DevicePlaceholderDef(
        name="TIMER0_IRQ_FLAG",
        description="Timer0 interrupt flag clear register",
        title="Timer0 IRQFlag"))

    defs.timer_base = TimerBaseDef(
        variable_name="g_system_tick", unit="1ms",
        data_type="volatile uint32_t",
        derived=[
            TimerDerivedDef(period_name="10ms", multiplier=10,
                            variable_name="g_tick_10ms",
                            data_type="uint8_t", title="10msTimer"),
            TimerDerivedDef(period_name="100ms", multiplier=100,
                            variable_name="g_tick_100ms",
                            data_type="uint8_t", title="100msTimer"),
            TimerDerivedDef(period_name="1s", multiplier=1000,
                            variable_name="g_tick_1s",
                            data_type="uint16_t", title="1sTimer"),
        ],
        title="System timer base",
        interrupt_name="TIMER0"
    )

    defs.extra_timers.append(TimerBaseDef(
        variable_name="g_high_speed_tick", unit="100us",
        data_type="volatile uint32_t",
        derived=[
            TimerDerivedDef(period_name="1ms", multiplier=10,
                            variable_name="g_hs_1ms",
                            data_type="uint16_t",
                            title="High-speed 1ms timer"),
        ],
        title="High-speed timer base",
        interrupt_name="TIMER1"
    ))

    defs.event_queues.append(EventQueueDef(
        name="UartQueue", size=16, element_type="uint8_t",
        event_ids=["ERROR"], priority_enabled=False,
        interrupt_safe=True, rtos_enabled=False,
        description="UART receive queue", title="UART receive queue"
    ))

    defs.add_timer_variables()

    return defs