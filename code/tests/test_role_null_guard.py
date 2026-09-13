# tests/test_role_null_guard.py
"""
RoleFunctionGenerator の NULL transition ガードテスト（H1 Stage 2）
"""

import sys
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

from statable.model import RoleFunction
from sample_data import SampleDataGenerator
from role_function_generator import RoleFunctionGenerator


def make_func(name, namespace='', description='', title=''):
    return RoleFunction(
        name=name, namespace=namespace,
        description=description, title=title,
    )


class DummyVar:
    def __init__(self, name, type_, unit='', description='',
                 array_size=0):
        self.name = name
        self.type = type_
        self.unit = unit
        self.description = description
        self.array_size = array_size


class DummyGlobalDefs:
    def __init__(self, variables=None):
        self.variables = variables or []


# ============================================================
# 1. NULL ガード生成
# ============================================================
class TestNullGuard(unittest.TestCase):

    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_null_guard_header_present(self):
        impl = self.gen.generate_implementation(
            make_func("Init"),
            include_transition_id=False,
        )
        self.assertIn(
            "/* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */",
            impl,
        )

    def test_from_state_default_value(self):
        impl = self.gen.generate_implementation(
            make_func("Init"),
            include_transition_id=False,
        )
        self.assertIn(
            "STATE_Driver_t from_state = STATE_Driver_MAX;",
            impl,
        )

    def test_event_default_value(self):
        impl = self.gen.generate_implementation(
            make_func("Init"),
            include_transition_id=False,
        )
        self.assertIn(
            "EVENT_Driver_t event = EVENT_Driver_NONE;",
            impl,
        )

    def test_null_check(self):
        impl = self.gen.generate_implementation(
            make_func("Init"),
            include_transition_id=False,
        )
        self.assertIn("if (transition != NULL) {", impl)

    def test_null_guard_assign(self):
        impl = self.gen.generate_implementation(
            make_func("Init"),
            include_transition_id=False,
        )
        self.assertIn("from_state = transition->from_state;", impl)
        self.assertIn("event = transition->event;", impl)

    def test_void_suppress(self):
        impl = self.gen.generate_implementation(
            make_func("Init"),
            include_transition_id=False,
        )
        self.assertIn("(void)from_state;", impl)
        self.assertIn("(void)event;", impl)

    def test_no_layer_null_guard(self):
        gen = RoleFunctionGenerator()
        impl = gen.generate_implementation(
            make_func("Init"),
            include_transition_id=False,
        )
        self.assertIn("STATE_t from_state = STATE_MAX;", impl)
        self.assertIn("EVENT_t event = EVENT_NONE;", impl)


# ============================================================
# 2. Transition_GetId の NULL チェック
# ============================================================
class TestTransitionGetIdNullCheck(unittest.TestCase):

    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_transition_null_check(self):
        code = self.gen.generate_transition_id_function()
        self.assertIn(
            "if (transition == NULL || table == NULL) {", code
        )

    def test_returns_none(self):
        code = self.gen.generate_transition_id_function()
        self.assertIn("return TRANSITION_ID_NONE;", code)


# ============================================================
# 3. namespace 対応
# ============================================================
class TestNamespaceInRoleFuncGen(unittest.TestCase):

    def setUp(self):
        self.gen = RoleFunctionGenerator()

    def test_namespace_in_function_name(self):
        func = make_func("Init", namespace="Driver")
        name = self.gen._generate_function_name(func)
        self.assertEqual(name, "RoleFunc_Driver_Init")

    def test_namespace_in_marker(self):
        func = make_func("Init", namespace="Driver")
        marker = self.gen._get_marker_name(func)
        self.assertEqual(marker, "Driver_Init")

    def test_namespace_fallback_to_layer(self):
        self.gen.set_layer("Application")
        func = make_func("Init", namespace="")  # namespace 空
        name = self.gen._generate_function_name(func)
        # layer_name にフォールバック
        self.assertEqual(name, "RoleFunc_Application_Init")

    def test_explicit_namespace_overrides_layer(self):
        self.gen.set_layer("Application")
        func = make_func("Init", namespace="Driver")
        name = self.gen._generate_function_name(func)
        # func.namespace 優先
        self.assertEqual(name, "RoleFunc_Driver_Init")

    def test_dedupe_by_namespace_name(self):
        funcs = [
            make_func("Init", namespace="Driver"),
            make_func("Init", namespace="Application"),
            make_func("Init", namespace="Driver"),  # 重複
        ]
        result = self.gen._dedupe_by_name(funcs)
        self.assertEqual(len(result), 2)


# ============================================================
# 4. 実装全体の整合性
# ============================================================
class TestImplementationIntegration(unittest.TestCase):

    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_null_guard_before_transition_id(self):
        gd = DummyGlobalDefs(variables=[
            DummyVar('counter', 'uint32_t', '', 'カウンタ'),
        ])
        impl = self.gen.generate_implementation(
            make_func("Init", namespace="Driver"),
            global_defs=gd,
            include_transition_id=False,
        )
        pos_guard = impl.index("if (transition != NULL)")
        pos_data = impl.index("&ctx->data.counter")
        self.assertLess(pos_guard, pos_data)

    def test_marker_name_uses_namespace(self):
        impl = self.gen.generate_implementation(
            make_func("Init", namespace="Driver"),
            include_transition_id=False,
        )
        self.assertIn(
            "/* [[STABLE_USER_CODE_START:Driver_Init]] */", impl
        )


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestNullGuard,
        TestTransitionGetIdNullCheck,
        TestNamespaceInRoleFuncGen,
        TestImplementationIntegration,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)