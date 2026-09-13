# tests/test_xml_namespace.py
"""
XML namespace / used_role_functions の保存・復元テスト（H1 Stage 1）
"""

import sys
import os
import tempfile

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_THIS_DIR)

for _p in (_CODE_DIR,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest
import xml.etree.ElementTree as ET

from statable.model import (
    State, Event, Transition, RoleFunction,
)
from statable.state_machine import StateMachine
from statable.global_defs import (
    GlobalDefinitions, InterruptHandlerDef, InterruptAction,
)
from statable.xml_io import (
    state_machine_to_element,
    state_machine_from_element,
    global_defs_to_element,
    global_defs_from_element,
)


# ============================================================
# 1. StateMachine の RoleFunction namespace 保存/復元
# ============================================================
class TestRoleFunctionXml(unittest.TestCase):

    def _make_sm(self):
        sm = StateMachine()
        sm.layer_name = "Driver"
        sm.add_state(State(name="Idle"))
        sm.add_event(Event(name="START"))
        sm.add_role_function(RoleFunction(
            name="Init", namespace="Driver",
            description="ドライバ初期化",
        ))
        sm.add_role_function(RoleFunction(
            name="Shared", namespace="",
            description="共有関数",
        ))
        return sm

    def test_namespace_saved(self):
        sm = self._make_sm()
        elem = state_machine_to_element(sm)
        roles = elem.find("RoleFunctions")
        items = roles.findall("RoleFunction")
        self.assertEqual(len(items), 2)
        by_name = {r.get("name"): r for r in items}
        self.assertIn("Init", by_name)
        self.assertEqual(by_name["Init"].get("namespace"), "Driver")
        self.assertIn("Shared", by_name)
        self.assertEqual(by_name["Shared"].get("namespace"), "")

    def test_namespace_restored(self):
        sm = self._make_sm()
        elem = state_machine_to_element(sm)
        sm2 = state_machine_from_element(elem)

        rf_init = sm2.role_functions.get("Init")
        self.assertIsNotNone(rf_init)
        self.assertEqual(rf_init.namespace, "Driver")
        self.assertEqual(rf_init.qualified_name, "Driver.Init")

        rf_shared = sm2.role_functions.get("Shared")
        self.assertIsNotNone(rf_shared)
        self.assertEqual(rf_shared.namespace, "")

    def test_legacy_migration(self):
        """旧形式 'Driver_Init' が namespace/name に自動移行"""
        sm = StateMachine()
        sm.layer_name = "Driver"
        # 旧形式で登録
        sm.add_role_function(RoleFunction(
            name="Driver_Init",
            namespace="",
            description="レガシー",
        ))

        elem = state_machine_to_element(sm)
        sm2 = state_machine_from_element(elem)

        # 移行後: name="Init", namespace="Driver"
        self.assertIn("Init", sm2.role_functions)
        rf = sm2.role_functions["Init"]
        self.assertEqual(rf.namespace, "Driver")
        self.assertEqual(rf.qualified_name, "Driver.Init")

    def test_legacy_no_layer_no_migration(self):
        """layer_name 空なら移行しない"""
        sm = StateMachine()
        sm.layer_name = ""
        sm.add_role_function(RoleFunction(
            name="Driver_Init", namespace="",
        ))

        elem = state_machine_to_element(sm)
        sm2 = state_machine_from_element(elem)

        self.assertIn("Driver_Init", sm2.role_functions)
        rf = sm2.role_functions["Driver_Init"]
        self.assertEqual(rf.namespace, "")

    def test_legacy_different_prefix_no_migration(self):
        """別の層名プレフィックスなら移行しない"""
        sm = StateMachine()
        sm.layer_name = "Application"
        sm.add_role_function(RoleFunction(
            name="Driver_Init", namespace="",
        ))

        elem = state_machine_to_element(sm)
        sm2 = state_machine_from_element(elem)

        self.assertIn("Driver_Init", sm2.role_functions)
        rf = sm2.role_functions["Driver_Init"]
        self.assertEqual(rf.namespace, "")


# ============================================================
# 2. InterruptHandlerDef の used_* 保存/復元
# ============================================================
class TestInterruptUsedRoleFunctionsXml(unittest.TestCase):

    def test_used_role_functions_saved(self):
        gd = GlobalDefinitions()
        intr = InterruptHandlerDef(
            name="TIMER0",
            actions=[InterruptAction(condition="", action="Driver.Init")],
            used_role_functions=["Driver.Init", "Application.HandleTick"],
            used_variables=["counter"],
        )
        gd.interrupts.append(intr)

        elem = global_defs_to_element(gd)
        intrs = elem.find("Interrupts")
        child = intrs.find("Interrupt")
        refs = child.findall("UsedRoleFunction")
        self.assertEqual(len(refs), 2)
        self.assertEqual(refs[0].get("ref"), "Driver.Init")
        self.assertEqual(refs[1].get("ref"), "Application.HandleTick")
        vars_ = child.findall("UsedVariable")
        self.assertEqual(len(vars_), 1)
        self.assertEqual(vars_[0].get("name"), "counter")

    def test_used_role_functions_restored(self):
        gd = GlobalDefinitions()
        intr = InterruptHandlerDef(
            name="TIMER0",
            actions=[InterruptAction(condition="", action="Driver.Init")],
            used_role_functions=["Driver.Init", "Application.HandleTick"],
            used_variables=["counter"],
        )
        gd.interrupts.append(intr)

        elem = global_defs_to_element(gd)
        gd2 = global_defs_from_element(elem)

        self.assertEqual(len(gd2.interrupts), 1)
        restored = gd2.interrupts[0]
        self.assertEqual(
            restored.used_role_functions,
            ["Driver.Init", "Application.HandleTick"],
        )
        self.assertEqual(restored.used_variables, ["counter"])

    def test_empty_used_lists(self):
        gd = GlobalDefinitions()
        intr = InterruptHandlerDef(name="TIMER0")
        gd.interrupts.append(intr)

        elem = global_defs_to_element(gd)
        child = elem.find("Interrupts").find("Interrupt")
        self.assertEqual(len(child.findall("UsedRoleFunction")), 0)
        self.assertEqual(len(child.findall("UsedVariable")), 0)

        gd2 = global_defs_from_element(elem)
        self.assertEqual(gd2.interrupts[0].used_role_functions, [])
        self.assertEqual(gd2.interrupts[0].used_variables, [])


# ============================================================
# 3. 統合（ファイル保存 → 読込）
# ============================================================
class TestProjectRoundtrip(unittest.TestCase):

    def test_full_roundtrip(self):
        from statable.xml_io import project_to_xml, project_from_xml

        sm = StateMachine()
        sm.layer_name = "Driver"
        sm.add_state(State(name="Idle"))
        sm.add_event(Event(name="START"))
        sm.add_role_function(RoleFunction(
            name="Init", namespace="Driver",
        ))

        gd = GlobalDefinitions()
        gd.interrupts.append(InterruptHandlerDef(
            name="TIMER0",
            used_role_functions=["Driver.Init"],
        ))

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "project.xml")
            project_to_xml([("Driver", sm)], gd, path)

            (tabs, gd2, rl, cl, ll, ps) = project_from_xml(path)

        self.assertEqual(len(tabs), 1)
        _, sm2 = tabs[0]
        rf = sm2.role_functions.get("Init")
        self.assertIsNotNone(rf)
        self.assertEqual(rf.namespace, "Driver")

        self.assertEqual(len(gd2.interrupts), 1)
        self.assertEqual(
            gd2.interrupts[0].used_role_functions,
            ["Driver.Init"],
        )


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestRoleFunctionXml,
        TestInterruptUsedRoleFunctionsXml,
        TestProjectRoundtrip,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)