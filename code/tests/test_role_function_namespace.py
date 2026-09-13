# tests/test_role_function_namespace.py
"""
RoleFunction.namespace の単体テスト（H1 Stage 1）
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


# ============================================================
# 1. model.RoleFunction
# ============================================================
class TestModelRoleFunction(unittest.TestCase):

    def test_default_namespace_empty(self):
        rf = RoleFunction(name="Init")
        self.assertEqual(rf.namespace, "")

    def test_qualified_name_with_namespace(self):
        rf = RoleFunction(name="Init", namespace="Driver")
        self.assertEqual(rf.qualified_name, "Driver.Init")

    def test_qualified_name_without_namespace(self):
        rf = RoleFunction(name="Init")
        self.assertEqual(rf.qualified_name, "Init")

    def test_title_uses_qualified_name(self):
        rf = RoleFunction(name="Init", namespace="Driver")
        self.assertEqual(rf.title, "ロール関数: Driver.Init")

    def test_explicit_title_preserved(self):
        rf = RoleFunction(name="Init", namespace="Driver",
                          title="ドライバ初期化")
        self.assertEqual(rf.title, "ドライバ初期化")

    def test_from_legacy_name_with_layer(self):
        rf = RoleFunction.from_legacy_name(
            "Driver_Init", layer_names=["Driver", "Application"]
        )
        self.assertEqual(rf.namespace, "Driver")
        self.assertEqual(rf.name, "Init")

    def test_from_legacy_name_no_match(self):
        rf = RoleFunction.from_legacy_name(
            "Init", layer_names=["Driver", "Application"]
        )
        self.assertEqual(rf.namespace, "")
        self.assertEqual(rf.name, "Init")

    def test_from_legacy_name_empty(self):
        rf = RoleFunction.from_legacy_name("", layer_names=["Driver"])
        self.assertEqual(rf.name, "")
        self.assertEqual(rf.namespace, "")

    def test_from_legacy_name_no_layer_list(self):
        rf = RoleFunction.from_legacy_name("Driver_Init", layer_names=None)
        self.assertEqual(rf.namespace, "")
        self.assertEqual(rf.name, "Driver_Init")


# ============================================================
# 2. libcntrl.RoleFunction
# ============================================================
class TestLibcntrlRoleFunction(unittest.TestCase):

    def setUp(self):
        try:
            from libcntrl.role_function_library import (
                RoleFunction as LibRoleFunction
            )
        except ImportError:
            from statable_gui.libcntrl.role_function_library import (
                RoleFunction as LibRoleFunction
            )
        self.LibRoleFunction = LibRoleFunction

    def test_default_namespace_empty(self):
        rf = self.LibRoleFunction(name="Init")
        self.assertEqual(rf.namespace, "")

    def test_qualified_name_with_namespace(self):
        rf = self.LibRoleFunction(name="Init", namespace="Driver")
        self.assertEqual(rf.qualified_name, "Driver.Init")

    def test_qualified_name_without_namespace(self):
        rf = self.LibRoleFunction(name="Init")
        self.assertEqual(rf.qualified_name, "Init")

    def test_to_dict_includes_namespace(self):
        rf = self.LibRoleFunction(name="Init", namespace="Driver")
        d = rf.to_dict()
        self.assertEqual(d['name'], "Init")
        self.assertEqual(d['namespace'], "Driver")

    def test_from_dict_with_namespace(self):
        d = {'name': "Init", 'namespace': "Driver",
             'title': "", 'description': ""}
        rf = self.LibRoleFunction.from_dict(d)
        self.assertEqual(rf.namespace, "Driver")
        self.assertEqual(rf.name, "Init")

    def test_from_dict_legacy_no_namespace(self):
        d = {'name': "Init", 'title': "", 'description': ""}
        rf = self.LibRoleFunction.from_dict(d)
        self.assertEqual(rf.namespace, "")


# ============================================================
# 3. RoleFunctionLibrary
# ============================================================
class TestRoleFunctionLibrary(unittest.TestCase):

    def setUp(self):
        try:
            from libcntrl.role_function_library import (
                RoleFunctionLibrary, RoleFunction as LibRoleFunction
            )
        except ImportError:
            from statable_gui.libcntrl.role_function_library import (
                RoleFunctionLibrary, RoleFunction as LibRoleFunction
            )
        self.Lib = RoleFunctionLibrary
        self.RF = LibRoleFunction

    def test_add_and_get_by_qualified_name(self):
        lib = self.Lib()
        lib.add(self.RF(name="Init", namespace="Driver"))
        rf = lib.get("Driver.Init")
        self.assertIsNotNone(rf)
        self.assertEqual(rf.namespace, "Driver")

    def test_add_and_get_by_bare_name(self):
        lib = self.Lib()
        lib.add(self.RF(name="Init", namespace="Driver"))
        rf = lib.get("Init")
        self.assertIsNotNone(rf)
        self.assertEqual(rf.namespace, "Driver")

    def test_namespace_avoids_collision(self):
        lib = self.Lib()
        lib.add(self.RF(name="Init", namespace="Driver"))
        lib.add(self.RF(name="Init", namespace="Application"))
        self.assertEqual(len(lib.list_all()), 2)

    def test_duplicate_namespace_name_raises(self):
        lib = self.Lib()
        lib.add(self.RF(name="Init", namespace="Driver"))
        with self.assertRaises(ValueError):
            lib.add(self.RF(name="Init", namespace="Driver"))

    def test_to_dict_from_dict_roundtrip(self):
        lib = self.Lib()
        lib.add(self.RF(name="Init", namespace="Driver",
                        description="init desc"))
        d = lib.to_dict()
        lib2 = self.Lib.from_dict(d)
        rf = lib2.get("Driver.Init")
        self.assertIsNotNone(rf)
        self.assertEqual(rf.description, "init desc")


# ============================================================
# 実行
# ============================================================
def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestModelRoleFunction,
        TestLibcntrlRoleFunction,
        TestRoleFunctionLibrary,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite).wasSuccessful()


if __name__ == '__main__':
    sys.exit(0 if run_tests() else 1)