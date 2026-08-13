import unittest
from statable.model import State, Event, Transition, StateType, EventKind
from statable.state_machine import StateMachine
from statable.mermaid_gen import generate_mermaid


class TestStateMachine(unittest.TestCase):
    def setUp(self):
        self.sm = StateMachine()
        self.sm.add_state(State("Idle", entry="init()"))
        self.sm.add_state(State("Active"))
        self.sm.add_state(State("Error"))
        self.sm.add_state(State("Halt", type=StateType.FINAL))
        self.sm.add_event(Event("start", id=1))
        self.sm.add_event(Event("stop", id=2))
        self.sm.add_event(Event("error", id=3, params=["uint8_t err_code"]))
        self.sm.set_initial("Idle")
        self.sm.add_transition(Transition("Idle", "start", "", "init()", "Active"))
        self.sm.add_transition(Transition("Active", "stop", "", "stop()", "Idle"))
        self.sm.add_transition(Transition("Active", "error", "err_code != 0", "log()", "Error"))
        self.sm.add_transition(Transition("Error", "", "retry_count < 3", "retry_count++", "Active"))
        self.sm.add_transition(Transition("Error", "", "retry_count >= 3", "", "Halt"))

    def test_state_count(self):
        self.assertEqual(len(self.sm.states), 4)

    def test_event_count(self):
        self.assertEqual(len(self.sm.events), 3)

    def test_transition_count(self):
        self.assertEqual(len(self.sm.transitions), 5)

    def test_initial_state(self):
        self.assertEqual(self.sm.initial_state, "Idle")

    def test_mermaid_generation(self):
        mermaid = generate_mermaid(self.sm)
        self.assertIn("[*] --> Idle", mermaid)
        self.assertIn("Idle --> Active : start / init()", mermaid)
        self.assertIn("Active --> Error : error [err_code != 0] / log()", mermaid)
        # 修正: 内部遷移ではなく外部遷移として期待する
        self.assertIn("Error --> Halt : [retry_count >= 3]", mermaid)


if __name__ == "__main__":
    unittest.main()