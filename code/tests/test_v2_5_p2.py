#!/usr/bin/env python3
"""StaTable v2.5 P2 (C-50 namespace constraint) test suite.

Verifies the fix for the C-50 issue:
  role_function_generator._should_declare_here must honor call_map so
  that a non-prefix namespace (e.g. namespace="Vending" in
  layer_name="Application") is declared in the layer header when it
  is actually called from that layer.

Sections:
  1. _should_declare_here: exact / prefix / call_map / mismatch
  2. generate_all_declarations: with and without state_machine
  3. Integration: full C generation from an XML that uses "Vending"
  4. Regression: existing prefix-match behavior still works

Run:
  python tests/test_v2_5_p2.py
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ======================================================================
# Harness (matches other v2_2 / v2_5 suites)
# ======================================================================
class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  [PASS] {name}")

    def fail(self, name, msg=""):
        self.failed += 1
        self.errors.append((name, msg))
        print(f"  [FAIL] {name}")
        if msg:
            print(f"         {msg}")

    def summary(self):
        total = self.passed + self.failed
        print()
        print("=" * 70)
        print(f"  TOTAL: {total}  PASSED: {self.passed}  FAILED: {self.failed}")
        print("=" * 70)
        if self.errors:
            print("\nFailures:")
            for name, msg in self.errors:
                print(f"  - {name}")
                if msg:
                    print(f"      {msg}")
        return self.failed == 0


R = TestResult()


def check(name, cond, msg=""):
    if cond:
        R.ok(name)
    else:
        R.fail(name, msg)
    return cond


# ======================================================================
# Fixtures
# ======================================================================
def make_sm(layer_name="Application", roles=None, transitions=None):
    from statable.state_machine import StateMachine
    from statable.model import State, Event

    sm = StateMachine()
    sm.layer_name = layer_name
    for name in ["Idle", "Active", "Error"]:
        sm.add_state(State(name=name))
    for name in ["START", "STOP"]:
        sm.add_event(Event(name=name))

    for rf in (roles or []):
        sm.add_role_function(rf)
    for t in (transitions or []):
        sm.add_transition(t)
    return sm


def make_role(name, namespace):
    from statable.model import RoleFunction
    return RoleFunction(name=name, namespace=namespace)


# ======================================================================
# [1] _should_declare_here: the core decision
# ======================================================================
def test_should_declare_here():
    print("\n[1] _should_declare_here")

    from codegen.role_function_generator import RoleFunctionGenerator
    gen = RoleFunctionGenerator()
    gen.set_layer("Application")

    # 1a. Exact match (Application == Application)
    rf_exact = make_role("Init", "Application")
    check("exact match -> True",
          gen._should_declare_here(rf_exact) is True)

    # 1b. Prefix match (App <-> Application)
    rf_prefix = make_role("Show", "App")
    check("prefix match (App <-> Application) -> True",
          gen._should_declare_here(rf_prefix) is True)

    # 1c. Non-prefix namespace (Vending) WITHOUT call_map
    rf_vending = make_role("ShowBalance", "Vending")
    check("non-prefix without call_map -> False (backward compat)",
          gen._should_declare_here(rf_vending) is False)

    # 1d. Non-prefix namespace WITH call_map hit (qualified name)
    call_map = {"Vending.ShowBalance": [object()]}
    check("non-prefix WITH call_map (qualified) -> True",
          gen._should_declare_here(rf_vending, call_map) is True)

    # 1e. Non-prefix namespace WITH call_map hit (bare name)
    call_map_bare = {"ShowBalance": [object()]}
    check("non-prefix WITH call_map (bare) -> True",
          gen._should_declare_here(rf_vending, call_map_bare) is True)

    # 1f. Non-prefix namespace WITH empty call_map -> False
    check("non-prefix WITH empty call_map -> False",
          gen._should_declare_here(rf_vending, {}) is False)

    # 1g. Non-prefix namespace WITH unrelated call_map -> False
    call_map_other = {"Unrelated.Func": [object()]}
    check("non-prefix WITH unrelated call_map -> False",
          gen._should_declare_here(rf_vending, call_map_other) is False)

    # 1h. No layer_name (root / system) -> True always
    gen_nolayer = RoleFunctionGenerator()
    gen_nolayer.set_layer("")
    check("no layer_name -> True (any)",
          gen_nolayer._should_declare_here(rf_vending) is True)


# ======================================================================
# [2] generate_all_declarations signature & behavior
# ======================================================================
def test_generate_all_declarations():
    print("\n[2] generate_all_declarations")

    from codegen.role_function_generator import RoleFunctionGenerator
    from statable.model import Transition

    # SM with a non-prefix role function
    rf_vending = make_role("ShowBalance", "Vending")
    t = Transition(
        source="Idle", event="START",
        condition="",
        target="Active",
        has_else=False, early_return=True, label="T1",
        pre_actions=["Vending.ShowBalance"],
    )
    sm = make_sm(
        layer_name="Application",
        roles=[rf_vending],
        transitions=[t],
    )

    gen = RoleFunctionGenerator()
    gen.set_layer("Application")

    # 2a. Without state_machine: no declaration (backward compat)
    h_no_sm = gen.generate_all_declarations([rf_vending])
    check("without state_machine: no declaration (backward compat)",
          "ShowBalance" not in h_no_sm,
          f"got:\n{h_no_sm}")

    # 2b. With state_machine: declaration appears
    h_with_sm = gen.generate_all_declarations([rf_vending], sm)
    check("with state_machine: declaration present",
          "ShowBalance" in h_with_sm,
          f"got:\n{h_with_sm}")
    check("with state_machine: uses Vending namespace",
          "RoleFunc_Vending_ShowBalance" in h_with_sm,
          f"got:\n{h_with_sm}")


# ======================================================================
# [3] Regression: prefix-match still works
# ======================================================================
def test_prefix_regression():
    print("\n[3] Prefix-match regression")

    from codegen.role_function_generator import RoleFunctionGenerator
    gen = RoleFunctionGenerator()
    gen.set_layer("Application")

    rf_app = make_role("Init", "App")
    h = gen.generate_all_declarations([rf_app])
    check("prefix namespace App still declared without sm",
          "Init" in h, f"got:\n{h}")
    check("uses App namespace",
          "RoleFunc_App_Init" in h, f"got:\n{h}")

    rf_exact = make_role("Boot", "Application")
    h2 = gen.generate_all_declarations([rf_exact])
    check("exact namespace Application still declared",
          "Boot" in h2, f"got:\n{h2}")


# ======================================================================
# [4] Integration: XML with non-prefix namespace -> both .h and .c
# ======================================================================
def test_full_generation():
    print("\n[4] Full generation (XML with non-prefix namespace)")

    from statable.xml_io import project_from_xml
    from codegen.c_code_generator import CCodeGenerator
    from codegen.config import ConfigManager
    import tempfile
    import shutil

    xml_path = PROJECT_ROOT / "docs" / "tutorial" / "vending_machine.xml"
    if not xml_path.exists():
        R.fail("vending_machine.xml not found (skip integration)",
               f"path: {xml_path}")
        return

    # Note: The vending XML uses namespace="App" (workaround).
    # We exercise the code path with state_machine plumbing anyway.
    # A future version with namespace="Vending" would exercise the
    # call_map fallback via the same generator.

    tabs, gd, role_lib, _, _, ps = project_from_xml(str(xml_path))

    cm = ConfigManager()
    if ps:
        cfg = cm.get_config()
        for k, v in ps.items():
            if hasattr(cfg, k):
                try:
                    setattr(cfg, k, v)
                except Exception:
                    pass
    config = cm.get_config()

    layers = tabs if isinstance(tabs, list) else list(tabs.values())
    # Normalize tuples
    layers = [t[1] if isinstance(t, tuple) and len(t) >= 2 else t
              for t in layers]

    gen = CCodeGenerator(config=config)
    files = gen.generate_all_layers(layers, gd, role_lib)

    # Find the Application layer header
    h_key = None
    for k in files:
        if "role_functions_Application.h" in k:
            h_key = k
            break

    check("Application role_functions .h generated",
          h_key is not None,
          f"available keys: {list(files.keys())}")

    if h_key:
        h_content = files[h_key]
        # Since the tutorial XML uses "App", expect App declarations
        check("declaration for App.IdleExit in .h",
              "IdleExit" in h_content,
              f"h content:\n{h_content[:500]}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.5 P2 (C-50 namespace constraint) test suite")
    print("=" * 70)

    test_should_declare_here()
    test_generate_all_declarations()
    test_prefix_regression()
    test_full_generation()

    ok = R.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()