# tests/test_transition_generator.py
"""TransitionGenerator（多層対応 + Function Dictionary）の単体テスト"""

import sys
import os
import unittest
import logging

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'codegen'))
sys.path.insert(0, os.path.join(project_root, 'statable'))

logging.basicConfig(level=logging.INFO)

from codegen.transition_generator import TransitionGenerator
from statable.model import State, Event, Transition, StateType, EventKind
from statable.state_machine import StateMachine


def build_test_sm():
    """テスト用ステートマシン"""
    sm = StateMachine()
    sm.add_state(State(name="Idle", type=StateType.INITIAL))
    sm.add_state(State(name="Active"))
    sm.add_state(State(name="Error"))
    sm.set_initial("Idle")

    sm.add_event(Event(name="START"))
    sm.add_event(Event(name="ERROR"))
    sm.add_event(Event(name=""))  # 完了遷移

    # Idle -[START]-> Active
    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="err_code != 0",
        pre_actions=["LogError"],
        target="Active",
        has_else=True,
        else_target="Error",
        else_actions=["LogWarning"],
    ))

    # Active -[ERROR]-> Error
    sm.add_transition(Transition(
        source="Active", event="ERROR",
        condition="",
        pre_actions=["CheckSensor"],
        target="Error",
        has_else=True,
        else_target="",
        else_actions=[],
    ))

    return sm


class TestTransitionGeneratorLayer(unittest.TestCase):

    def setUp(self):
        self.gen = TransitionGenerator()

    def test_set_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen.layer_name, "Driver")

    def test_state_enum(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen._state_enum("Idle"), "STATE_Driver_Idle")

    def test_event_enum_empty(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen._event_enum(""), "EVENT_Driver_NONE")

    def test_cell_func_name(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._cell_func_name("Idle", "START"),
            "transition_Driver_Idle_START"
        )

    def test_cell_func_name_empty_event(self):
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._cell_func_name("Error", ""),
            "transition_Driver_Error_NONE"
        )

    def test_cell_functions_generation(self):
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_transition_cell_functions(sm)

        print("\n=== Cell Functions ===")
        print(result)

        # 検証
        self.assertIn("transition_Driver_Idle_START", result)
        self.assertIn("transition_Driver_Active_ERROR", result)
        self.assertIn("STATE_Driver_t next_state", result)
        self.assertIn("RoleFunc_Driver_LogError(transition, ctx)", result)
        self.assertIn("RoleFunc_Driver_CheckSensor(transition, ctx)", result)
        self.assertIn("if (err_code != 0)", result)
        self.assertIn("if (1)", result)  # 空条件

    def test_transition_table_generation(self):
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_transition_table(sm)

        print("\n=== Transition Table ===")
        print(result)

        self.assertIn("typedef STATE_Driver_t (*TransitionFunc_Driver_t)", result)
        self.assertIn("transition_table_Driver", result)
        self.assertIn("[STATE_Driver_Idle][EVENT_Driver_START]", result)
        self.assertIn("transition_Driver_Idle_START", result)

    def test_function_dictionary_generation(self):
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_function_dictionary(sm)

        print("\n=== Function Dictionary ===")
        print(result)

        # 検証
        self.assertIn("TransitionDictEntry_Driver_t", result)
        self.assertIn("transition_dict_Driver[]", result)
        self.assertIn("TRANSITION_DICT_DRIVER_SIZE", result)
        self.assertIn('"Driver_Idle_START"', result)
        self.assertIn('"err_code != 0"', result)
        self.assertIn("transition_Driver_Idle_START", result)

    def test_process_function_generation(self):
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_process_function(sm)

        print("\n=== Process Function ===")
        print(result)

        self.assertIn("STATE_Driver_t StateMachine_Process_Driver(", result)
        self.assertIn("TransitionContext_Driver_t transition", result)
        self.assertIn("transition_table_Driver[current_state][event]", result)

    def test_get_next_event_generation(self):
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_get_next_event_function(sm)

        print("\n=== GetNextEvent ===")
        print(result)

        self.assertIn("EVENT_Driver_t StateMachine_GetNextEvent_Driver(", result)
        self.assertIn("MAX_CONSECUTIVE_PENDING_EVENTS", result)
        self.assertIn("EVENT_Driver_NONE", result)

    def test_generate_all(self):
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_all(sm)

        self.assertIn('cell_functions', result)
        self.assertIn('transition_table', result)
        self.assertIn('function_dict', result)
        self.assertIn('process_func', result)
        self.assertIn('get_next_event', result)

        print(f"\n=== generate_all ===")
        print(f"  cell_functions: {len(result['cell_functions'])} chars")
        print(f"  transition_table: {len(result['transition_table'])} chars")
        print(f"  function_dict: {len(result['function_dict'])} chars")
        print(f"  process_func: {len(result['process_func'])} chars")
        print(f"  get_next_event: {len(result['get_next_event'])} chars")


def main():
    print("=" * 70)
    print("  TransitionGenerator 単体テスト")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTransitionGeneratorLayer)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 70)
    if result.wasSuccessful():
        print("  ✅ すべてのテストが成功しました")
    else:
        print(f"  ❌ 失敗: {len(result.failures)}, エラー: {len(result.errors)}")
    print("=" * 70)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())