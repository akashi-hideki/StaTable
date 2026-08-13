from statable.model import State, Event, Transition, StateType, EventKind
from statable.state_machine import StateMachine
from statable.mermaid_gen import generate_mermaid


def main():
    sm = StateMachine()

    # 状態定義
    sm.add_state(State("Idle", entry="init()"))
    sm.add_state(State("Active"))
    sm.add_state(State("Error"))
    sm.add_state(State("Halt", type=StateType.FINAL))

    # イベント辞書
    sm.add_event(Event("start", id=1))
    sm.add_event(Event("stop", id=2))
    sm.add_event(Event("error", id=3, params=["uint8_t err_code"]))

    # 初期状態
    sm.set_initial("Idle")

    # 遷移定義
    sm.add_transition(Transition("Idle", "start", "", "init()", "Active"))
    sm.add_transition(Transition("Active", "stop", "", "stop()", "Idle"))
    sm.add_transition(Transition("Active", "error", "err_code != 0", "log()", "Error"))
    sm.add_transition(Transition("Error", "", "retry_count < 3", "retry_count++", "Active"))
    sm.add_transition(Transition("Error", "", "retry_count >= 3", "", "Halt"))

    # Mermaid生成
    mermaid = generate_mermaid(sm)
    print(mermaid)


if __name__ == "__main__":
    main()