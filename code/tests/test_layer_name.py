# tests/test_layer_name.py
"""
layer_name 属性の単体テスト（(a) 段階）

テスト範囲:
  - StateMachine 属性
  - xml_io 保存/復元
  - c_code_generator での反映
  - _get_layer_name ユーティリティ
"""

import sys
import os
import tempfile

_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR    = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

from statable.state_machine import StateMachine
from statable.model import State, Event, Transition
from statable.xml_io import (
    state_machine_to_element,
    state_machine_from_element,
)

from sample_data import SampleDataGenerator
from c_code_generator import CCodeGenerator
from config import CodeGenerationConfig


def make_sample():
    return SampleDataGenerator().get_sample_data()


def make_sm(layer_name=""):
    """テスト用 StateMachine を構築"""
    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.add_transition(Transition(
        source="Idle", event="START", target="Active",
    ))
    sm.set_initial("Idle")
    sm.layer_name = layer_name
    return sm


# ============================================================
# 1. StateMachine 属性
# ============================================================
class TestStateMachineAttribute(unittest.TestCase):

    def test_default_is_empty(self):
        sm = StateMachine()
        self.assertEqual(sm.layer_name, "")

    def test_set_and_get(self):
        sm = StateMachine()
        sm.layer_name = "Driver"
        self.assertEqual(sm.layer_name, "Driver")

    def test_independent_instances(self):
        sm1 = StateMachine()
        sm2 = StateMachine()
        sm1.layer_name = "Driver"
        self.assertEqual(sm2.layer_name, "")

    def test_coexists_with_priority(self):
        sm = StateMachine()
        sm.layer_name = "Driver"
        sm.layer_priority = 3
        sm.layer_description = "Driver layer"
        self.assertEqual(sm.layer_name, "Driver")
        self.assertEqual(sm.layer_priority, 3)
        self.assertEqual(sm.layer_description, "Driver layer")


# ============================================================
# 2. xml_io 保存/復元
# ============================================================
class TestXmlIO(unittest.TestCase):

    def test_save_layer_name(self):
        sm = make_sm(layer_name="Driver")
        elem = state_machine_to_element(sm)
        self.assertEqual(elem.get("layer_name"), "Driver")

    def test_save_empty_layer_name(self):
        sm = make_sm(layer_name="")
        elem = state_machine_to_element(sm)
        self.assertEqual(elem.get("layer_name"), "")

    def test_load_layer_name(self):
        sm = make_sm(layer_name="Driver")
        elem = state_machine_to_element(sm)
        sm2 = state_machine_from_element(elem)
        self.assertEqual(sm2.layer_name, "Driver")

    def test_load_empty_layer_name(self):
        sm = make_sm(layer_name="")
        elem = state_machine_to_element(sm)
        sm2 = state_machine_from_element(elem)
        self.assertEqual(sm2.layer_name, "")

    def test_roundtrip(self):
        sm = make_sm(layer_name="Middleware")
        sm.layer_priority = 3
        sm.layer_description = "Middle layer"
        elem = state_machine_to_element(sm)
        sm2 = state_machine_from_element(elem)
        self.assertEqual(sm2.layer_name, "Middleware")
        self.assertEqual(sm2.layer_priority, 3)
        self.assertEqual(sm2.layer_description, "Middle layer")

    def test_missing_attr_uses_default(self):
        """古いXML（layer_name なし）を読込"""
        sm = make_sm(layer_name="Driver")
        elem = state_machine_to_element(sm)
        # 属性削除
        del elem.attrib["layer_name"]
        sm2 = state_machine_from_element(elem)
        self.assertEqual(sm2.layer_name, "")


# ============================================================
# 3. 生成コードへの反映
# ============================================================
class TestGenerationWithLayerName(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()

    def test_no_layer_name(self):
        """層名なし → STATE_XXX 形式（大文字）"""
        self.sm.layer_name = ""
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        types = files['statable_types.h']
        # ★ sample_data の状態名は INIT/IDLE/RUNNING/ERROR（大文字）
        self.assertIn('STATE_INIT', types)
        self.assertIn('STATE_IDLE', types)
        self.assertIn('STATE_RUNNING', types)
        self.assertIn('STATE_ERROR', types)
        # 型名も層名なし
        self.assertIn('} STATE_t;', types)
        # 層名が付いていない
        self.assertNotIn('STATE_Driver_', types)
        self.assertNotIn('STATE_Application_', types)

    def test_with_layer_name(self):
        """層名あり → STATE_<Layer>_XXX 形式"""
        self.sm.layer_name = "Driver"
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        types = files['statable_types.h']
        # 層名付き
        self.assertIn('STATE_Driver_INIT', types)
        self.assertIn('STATE_Driver_IDLE', types)
        self.assertIn('STATE_Driver_RUNNING', types)
        self.assertIn('STATE_Driver_ERROR', types)
        # 型名も層名付き
        self.assertIn('} STATE_Driver_t;', types)

    def test_transitions_process_func_layer(self):
        """StateMachine_Process_<Layer> 生成"""
        self.sm.layer_name = "Driver"
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        src = files['statable_transitions.c']
        self.assertIn('StateMachine_Process_Driver', src)

    def test_transitions_process_func_nolayer(self):
        """層名なし → StateMachine_Process"""
        self.sm.layer_name = ""
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        src = files['statable_transitions.c']
        self.assertIn('StateMachine_Process(', src)

    def test_super_loop_state_var(self):
        """スーパーループの層付き変数"""
        self.sm.layer_name = "Driver"
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        run_c = files['MyProject_run.c']
        self.assertIn('g_Driver_state', run_c)

    def test_super_loop_state_var_nolayer(self):
        """スーパーループの層なし変数"""
        self.sm.layer_name = ""
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        run_c = files['MyProject_run.c']
        self.assertIn('g_state', run_c)
        self.assertNotIn('g_Driver_state', run_c)

    def test_super_include_extern(self):
        """スーパーインクルードの extern 宣言"""
        self.sm.layer_name = "Driver"
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        h = files['statable_all.h']
        self.assertIn('extern STATE_Driver_t g_Driver_state;', h)

    def test_super_include_extern_nolayer(self):
        self.sm.layer_name = ""
        gen = CCodeGenerator()
        files = gen.generate_all(self.sm, self.gd)
        h = files['statable_all.h']
        self.assertIn('extern STATE_t g_state;', h)


# ============================================================
# 4. 部分修飾（_get_layer_name）
# ============================================================
class TestGetLayerName(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.gen = CCodeGenerator()

    def test_returns_empty_when_unset(self):
        self.sm.layer_name = ""
        self.assertEqual(self.gen._get_layer_name(self.sm), "")

    def test_returns_name_when_set(self):
        self.sm.layer_name = "Driver"
        self.assertEqual(
            self.gen._get_layer_name(self.sm), "Driver"
        )

    def test_handles_missing_attr(self):
        """layer_name 属性がないオブジェクト"""
        class Dummy:
            pass
        self.assertEqual(
            self.gen._get_layer_name(Dummy()), ""
        )

    def test_handles_none(self):
        """layer_name = None"""
        self.sm.layer_name = None
        self.assertEqual(
            self.gen._get_layer_name(self.sm), ""
        )


# ============================================================
# 5. ジェネレータへの伝搬
# ============================================================
class TestGeneratorSetup(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.gen = CCodeGenerator()

    def test_setup_propagates_to_sub_generators(self):
        """_setup_layer_generators が各サブジェネレータに反映"""
        self.sm.layer_name = "Driver"
        self.gen._setup_layer_generators(self.sm)
        self.assertEqual(
            self.gen.enum_gen.layer_name, "Driver"
        )
        self.assertEqual(
            self.gen.transition_gen.layer_name, "Driver"
        )
        self.assertEqual(
            self.gen.role_func_gen.layer_name, "Driver"
        )

    def test_setup_clears_previous_layer(self):
        """前回の層名が残留しない"""
        self.sm.layer_name = "Driver"
        self.gen._setup_layer_generators(self.sm)
        # 別の層なし StateMachine で再設定
        sm2 = make_sm(layer_name="")
        self.gen._setup_layer_generators(sm2)
        self.assertEqual(
            self.gen.enum_gen.layer_name, ""
        )
        self.assertEqual(
            self.gen.transition_gen.layer_name, ""
        )


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestStateMachineAttribute,
        TestXmlIO,
        TestGenerationWithLayerName,
        TestGetLayerName,
        TestGeneratorSetup,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)