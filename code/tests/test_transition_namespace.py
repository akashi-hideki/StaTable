# tests/test_transition_namespace.py
"""
Stage 4: 遷移側 Namespace.Name 対応テスト

対象: codegen/role_function_generator.py
  - _normalize_func_ref の qualified 保持
  - _extract_func_names_from_condition の dot-form 検出
  - _collect_call_sites の qualified キー
  - generate_call の namespace 正規化
  - 完全パイプライン（SM → 生成コード）
"""

import sys
import os
import re

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_THIS_DIR)
_CODEGEN_DIR = os.path.join(_CODE_DIR, 'codegen')

for _p in (_CODEGEN_DIR, _CODE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest

from statable.model import (
    State, Event, Transition, RoleFunction,
)
from statable.state_machine import StateMachine

from role_function_generator import RoleFunctionGenerator


def make_sm(layer="Driver"):
    sm = StateMachine()
    sm.layer_name = layer
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.add_event(Event(name="STOP"))
    return sm


def make_rf(name, namespace=""):
    return RoleFunction(name=name, namespace=namespace)


# ============================================================
# 1. _normalize_func_ref
# ============================================================
class TestNormalizeFuncRef(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_dot_form_preserved(self):
        self.assertEqual(
            self.gen._normalize_func_ref("Driver.Init"), "Driver.Init",
        )

    def test_dot_form_with_args(self):
        self.assertEqual(
            self.gen._normalize_func_ref("Driver.Init(arg1, arg2)"),
            "Driver.Init",
        )

    def test_dot_form_with_empty_parens(self):
        self.assertEqual(
            self.gen._normalize_func_ref("Driver.Init()"),
            "Driver.Init",
        )

    def test_bare_name(self):
        self.assertEqual(self.gen._normalize_func_ref("Init"), "Init")

    def test_bare_call(self):
        self.assertEqual(
            self.gen._normalize_func_ref("Init(arg1, arg2)"), "Init",
        )

    def test_rolefunc_with_layer(self):
        # RoleFunc_Driver_Init + layer=Driver → Driver.Init
        self.assertEqual(
            self.gen._normalize_func_ref("RoleFunc_Driver_Init"),
            "Driver.Init",
        )

    def test_rolefunc_without_layer_prefix(self):
        # RoleFunc_Init → Init
        self.assertEqual(
            self.gen._normalize_func_ref("RoleFunc_Init"), "Init",
        )

    def test_rolefunc_different_namespace(self):
        # RoleFunc_App_Init + layer=Driver → App_Init（layer と不一致）
        self.assertEqual(
            self.gen._normalize_func_ref("RoleFunc_App_Init"),
            "App_Init",
        )

    def test_legacy_underscore(self):
        # Driver_Init + layer=Driver → そのまま（RoleFunc_ なし）
        self.assertEqual(
            self.gen._normalize_func_ref("Driver_Init"), "Driver_Init",
        )

    def test_empty(self):
        self.assertEqual(self.gen._normalize_func_ref(""), "")

    def test_whitespace(self):
        self.assertEqual(
            self.gen._normalize_func_ref("   "), "",
        )

    def test_no_layer_dot_form(self):
        gen = RoleFunctionGenerator()
        self.assertEqual(
            gen._normalize_func_ref("Driver.Init"), "Driver.Init",
        )


# ============================================================
# 2. _extract_func_names_from_condition
# ============================================================
class TestExtractFromCondition(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_dot_form_bare(self):
        names = self.gen._extract_func_names_from_condition(
            "Driver.StartOk"
        )
        self.assertIn("Driver.StartOk", names)

    def test_dot_form_in_expression(self):
        names = self.gen._extract_func_names_from_condition(
            "Driver.StartOk && Application.CheckOther"
        )
        self.assertIn("Driver.StartOk", names)
        self.assertIn("Application.CheckOther", names)

    def test_dot_form_with_call(self):
        names = self.gen._extract_func_names_from_condition(
            "Driver.StartOk()"
        )
        self.assertIn("Driver.StartOk", names)

    def test_mixed_forms(self):
        names = self.gen._extract_func_names_from_condition(
            "Driver.StartOk() && Init && RoleFunc_Driver_Check"
        )
        self.assertIn("Driver.StartOk", names)
        self.assertIn("Init", names)
        self.assertIn("Driver.Check", names)

    def test_bare_only(self):
        names = self.gen._extract_func_names_from_condition("StartOk")
        self.assertIn("StartOk", names)

    def test_call_only(self):
        names = self.gen._extract_func_names_from_condition("StartOk()")
        self.assertIn("StartOk", names)

    def test_empty(self):
        self.assertEqual(
            self.gen._extract_func_names_from_condition(""), [],
        )

    def test_no_duplicates(self):
        names = self.gen._extract_func_names_from_condition(
            "Driver.Init && Driver.Init"
        )
        self.assertEqual(names.count("Driver.Init"), 1)


# ============================================================
# 3. _collect_call_sites
# ============================================================
class TestCollectCallSites(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_dot_form_in_condition(self):
        sm = make_sm("Driver")
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            condition="Driver.StartOk",
        ))
        cm = self.gen._collect_call_sites(sm)
        self.assertIn("Driver.StartOk", cm)
        self.assertEqual(cm["Driver.StartOk"][0].kind, "condition")

    def test_dot_form_in_pre_action(self):
        sm = make_sm("Driver")
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            pre_actions=["Driver.Init"],
        ))
        cm = self.gen._collect_call_sites(sm)
        self.assertIn("Driver.Init", cm)
        self.assertEqual(cm["Driver.Init"][0].kind, "pre_action")

    def test_dot_form_in_else_action(self):
        sm = make_sm("Driver")
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            else_actions=["Application.Fallback"],
        ))
        cm = self.gen._collect_call_sites(sm)
        self.assertIn("Application.Fallback", cm)
        self.assertEqual(cm["Application.Fallback"][0].kind, "else_action")

    def test_bare_name_still_works(self):
        sm = make_sm("Driver")
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            condition="StartOk",
        ))
        cm = self.gen._collect_call_sites(sm)
        self.assertIn("StartOk", cm)


# ============================================================
# 4. generate_call
# ============================================================
class TestGenerateCall(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Application")  # 層名と namespace を分離

    def test_dot_form_uses_explicit_namespace(self):
        """Driver.Init → RoleFunc_Driver_Init (layer 名は無視)"""
        self.assertEqual(
            self.gen.generate_call("Driver.Init"),
            "RoleFunc_Driver_Init(transition, ctx)",
        )

    def test_bare_falls_back_to_layer(self):
        """Init → RoleFunc_Application_Init (layer 名)"""
        self.assertEqual(
            self.gen.generate_call("Init"),
            "RoleFunc_Application_Init(transition, ctx)",
        )

    def test_rolefunc_passthrough(self):
        self.assertEqual(
            self.gen.generate_call("RoleFunc_Driver_Init"),
            "RoleFunc_Driver_Init(transition, ctx)",
        )

    def test_snake_case_bare(self):
        self.assertEqual(
            self.gen.generate_call("check_sensor"),
            "RoleFunc_Application_CheckSensor(transition, ctx)",
        )


# ============================================================
# 5. End-to-End: 遷移 → 生成コード
# ============================================================
class TestE2ETransitionNamespace(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Application")

    def test_dot_form_in_implementation(self):
        """RoleFunction の call_sites テーブルに Driver.Init が反映"""
        sm = make_sm("Application")
        sm.add_role_function(make_rf("Init", namespace="Driver"))
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            condition="Driver.Init",
        ))

        impl = self.gen.generate_all_implementations(
            list(sm.role_functions.values()),
            state_machine=sm,
        )

        # 関数名は RoleFunc_Driver_Init
        self.assertIn("int RoleFunc_Driver_Init(", impl)
        # call_sites テーブルあり
        self.assertIn("call_sites_", impl)

    def test_bare_form_falls_back_to_layer(self):
        """bare name は layer_name で namespace 補完"""
        sm = make_sm("Application")
        sm.add_role_function(make_rf("Init", namespace=""))
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            condition="Init",
        ))

        impl = self.gen.generate_all_implementations(
            list(sm.role_functions.values()),
            state_machine=sm,
        )
        self.assertIn("int RoleFunc_Application_Init(", impl)

    def test_dot_and_bare_coexist(self):
        """同一 SM 内で dot と bare が共存"""
        sm = make_sm("Application")
        sm.add_role_function(make_rf("Init", namespace="Driver"))
        sm.add_role_function(make_rf("Fallback", namespace=""))
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            condition="Driver.Init",
            else_actions=["Fallback"],
        ))

        impl = self.gen.generate_all_implementations(
            list(sm.role_functions.values()),
            state_machine=sm,
        )
        self.assertIn("int RoleFunc_Driver_Init(", impl)
        self.assertIn("int RoleFunc_Application_Fallback(", impl)


# ============================================================
# 6. 後方互換
# ============================================================
class TestBackwardCompat(unittest.TestCase):
    def setUp(self):
        self.gen = RoleFunctionGenerator()
        self.gen.set_layer("Driver")

    def test_bare_name_lookup_fallback(self):
        """call_map に bare name で引いても動く（後方互換）"""
        sm = make_sm("Driver")
        sm.add_role_function(make_rf("CheckSensor"))
        sm.add_transition(Transition(
            source="Idle", event="START", target="Active",
            pre_actions=["CheckSensor()"],
        ))
        cm = self.gen._collect_call_sites(sm)
        self.assertIn("CheckSensor", cm)

    def test_old_style_still_works(self):
        """旧形式（layer_name prefix）は影響なし"""
        gen = RoleFunctionGenerator()
        # layer_name 未設定
        names = gen._extract_func_names_from_condition(
            "CheckSensor()"
        )
        self.assertIn("CheckSensor", names)


# ============================================================
# 実行
# ============================================================
def run_tests(dump: bool = False):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestNormalizeFuncRef,
        TestExtractFromCondition,
        TestCollectCallSites,
        TestGenerateCall,
        TestE2ETransitionNamespace,
        TestBackwardCompat,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    ok = runner.run(suite).wasSuccessful()
    return ok


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)