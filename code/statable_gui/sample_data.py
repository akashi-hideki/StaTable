from statable.model import State, Event, Transition, StateType, EventKind, RoleFunction
from statable.state_machine import StateMachine
from .global_defs import GlobalDefinitions, SystemVariable, EventFlag


def create_sample_state_machine() -> StateMachine:
    sm = StateMachine()
    sm.add_state(State("Idle", entry="Idle_entry", description="初期状態"))
    sm.add_state(State("Active", do="Active_do", description="動作中"))
    sm.add_state(State("Error", entry="Error_entry", exit="Error_exit", description="エラー状態"))
    sm.add_state(State("Halt", type=StateType.FINAL, description="停止状態"))
    sm.add_event(Event("start", id=1, description="起動要求"))
    sm.add_event(Event("stop", id=2, description="停止要求"))
    sm.add_event(Event("error", id=3, params=["uint8_t err_code"], description="エラー通知"))
    sm.add_event(Event("", id=0, kind=EventKind.SIGNAL, description="完了遷移"))
    sm.set_initial("Idle")
    sm.add_transition(Transition("Idle", "start", "", "init()", "Active"))
    sm.add_transition(Transition("Active", "stop", "", "stop()", "Idle"))
    sm.add_transition(Transition("Active", "error", "err_code != 0", "log()", "Error"))
    sm.add_transition(Transition("Error", "", "retry_count < 3", "retry_count++", "Active"))
    sm.add_transition(Transition("Error", "", "retry_count >= 3", "", "Halt"))
    sm.add_transition(Transition("Active", "error", "err_code == 0", "ignore()", "Active"))

    # ロール関数のサンプル
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
    defs = GlobalDefinitions()
    defs.variables.append(SystemVariable(
        name="battery_voltage", type="uint16_t", unit="mV",
        default_value="0", group="Power", description="バッテリ電圧"
    ))
    defs.variables.append(SystemVariable(
        name="motor_current", type="int16_t", unit="mA",
        default_value="0", group="Motor", description="モータ電流"
    ))
    defs.flags.append(EventFlag(
        name="EVT_START_REQ", min_value=0, max_value=1,
        group="SystemEvents", description="起動要求"
    ))
    defs.flags.append(EventFlag(
        name="EVT_MODE", min_value=0, max_value=3,
        group="SystemEvents", description="モード指示"
    ))
    return defs