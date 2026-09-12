# tests/test_transition_generator.py
"""TransitionGenerator（横並びテーブル + 短縮セル関数名）の単体テスト"""

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
from statable.model import State, Event, Transition, StateType
from statable.state_machine import StateMachine


def build_test_sm():
    sm = StateMachine()
    sm.add_state(State(name="Idle", type=StateType.INITIAL))
    sm.add_state(State(name="Active"))
    sm.add_state(State(name="Error"))
    sm.set_initial("Idle")

    sm.add_event(Event(name="START"))
    sm.add_event(Event(name="ERROR"))
    sm.add_event(Event(name=""))

    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="err_code != 0",
        pre_actions=["LogError"],
        target="Active",
        has_else=True,
        else_target="Error",
        else_actions=["LogWarning"],
    ))
    sm.add_transition(Transition(
        source="Active", event="ERROR",
        condition="",
        pre_actions=["CheckSensor"],
        target="Error",
        has_else=True,
    ))
    return sm


class TestTransitionGeneratorHorizontal(unittest.TestCase):

    def setUp(self):
        self.gen = TransitionGenerator()

    def test_set_layer(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen.layer_name, "Driver")

    def test_short_cell_func_name(self):
        """短縮セル関数名 t_<State>_<Event>"""
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen._cell_func_name("Idle", "START"), "t_Idle_START")

    def test_short_cell_func_name_empty_event(self):
        """空イベントは NONE"""
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen._cell_func_name("Error", ""), "t_Error_NONE")

    def test_long_cell_func_name(self):
        """SHORT_CELL_NAMES=False の完全名"""
        self.gen.SHORT_CELL_NAMES = False
        self.gen.set_layer("Driver")
        self.assertEqual(
            self.gen._cell_func_name("Idle", "START"),
            "transition_Driver_Idle_START"
        )

    def test_state_enum(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen._state_enum("Idle"), "STATE_Driver_Idle")

    def test_event_enum_empty(self):
        self.gen.set_layer("Driver")
        self.assertEqual(self.gen._event_enum(""), "EVENT_Driver_NONE")

    def test_cell_functions_generation(self):
        """セル関数が短縮名で生成される"""
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_transition_cell_functions(sm)

        print("\n=== Cell Functions ===")
        print(result)

        self.assertIn("static STATE_Driver_t t_Idle_START(", result)
        self.assertIn("static STATE_Driver_t t_Active_ERROR(", result)
        self.assertIn("RoleFunc_Driver_LogError(transition, ctx)", result)
        self.assertIn("RoleFunc_Driver_CheckSensor(transition, ctx)", result)
        self.assertIn("if (err_code != 0)", result)

    def test_transition_table_generation(self):
        """横並びテーブルが生成される"""
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_transition_table(sm)

        print("\n=== Horizontal Transition Table ===")
        print(result)

        # 横並びテーブルの検証
        self.assertIn("typedef STATE_Driver_t (*TransitionFunc_Driver_t)", result)
        self.assertIn("transition_table_Driver", result)
        self.assertIn("[STATE_Driver_MAX][EVENT_Driver_MAX] = {", result)

        # 短縮関数名の検証
        self.assertIn("t_Idle_START", result)
        self.assertIn("t_Active_ERROR", result)
        self.assertIn("NULL", result)

        # 状態コメント
        self.assertIn("/* Idle", result)
        self.assertIn("/* Active", result)
        self.assertIn("/* Error", result)

        # ヘッダ行
        self.assertIn("START", result)
        self.assertIn("ERROR", result)
        self.assertIn("NONE", result)

    def test_function_dictionary_generation(self):
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_function_dictionary(sm)

        print("\n=== Function Dictionary ===")
        print(result)

        self.assertIn("TransitionDictEntry_Driver_t", result)
        self.assertIn("transition_dict_Driver[]", result)
        self.assertIn("TRANSITION_DICT_DRIVER_SIZE", result)
        self.assertIn('"Driver_Idle_START"', result)
        self.assertIn('"err_code != 0"', result)
        self.assertIn("t_Idle_START", result)
        self.assertIn("t_Active_ERROR", result)

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

        print(f"\n=== generate_all summary ===")
        for key, val in result.items():
            print(f"  {key}: {len(val)} chars")
            
    def test_cell_prototypes_generation(self):
        """セル関数の前方宣言が生成される"""
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_transition_cell_prototypes(sm)

        print("\n=== Cell Prototypes ===")
        print(result)

        # 検証
        self.assertIn("/* ===== セル単位遷移関数の前方宣言 ===== */", result)
        self.assertIn("static STATE_Driver_t t_Idle_START(", result)
        self.assertIn("static STATE_Driver_t t_Active_ERROR(", result)
        self.assertIn("const TransitionContext_Driver_t *transition,", result)
        self.assertIn("SystemContext_t *ctx);", result)


    def test_generate_all_includes_prototypes(self):
        """generate_all に cell_prototypes が含まれる"""
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_all(sm)

        self.assertIn('cell_prototypes', result)
        self.assertIn('cell_functions', result)
        self.assertIn('transition_table', result)
        self.assertIn('transition_table_header', result)
        self.assertIn('function_dict', result)
        self.assertIn('process_func', result)
        self.assertIn('get_next_event', result)

        print(f"\n=== generate_all summary ===")
        for key, val in result.items():
            print(f"  {key}: {len(val)} chars")
        
    def test_table_horizontal_alignment(self):
        """横並びテーブルの罫線と列の整列を確認"""
        self.gen.set_layer("Driver")
        sm = build_test_sm()
        result = self.gen.generate_transition_table(sm)

        # 期待される構造
        self.assertIn("/* Idle", result)
        self.assertIn("*/ {", result)  # 状態名の後に { があること
        self.assertIn("};", result)

def main():
    print("=" * 70)
    print("  TransitionGenerator 単体テスト（横並びテーブル + 短縮名）")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTransitionGeneratorHorizontal)
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