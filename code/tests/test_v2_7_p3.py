#!/usr/bin/env python3
"""
P3 (State actions codegen) test suite for StaTable v2.7.0.

Verifies:
  1. StateActionsGenerator module import
  2. set_layer / generate_header / generate_source
  3. _extract_rf_name / _action_line helpers
  4. Entry / Exit / Do table structure (ordered init, C89)
  5. Dispatcher range + NULL guard
  6. [[STABLE_USER_CODE_..._custom]] markers
  7. Integration: CCodeGenerator generates state_actions_<Layer>.{h,c}
  8. Integration: {project}_run.c emits <Layer>_Do(...) in loop top
  9. Integration: StateMachine_Process_<Layer> calls Entry/Exit on change

Run:
  python tests/test_v2_7_p3.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ======================================================================
# Simple test harness
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


RESULT = TestResult()


def check(name, condition, msg=""):
    if condition:
        RESULT.ok(name)
    else:
        RESULT.fail(name, msg)
    return condition


def _make_sm():
    """Build a small test StateMachine with two states."""
    from statable.state_machine import StateMachine
    from statable.model import State, Event, ActionStep

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.layer_priority = 3
    sm.add_state(State(
        name="Idle",
        entry=[ActionStep(role_function="Driver.IdleEntry")],
        do_actions=[ActionStep(role_function="Driver.Poll")],
    ))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.set_initial("Idle")
    return sm


# ======================================================================
# 1. Module import
# ======================================================================
def test_module_import():
    print("\n[1] Module import & _extract_rf_name")
    try:
        from codegen.state_actions_generator import (
            StateActionsGenerator, _extract_rf_name,
        )
        RESULT.ok("StateActionsGenerator imported")
        RESULT.ok("_extract_rf_name imported")
    except Exception as e:
        RESULT.fail("import failed", f"{type(e).__name__}: {e}")
        return

    from codegen.state_actions_generator import _extract_rf_name
    from statable.model import ActionStep

    check("_extract_rf_name(str)",
          _extract_rf_name("Driver.X") == "Driver.X")
    check("_extract_rf_name(ActionStep)",
          _extract_rf_name(ActionStep(role_function="A.B")) == "A.B")
    check("_extract_rf_name(None)",
          _extract_rf_name(None) == "")
    check("_extract_rf_name(empty ActionStep)",
          _extract_rf_name(ActionStep()) == "")


# ======================================================================
# 2. set_layer / name helpers
# ======================================================================
def test_set_layer_and_names():
    print("\n[2] set_layer & name helpers")
    from codegen.state_actions_generator import StateActionsGenerator

    g = StateActionsGenerator()
    check("default layer empty", g.layer_name == "")
    check("default _state_type()", g._state_type() == "STATE_t")

    g.set_layer("Driver")
    check("layer set", g.layer_name == "Driver")
    check("_state_type()", g._state_type() == "STATE_Driver_t")
    check("_state_max()", g._state_max() == "STATE_Driver_MAX")
    check("_func_type()", g._func_type() == "Driver_StateFunc_t")
    check("_state_enum('Idle')",
          g._state_enum("Idle") == "STATE_Driver_Idle")
    check("_state_func_name('Entry', 'Idle')",
          g._state_func_name("Entry", "Idle") == "Driver_Entry_Idle")
    check("_custom_marker_name('Do', 'Active')",
          g._custom_marker_name("Do", "Active") == "Driver_Do_Active_custom")


# ======================================================================
# 3. _rf_call / _fire_event_call
# ======================================================================
def test_role_and_event_calls():
    print("\n[3] RoleFunc / FIRE_EVENT calls")
    from codegen.state_actions_generator import StateActionsGenerator

    g = StateActionsGenerator()
    g.set_layer("Driver")

    check("_rf_call(Driver.X)",
          g._rf_call("Driver.X") ==
          "(void)RoleFunc_Driver_X(NULL, ctx)")
    check("_rf_call(bare)",
          g._rf_call("Poll") ==
          "(void)RoleFunc_Driver_Poll(NULL, ctx)")
    check("_rf_call(empty)", g._rf_call("") == "")

    check("_fire_event_call(Driver.TICK)",
          g._fire_event_call("Driver.TICK") ==
          "FIRE_EVENT_Driver(DRIVER_TICK)")
    check("_fire_event_call(empty)",
          g._fire_event_call("") == "")


# ======================================================================
# 4. _action_line
# ======================================================================
def test_action_line():
    print("\n[4] _action_line")
    from codegen.state_actions_generator import StateActionsGenerator
    from statable.model import ActionStep

    g = StateActionsGenerator()
    g.set_layer("Driver")

    # role without condition
    a1 = ActionStep(role_function="Driver.X")
    line1 = g._action_line(a1)
    check("role without condition",
          "(void)RoleFunc_Driver_X(NULL, ctx);" in line1)

    # role with condition
    a2 = ActionStep(role_function="Driver.Poll", condition="ctx->x > 0")
    line2 = g._action_line(a2)
    check("role with condition: if",
          "if (ctx->x > 0)" in line2)
    check("role with condition: call",
          "(void)RoleFunc_Driver_Poll(NULL, ctx);" in line2)

    # fire_event
    a3 = ActionStep(action_type="fire_event", event_name="Driver.TICK")
    line3 = g._action_line(a3)
    check("fire_event call",
          "FIRE_EVENT_Driver(DRIVER_TICK)" in line3)

    # custom -> skipped
    a4 = ActionStep(action_type="custom")
    line4 = g._action_line(a4)
    check("custom skipped", line4 == "")

    # empty role -> skipped
    a5 = ActionStep()
    line5 = g._action_line(a5)
    check("empty role skipped", line5 == "")


# ======================================================================
# 5. generate_header
# ======================================================================
def test_generate_header():
    print("\n[5] generate_header")
    from codegen.state_actions_generator import StateActionsGenerator

    sm = _make_sm()
    g = StateActionsGenerator()
    g.set_layer("Driver")
    h = g.generate_header(sm)

    check("has file comment",
          "@file    statable_state_actions_Driver.h" in h)
    check("has guard start",
          "#ifndef STATABLE_STATE_ACTIONS_DRIVER_H" in h)
    check("has include types_common",
          '#include "statable_types_common.h"' in h)
    check("has include types layer",
          '#include "statable_types_Driver.h"' in h)
    check("decl Entry",
          "void Driver_Entry(STATE_Driver_t state, SystemContext_t *ctx);" in h)
    check("decl Exit",
          "void Driver_Exit (STATE_Driver_t state, SystemContext_t *ctx);" in h)
    check("decl Do",
          "void Driver_Do   (STATE_Driver_t state, SystemContext_t *ctx);" in h)
    check("has guard end",
          "#endif /* STATABLE_STATE_ACTIONS_DRIVER_H */" in h)


# ======================================================================
# 6. generate_source structure
# ======================================================================
def test_generate_source_structure():
    print("\n[6] generate_source structure")
    from codegen.state_actions_generator import StateActionsGenerator

    sm = _make_sm()
    g = StateActionsGenerator()
    g.set_layer("Driver")
    src = g.generate_source(sm)

    check("has file comment",
          "@file    statable_state_actions_Driver.c" in src)
    check("has own include",
          '#include "statable_state_actions_Driver.h"' in src)
    check("has type_typedef",
          "typedef void (*Driver_StateFunc_t)(SystemContext_t *ctx);" in src)

    # Forward declarations
    check("Entry fwd decl Idle",
          "static void Driver_Entry_Idle(SystemContext_t *ctx);" in src)
    check("Entry fwd decl Active",
          "static void Driver_Entry_Active(SystemContext_t *ctx);" in src)
    check("Do fwd decl Idle",
          "static void Driver_Do_Idle(SystemContext_t *ctx);" in src)

    # Tables (ordered init)
    check("Entry table declared",
          "static const Driver_StateFunc_t g_Driver_EntryTable[STATE_Driver_MAX] = {" in src)
    check("Exit table declared",
          "static const Driver_StateFunc_t g_Driver_ExitTable[STATE_Driver_MAX] = {" in src)
    check("Do table declared",
          "static const Driver_StateFunc_t g_Driver_DoTable[STATE_Driver_MAX] = {" in src)

    # Table entry order (Idle then Active)
    idx_idle = src.find("Driver_Entry_Idle,  /* STATE_Driver_Idle */")
    idx_active = src.find("Driver_Entry_Active,  /* STATE_Driver_Active */")
    check("Entry table: Idle before Active",
          idx_idle >= 0 and idx_active > idx_idle)

    # Dispatchers
    check("Entry dispatcher",
          "void Driver_Entry(STATE_Driver_t state, SystemContext_t *ctx)" in src)
    check("Exit dispatcher",
          "void Driver_Exit(STATE_Driver_t state, SystemContext_t *ctx)" in src)
    check("Do dispatcher",
          "void Driver_Do(STATE_Driver_t state, SystemContext_t *ctx)" in src)
    check("range check cast",
          "(unsigned)state < (unsigned)STATE_Driver_MAX" in src)
    check("NULL guard",
          "if (fn != NULL)" in src)


# ======================================================================
# 7. Per-state functions + custom markers
# ======================================================================
def test_per_state_functions_and_markers():
    print("\n[7] Per-state functions + markers")
    from codegen.state_actions_generator import StateActionsGenerator

    sm = _make_sm()
    g = StateActionsGenerator()
    g.set_layer("Driver")
    src = g.generate_source(sm)

    # Idle has entry action
    check("Driver_Entry_Idle defined",
          "static void Driver_Entry_Idle(SystemContext_t *ctx)" in src)
    check("RoleFunc_Driver_IdleEntry called",
          "(void)RoleFunc_Driver_IdleEntry(NULL, ctx);" in src)

    # Active Do has Poll (condition-less in current test data)
    check("Driver_Do_Idle has RoleFunc_Driver_Poll",
          "(void)RoleFunc_Driver_Poll(NULL, ctx);" in src)

    # Custom markers (all 3 kinds x 2 states = 6)
    for kind in ("Entry", "Exit", "Do"):
        for state in ("Idle", "Active"):
            marker = f"Driver_{kind}_{state}_custom"
            start = f"/* [[STABLE_USER_CODE_START:{marker}]] */"
            end = f"/* [[STABLE_USER_CODE_END:{marker}]] */"
            check(f"marker start {marker}", start in src)
            check(f"marker end   {marker}", end in src)


# ======================================================================
# 8. Integration: CCodeGenerator generates state_actions files
# ======================================================================
def test_integration_generate_all_layers():
    print("\n[8] Integration: CCodeGenerator")
    from codegen.c_code_generator import CCodeGenerator
    from codegen.config import CodeGenerationConfig
    from statable.state_machine import StateMachine
    from statable.model import State, Event
    from statable.global_defs import GlobalDefinitions

    # Build a minimal multi-layer input
    sm1 = StateMachine()
    sm1.layer_name = "Driver"
    sm1.layer_priority = 1
    sm1.add_state(State(name="Idle"))
    sm1.add_state(State(name="Active"))
    sm1.add_event(Event(name="START"))
    sm1.set_initial("Idle")

    sm2 = StateMachine()
    sm2.layer_name = "Application"
    sm2.layer_priority = 5
    sm2.add_state(State(name="Idle"))
    sm2.add_event(Event(name="PING"))
    sm2.set_initial("Idle")

    cfg = CodeGenerationConfig()
    cfg.folder_structure = "by_layer"
    cfg.project_name = "TestProj"
    gen = CCodeGenerator(config=cfg)

    layers = [("Driver", sm1), ("Application", sm2)]
    gd = GlobalDefinitions()
    files = gen.generate_all_layers(layers, gd, None)

    # Check generated file keys
    keys = list(files.keys())
    check("Driver/statable_state_actions_Driver.h",
          "Driver/statable_state_actions_Driver.h" in keys)
    check("Driver/statable_state_actions_Driver.c",
          "Driver/statable_state_actions_Driver.c" in keys)
    check("Application/statable_state_actions_Application.h",
          "Application/statable_state_actions_Application.h" in keys)

    # Content sanity
    driver_h = files.get("Driver/statable_state_actions_Driver.h", "")
    check("Driver .h has Entry decl",
          "void Driver_Entry(STATE_Driver_t state, SystemContext_t *ctx);" in driver_h)

    driver_c = files.get("Driver/statable_state_actions_Driver.c", "")
    check("Driver .c has Entry table",
          "g_Driver_EntryTable[STATE_Driver_MAX]" in driver_c)

    # Super loop contains Do calls
    run_c = files.get("TestProj_run.c", "")
    check("run.c has Driver_Do",
          "Driver_Do(g_Driver_state, &g_ctx);" in run_c)
    check("run.c has Application_Do",
          "Application_Do(g_Application_state, &g_ctx);" in run_c)

    # transitions.c includes state_actions_Driver.h
    trans_c = files.get("Driver/statable_transitions_Driver.c", "")
    check("transitions.c includes state_actions_Driver.h",
          '#include "statable_state_actions_Driver.h"' in trans_c)

    # Process body calls Exit/Entry
    check("Process calls Driver_Exit",
          "Driver_Exit(current_state, ctx);" in trans_c)
    check("Process calls Driver_Entry",
          "Driver_Entry(next_state, ctx);" in trans_c)
    check("Process has state change check",
          "if (next_state != current_state)" in trans_c)


# ======================================================================
# 9. Idempotency: regenerate yields identical content
# ======================================================================
def test_regeneration_idempotent():
    print("\n[9] Regeneration idempotency")
    from codegen.state_actions_generator import StateActionsGenerator

    sm = _make_sm()
    g = StateActionsGenerator()
    g.set_layer("Driver")

    h1 = g.generate_header(sm)
    h2 = g.generate_header(sm)
    check("header idempotent", h1 == h2)

    s1 = g.generate_source(sm)
    s2 = g.generate_source(sm)
    check("source idempotent", s1 == s2)


# ======================================================================
# 10. Edge cases: empty SM / no actions
# ======================================================================
def test_edge_cases():
    print("\n[10] Edge cases")
    from codegen.state_actions_generator import StateActionsGenerator
    from statable.state_machine import StateMachine
    from statable.model import State

    g = StateActionsGenerator()
    g.set_layer("Driver")

    # Empty SM (no states)
    sm = StateMachine()
    sm.layer_name = "Driver"
    h = g.generate_header(sm)
    s = g.generate_source(sm)
    check("empty SM header has decls",
          "void Driver_Entry" in h)
    check("empty SM source has tables",
          "g_Driver_EntryTable" in s)

    # Single state with no actions
    sm2 = StateMachine()
    sm2.layer_name = "Driver"
    sm2.add_state(State(name="Only"))
    s2 = g.generate_source(sm2)
    check("single state: no GUI actions header",
          "GUI-edited actions" not in s2)
    check("single state: custom marker present",
          "Driver_Do_Only_custom" in s2)


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.7.0 P3 (StateActions codegen) test suite")
    print("=" * 70)

    test_module_import()
    test_set_layer_and_names()
    test_role_and_event_calls()
    test_action_line()
    test_generate_header()
    test_generate_source_structure()
    test_per_state_functions_and_markers()
    test_integration_generate_all_layers()
    test_regeneration_idempotent()
    test_edge_cases()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()