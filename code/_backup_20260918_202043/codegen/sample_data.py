# codegen/sample_data.py
"""
Sample data for code generation tests.
Provides test data independent of the GUI.

[v1.5 fix]
  - Transition action= migrated to pre_actions=[] (bug #87)
    The action field is defined as "compat / unused" in v1.4 sec 2.2,
    and role_function_generator only references pre_actions,
    so action= does not reflect calls in code generation.
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
    """Sample data generator class"""

    def __init__(self):
        self.state_machine = None
        self.global_defs = None

    def create_sample_state_machine(self):
        sm = StateMachine()

        sm.add_state(State(name="INIT", type=StateType.INITIAL, description="Initial state"))
        sm.add_state(State(name="IDLE", type=StateType.NORMAL, description="Idle state"))
        sm.add_state(State(name="RUNNING", type=StateType.NORMAL, description="Running state"))
        sm.add_state(State(name="ERROR", type=StateType.NORMAL, description="Error state"))
        sm.set_initial("INIT")

        sm.add_event(Event(name="POWER_ON", kind=EventKind.SIGNAL, description="Power-on event"))
        sm.add_event(Event(name="START", kind=EventKind.SIGNAL, description="Start event"))
        sm.add_event(Event(name="STOP", kind=EventKind.SIGNAL, description="Stop event"))
        sm.add_event(Event(name="ERROR_DETECTED", kind=EventKind.SIGNAL, description="Error detected event"))

        # ==============================================================
        # [v1.5 fix] action= -> pre_actions=[]
        # ==============================================================
        sm.add_transition(Transition(
            source="INIT",
            event="POWER_ON",
            target="IDLE",
            pre_actions=["PowerOn"],
            title="Power on",
        ))
        sm.add_transition(Transition(
            source="IDLE",
            event="START",
            target="RUNNING",
            condition="StartOk",
            pre_actions=["Start"],
            title="Start",
        ))
        sm.add_transition(Transition(
            source="RUNNING",
            event="STOP",
            target="IDLE",
            pre_actions=["Stop"],
            title="Stop",
        ))
        sm.add_transition(Transition(
            source="RUNNING",
            event="ERROR_DETECTED",
            target="ERROR",
            pre_actions=["HandleError"],
            title="Error handling",
        ))

        sm.add_role_function(RoleFunction(
            name="PowerOn", return_type="void",
            description="Power-on processing",
        ))
        sm.add_role_function(RoleFunction(
            name="StartOk", return_type="bool",
            description="Start condition check",
        ))
        sm.add_role_function(RoleFunction(
            name="Start", return_type="void",
            description="Start processing",
        ))
        sm.add_role_function(RoleFunction(
            name="Stop", return_type="void",
            description="Stop processing",
        ))
        sm.add_role_function(RoleFunction(
            name="HandleError", return_type="void",
            description="Error handling",
        ))
        sm.add_role_function(RoleFunction(
            name="ProcessData", return_type="int",
            arg1_type="uint8_t*", arg1_name="data",
            arg2_type="uint16_t", arg2_name="len",
            description="Data processing",
        ))

        self.state_machine = sm
        return sm

    def create_sample_global_defs(self):
        gd = GlobalDefinitions()

        gd.variables = [
            SystemVariable(name="battery_voltage", type="uint16", unit="mV",
                           group="Power", description="Battery voltage"),
            SystemVariable(name="system_tick", type="uint32", unit="ms",
                           group="Timer", description="System timer"),
            SystemVariable(name="temperature", type="int16", unit="0.1C",
                           group="Sensor", description="Temperature sensor value"),
            SystemVariable(name="data_buffer", type="uint8",
                           group="Data", description="Data buffer",
                           array_size=64),
        ]

        gd.flags = [
            EventFlag(name="EVT_POWER_ON_REQ", min_value=0, max_value=1,
                      group="System", description="Power-on request"),
            EventFlag(name="EVT_START_REQ", min_value=0, max_value=1,
                      group="System", description="Start request"),
            EventFlag(name="EVT_STOP_REQ", min_value=0, max_value=1,
                      group="System", description="Stop request"),
            EventFlag(name="EVT_ERROR_FLAG", min_value=0, max_value=1,
                      group="Error", description="Error flag"),
        ]

        gd.custom_types = [
            CustomTypeDef(name="SystemStatus", description="System status management struct", members=[
                StructMemberDef(name="power_on", data_type="bool", bit_width=1,
                                description="Power-on state"),
                StructMemberDef(name="initialized", data_type="bool", bit_width=1,
                                description="Initialization completed flag"),
                StructMemberDef(name="error_code", data_type="uint8",
                                description="Error code"),
                StructMemberDef(name="mode", data_type="uint8",
                                description="Operation mode"),
            ]),
            CustomTypeDef(name="SensorData", description="Sensor data struct", members=[
                StructMemberDef(name="temperature", data_type="int16",
                                description="Temperature value"),
                StructMemberDef(name="humidity", data_type="uint8",
                                description="Humidity value"),
                StructMemberDef(name="pressure", data_type="uint16",
                                description="Pressure value"),
            ]),
        ]

        gd.event_queues = [
            EventQueueDef(
                name="MainEventQueue",
                size=16,
                element_type="EVENT_t",
                event_ids=["POWER_ON", "START", "STOP", "ERROR_DETECTED"],
                priority_enabled=False,
                interrupt_safe=True,
                rtos_enabled=False,
                description="Main event queue",
            ),
            EventQueueDef(
                name="HighPriorityQueue",
                size=8,
                element_type="EVENT_t",
                event_ids=["ERROR_DETECTED"],
                priority_enabled=True,
                interrupt_safe=True,
                rtos_enabled=False,
                description="High-priority event queue",
            ),
        ]

        gd.interrupts = [
            InterruptHandlerDef(
                name="UART_RX",
                description="UART receive interrupt",
                event_names=["START", "STOP"],
                is_timer=False,
                actions=[
                    InterruptAction(condition="", action="EVT_START_REQ = 1"),
                    InterruptAction(
                        condition="ctx->data.battery_voltage > 3000",
                        action="EVT_STOP_REQ = 1",
                    ),
                ],
            ),
            InterruptHandlerDef(
                name="TimerTick",
                description="Timer interrupt",
                event_names=[],
                is_timer=True,
                actions=[
                    InterruptAction(condition="", action="ctx->data.system_tick++"),
                ],
            ),
        ]

        gd.placeholders = [
            DevicePlaceholderDef(name="UART0", description="UART communication port"),
            DevicePlaceholderDef(name="ADC0", description="AD converter"),
        ]

        gd.timer_base = TimerBaseDef(
            variable_name="g_system_tick",
            unit="1ms",
            data_type="volatile uint32_t",
            interrupt_name="TimerTick",
            derived=[
                TimerDerivedDef(period_name="10ms", multiplier=10,
                                variable_name="g_tick_10ms", data_type="uint8_t"),
                TimerDerivedDef(period_name="100ms", multiplier=100,
                                variable_name="g_tick_100ms", data_type="uint8_t"),
            ],
        )

        gd.extra_timers = [
            TimerBaseDef(
                variable_name="g_high_speed_tick",
                unit="100us",
                data_type="volatile uint32_t",
                interrupt_name="HighSpeedTimerTick",
                derived=[
                    TimerDerivedDef(period_name="1ms", multiplier=10,
                                    variable_name="g_hs_tick_1ms",
                                    data_type="uint16_t"),
                ],
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