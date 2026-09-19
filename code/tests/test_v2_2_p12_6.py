#!/usr/bin/env python3
"""
P12-6 (AI action extensions) test suite for StaTable v2.2 §12-6.

Verifies 7 new ChangeActionType members + their apply() handlers:

  - ADD_CELL / REMOVE_CELL
  - ADD_ACTION_STEP / REMOVE_ACTION_STEP
  - ADD_TRANSITION_RELATION / REMOVE_TRANSITION_RELATION
  - SET_EARLY_RETURN

Each action is expected to:
  1. Exist in ChangeActionType enum
  2. Have an ACTION_DEFINITIONS entry
  3. Have a ChangeApplier handler
  4. Modify the StateMachine as documented

Run:
  python tests/test_v2_2_p12_6.py
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ======================================================================
# Harness
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


def make_sm():
    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition
    sm = StateMachine()
    sm.layer_name = "Driver"
    for s in ("Idle", "Active", "Error"):
        sm.add_state(State(name=s))
    sm.add_event(Event(name="START"))
    sm.add_event(Event(name="STOP"))
    sm.add_transition(Transition(
        source="Idle", event="START", condition="c1",
        target="Active", early_return=False, label="T1"))
    return sm


def make_applier(sm=None):
    from codegen.validate.change_applier import ChangeApplier
    from statable.global_defs import GlobalDefinitions
    sm = sm or make_sm()
    gd = GlobalDefinitions()
    return ChangeApplier(sm, gd), sm, gd


def apply_str(applier, action_str, params):
    """Apply with a raw string action (avoids enum dependency)."""
    from codegen.validate.change_actions import ChangeRequest
    # Try enum-based first; fall back to string
    try:
        from codegen.validate.change_actions import ChangeActionType
        for member in ChangeActionType:
            if member.value == action_str:
                return applier.apply(ChangeRequest(
                    action=member, params=params, reason="test"))
    except Exception:
        pass
    # Fallback: raw ChangeRequest with string action
    req = ChangeRequest.__new__(ChangeRequest)
    req.action = type("A", (), {"value": action_str})()
    req.params = params
    req.reason = "test"
    return applier.apply(req)


# ======================================================================
# 1. ChangeActionType enum members
# ======================================================================
def test_enum_members():
    print("\n[1] ChangeActionType has 7 new members")
    try:
        from codegen.validate.change_actions import ChangeActionType
    except ImportError as e:
        RESULT.fail("import ChangeActionType", str(e))
        return

    expected = [
        ("ADD_CELL", "add_cell"),
        ("REMOVE_CELL", "remove_cell"),
        ("ADD_ACTION_STEP", "add_action_step"),
        ("REMOVE_ACTION_STEP", "remove_action_step"),
        ("ADD_TRANSITION_RELATION", "add_transition_relation"),
        ("REMOVE_TRANSITION_RELATION", "remove_transition_relation"),
        ("SET_EARLY_RETURN", "set_early_return"),
    ]
    for name, value in expected:
        check(f"{name} exists",
              hasattr(ChangeActionType, name),
              f"missing {name}")
        if hasattr(ChangeActionType, name):
            m = getattr(ChangeActionType, name)
            check(f"{name}.value == {value!r}",
                  getattr(m, "value", None) == value,
                  f"got {getattr(m, 'value', None)!r}")


# ======================================================================
# 2. ACTION_DEFINITIONS entries
# ======================================================================
def test_action_definitions():
    print("\n[2] ACTION_DEFINITIONS has 7 new entries")
    from codegen.validate.data.action_definitions import ACTION_DEFINITIONS

    for key in ("add_cell", "remove_cell",
                "add_action_step", "remove_action_step",
                "add_transition_relation", "remove_transition_relation",
                "set_early_return"):
        check(f"'{key}' in ACTION_DEFINITIONS", key in ACTION_DEFINITIONS)


# ======================================================================
# 3. ChangeApplier handlers
# ======================================================================
def test_handlers_registered():
    print("\n[3] ChangeApplier._handlers has new handlers")
    applier, _, _ = make_applier()
    for key in ("add_cell", "remove_cell",
                "add_action_step", "remove_action_step",
                "add_transition_relation", "remove_transition_relation",
                "set_early_return"):
        check(f"handler for '{key}'",
              key in applier._handlers)


# ======================================================================
# 4. add_cell / remove_cell
# ======================================================================
def test_add_cell():
    print("\n[4] add_cell")
    applier, sm, _ = make_applier()
    ok, msg = apply_str(applier, "add_cell",
                        {"source": "Idle", "event": "START"})
    check("add_cell succeeded", ok, msg)
    check("cell_actions has entry for (Idle, START)",
          sm.get_actions_for_cell("Idle", "START") == [])


def test_remove_cell():
    print("\n[5] remove_cell")
    from statable.model import ActionStep, TransitionRelation
    applier, sm, _ = make_applier()
    sm.set_actions_for_cell("Idle", "START",
                            [ActionStep(role_function="X")])
    sm.set_relations_for_cell("Idle", "START",
                              [TransitionRelation(kind="sequential",
                                                  members=["T1"])])
    ok, msg = apply_str(applier, "remove_cell",
                        {"source": "Idle", "event": "START"})
    check("remove_cell succeeded", ok, msg)
    check("cell_actions removed",
          sm.get_actions_for_cell("Idle", "START") == [])
    check("cell_relations removed",
          sm.get_relations_for_cell("Idle", "START") == [])


# ======================================================================
# 6. add_action_step / remove_action_step
# ======================================================================
def test_add_action_step():
    print("\n[6] add_action_step")
    applier, sm, _ = make_applier()
    ok, msg = apply_str(applier, "add_action_step", {
        "source": "Idle", "event": "START",
        "role_function": "Driver.PreCheck",
        "trigger": "before_transitions",
    })
    check("add_action_step succeeded", ok, msg)
    actions = sm.get_actions_for_cell("Idle", "START")
    check("1 action added", len(actions) == 1, f"got {len(actions)}")
    if actions:
        check("role_function matches",
              actions[0].role_function == "Driver.PreCheck")
        check("trigger matches",
              actions[0].trigger == "before_transitions")


def test_remove_action_step():
    print("\n[7] remove_action_step")
    from statable.model import ActionStep
    applier, sm, _ = make_applier()
    sm.set_actions_for_cell("Idle", "START", [
        ActionStep(role_function="Driver.A", trigger="before_transitions"),
        ActionStep(role_function="Driver.B", trigger="after_transitions"),
    ])
    ok, msg = apply_str(applier, "remove_action_step", {
        "source": "Idle", "event": "START",
        "role_function": "Driver.A",
    })
    check("remove_action_step succeeded", ok, msg)
    actions = sm.get_actions_for_cell("Idle", "START")
    check("1 action remains", len(actions) == 1)
    if actions:
        check("remaining is Driver.B",
              actions[0].role_function == "Driver.B")


# ======================================================================
# 8. add_transition_relation / remove_transition_relation
# ======================================================================
def test_add_transition_relation():
    print("\n[8] add_transition_relation")
    applier, sm, _ = make_applier()
    ok, msg = apply_str(applier, "add_transition_relation", {
        "source": "Idle", "event": "START",
        "kind": "group",
        "members": ["T1"],
        "shared_condition": "cond_A",
    })
    check("add_transition_relation succeeded", ok, msg)
    rels = sm.get_relations_for_cell("Idle", "START")
    check("1 relation added", len(rels) == 1, f"got {len(rels)}")
    if rels:
        check("kind == group", rels[0].kind == "group")
        check("members == ['T1']", rels[0].members == ["T1"])
        check("shared_condition",
              rels[0].shared_condition == "cond_A")


def test_remove_transition_relation():
    print("\n[9] remove_transition_relation")
    from statable.model import TransitionRelation
    applier, sm, _ = make_applier()
    sm.set_relations_for_cell("Idle", "START", [
        TransitionRelation(kind="group", members=["T1"],
                           shared_condition="cond_A"),
        TransitionRelation(kind="exclusive", members=["T1"]),
    ])
    ok, msg = apply_str(applier, "remove_transition_relation", {
        "source": "Idle", "event": "START",
        "kind": "group",
        "shared_condition": "cond_A",
    })
    check("remove_transition_relation succeeded", ok, msg)
    rels = sm.get_relations_for_cell("Idle", "START")
    check("1 relation remains", len(rels) == 1)
    if rels:
        check("remaining kind is exclusive",
              rels[0].kind == "exclusive")


# ======================================================================
# 10. set_early_return
# ======================================================================
def test_set_early_return():
    print("\n[10] set_early_return")
    applier, sm, _ = make_applier()
    # Initial state: T1 has early_return=False
    t = sm.transitions[0]
    check("T1 initial early_return is False",
          t.early_return is False)

    ok, msg = apply_str(applier, "set_early_return", {
        "source": "Idle", "event": "START",
        "label": "T1",
        "early_return": True,
    })
    check("set_early_return succeeded", ok, msg)
    check("T1 early_return is now True",
          sm.transitions[0].early_return is True)


# ======================================================================
# 11. Error cases
# ======================================================================
def test_error_missing_params():
    print("\n[11] Error cases: missing required params")
    applier, _, _ = make_applier()
    ok, msg = apply_str(applier, "add_action_step", {
        "source": "Idle", "event": "START",
        # role_function missing
    })
    check("add_action_step fails without role_function", not ok)
    ok, msg = apply_str(applier, "add_transition_relation", {
        "source": "Idle", "event": "START",
        "kind": "group",
        # shared_condition missing for group
    })
    check("group without shared_condition fails", not ok)


def test_error_unknown_target():
    print("\n[12] Error cases: unknown target")
    applier, _, _ = make_applier()
    ok, msg = apply_str(applier, "add_action_step", {
        "source": "NoSuchState", "event": "START",
        "role_function": "X",
        "trigger": "before_transitions",
    })
    check("add_action_step on unknown source fails", not ok)
    ok, msg = apply_str(applier, "set_early_return", {
        "source": "Idle", "event": "START",
        "label": "T99",
        "early_return": True,
    })
    check("set_early_return on unknown label fails", not ok)


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2 P12-6 (AI action extensions) test suite")
    print("=" * 70)

    test_enum_members()
    test_action_definitions()
    test_handlers_registered()

    test_add_cell()
    test_remove_cell()

    test_add_action_step()
    test_remove_action_step()

    test_add_transition_relation()
    test_remove_transition_relation()

    test_set_early_return()

    test_error_missing_params()
    test_error_unknown_target()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()