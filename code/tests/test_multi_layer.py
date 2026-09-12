# tests/test_multi_layer.py
"""
複数層生成の単体テスト（(b) 段階）
"""

import sys
import os

_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR    = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

from statable.state_machine import StateMachine
from statable.model import State, Event, Transition

from sample_data import SampleDataGenerator
from c_code_generator import CCodeGenerator
from config import CodeGenerationConfig


def make_sm(layer_name, states=None, initial="Idle"):
    if states is None:
        states = ["Idle", "Active"]
    sm = StateMachine()
    for name in states:
        sm.add_state(State(name=name))
    sm.add_event(Event(name="START"))
    for i in range(len(states) - 1):
        sm.add_transition(Transition(
            source=states[i], event="START",
            target=states[i + 1],
        ))
    sm.set_initial(initial)
    sm.layer_name = layer_name
    return sm


def make_layers():
    d = make_sm("Driver");      d.layer_priority = 1
    m = make_sm("Middleware");  m.layer_priority = 3
    a = make_sm("Application"); a.layer_priority = 5
    return [("Driver", d), ("Middleware", m), ("Application", a)]


# ============================================================
# 1. _normalize_layers
# ============================================================
class TestNormalizeLayers(unittest.TestCase):

    def setUp(self):
        self.gen = CCodeGenerator()

    def test_single_sm(self):
        sm = make_sm("Driver")
        result = self.gen._normalize_layers(sm)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], sm)

    def test_list_of_tuples(self):
        layers = make_layers()
        result = self.gen._normalize_layers(layers)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], "Driver")
        self.assertEqual(result[1][0], "Middleware")
        self.assertEqual(result[2][0], "Application")

    def test_list_of_sm(self):
        d = make_sm("Driver")
        a = make_sm("Application")
        result = self.gen._normalize_layers([d, a])
        self.assertEqual(len(result), 2)

    def test_none_returns_empty(self):
        self.assertEqual(self.gen._normalize_layers(None), [])

    def test_priority_sorting(self):
        a = make_sm("A"); a.layer_priority = 9
        b = make_sm("B"); b.layer_priority = 1
        c = make_sm("C"); c.layer_priority = 5
        result = self.gen._normalize_layers([a, b, c])
        self.assertEqual([x[1] for x in result], [b, c, a])


# ============================================================
# 2. generate_all_layers
# ============================================================
class TestGenerateAllLayers(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()
        self.layers = make_layers()

    def test_single_layer_via_list(self):
        gen = CCodeGenerator()
        result = gen.generate_all_layers(
            [self.layers[0]], self.gd
        )
        self.assertIn('statable_types.h', result)
        self.assertEqual(len(result), 13)

    def test_multi_layer_count(self):
        gen = CCodeGenerator()
        result = gen.generate_all_layers(self.layers, self.gd)
        self.assertEqual(len(result), 13)

    def test_types_has_all_layers(self):
        gen = CCodeGenerator()
        result = gen.generate_all_layers(self.layers, self.gd)
        types = result['statable_types.h']

        self.assertIn('STATE_Driver_', types)
        self.assertIn('STATE_Middleware_', types)
        self.assertIn('STATE_Application_', types)

    def test_transitions_has_all_layers(self):
        gen = CCodeGenerator()
        result = gen.generate_all_layers(self.layers, self.gd)
        src = result['statable_transitions.c']

        self.assertIn('StateMachine_Process_Driver', src)
        self.assertIn('StateMachine_Process_Middleware', src)
        self.assertIn('StateMachine_Process_Application', src)

    def test_super_include_all_externs(self):
        gen = CCodeGenerator()
        result = gen.generate_all_layers(self.layers, self.gd)
        h = result['statable_all.h']

        self.assertIn('extern STATE_Driver_t g_Driver_state;', h)
        self.assertIn('extern STATE_Middleware_t g_Middleware_state;', h)
        self.assertIn('extern STATE_Application_t g_Application_state;', h)

    def test_super_loop_all_blocks(self):
        gen = CCodeGenerator()
        result = gen.generate_all_layers(self.layers, self.gd)
        run_c = result['MyProject_run.c']

        self.assertIn('g_Driver_state', run_c)
        self.assertIn('g_Middleware_state', run_c)
        self.assertIn('g_Application_state', run_c)
        self.assertIn('StateMachine_Process_Driver', run_c)
        self.assertIn('StateMachine_Process_Middleware', run_c)
        self.assertIn('StateMachine_Process_Application', run_c)

    def test_super_loop_priority_order(self):
        gen = CCodeGenerator()
        result = gen.generate_all_layers(self.layers, self.gd)
        run_c = result['MyProject_run.c']

        pos_driver = run_c.index('StateMachine_Process_Driver')
        pos_middle = run_c.index('StateMachine_Process_Middleware')
        pos_app    = run_c.index('StateMachine_Process_Application')

        self.assertLess(pos_driver, pos_middle)
        self.assertLess(pos_middle, pos_app)

    def test_super_loop_init_all(self):
        gen = CCodeGenerator()
        result = gen.generate_all_layers(self.layers, self.gd)
        run_c = result['MyProject_run.c']

        self.assertIn('g_Driver_state = STATE_Driver_Idle;', run_c)
        self.assertIn('g_Middleware_state = STATE_Middleware_Idle;', run_c)
        self.assertIn('g_Application_state = STATE_Application_Idle;', run_c)

    def test_single_sm_backward_compat(self):
        gen = CCodeGenerator()
        result = gen.generate_all_layers(
            self.layers[0][1], self.gd
        )
        self.assertEqual(len(result), 13)


# ============================================================
# 3. 空層対応
# ============================================================
class TestEmptyLayer(unittest.TestCase):

    def setUp(self):
        self.sm, self.gd = make_sample()

    def test_layer_name_empty(self):
        sm = make_sm("")
        gen = CCodeGenerator()
        result = gen.generate_all_layers([("", sm)], self.gd)
        types = result['statable_types.h']
        self.assertIn('STATE_', types)
        self.assertIn('} STATE_t;', types)

    def test_mixed_layers(self):
        d = make_sm("Driver")
        e = make_sm("")
        gen = CCodeGenerator()
        result = gen.generate_all_layers(
            [("Driver", d), ("", e)], self.gd
        )
        run_c = result['MyProject_run.c']
        self.assertIn('g_Driver_state', run_c)
        self.assertIn('g_state', run_c)


# ============================================================
# 実行
# ============================================================
def make_sample():
    return SampleDataGenerator().get_sample_data()


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestNormalizeLayers,
        TestGenerateAllLayers,
        TestEmptyLayer,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)