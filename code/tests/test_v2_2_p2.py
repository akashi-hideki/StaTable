#!/usr/bin/env python3
"""
P2 (Code generation) test suite for StaTable v2.2.

Verifies:
  1. Single Commit transition (early_return=True)
  2. Commit + else
  3. Tentative transition (early_return=False)
  4. Unconditional transition (no condition)
  5. Cell actions (before_transitions / after_transitions)
  6. Group + shared_condition
  7. State entry / exit calls
  8. Multiple transitions (T1, T2, T3)
  9. Backward compat: single transition without cell metadata
 10. Backward compat: old-style data (no early_return)

Version: 2.2.6 (2026-09-20 / MISRA-aware codegen expectations)
  - Expected output aligned with v2.5 transition_generator:
      * Single Commit no longer declares `_handled`
        (knownConditionTrueFalse / variableScope fix).
      * Mixed !/&& conditions are parenthesized
        (MISRA C:2012 Rule 12.1 fix).
  - Function signatures (arg / return types) are unchanged.

Run:
  python tests/test_v2_2_p2.py
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


def check_contains(name, haystack, needle, msg=""):
    if needle in haystack:
        RESULT.ok(name)
        return True
    else:
        RESULT.fail(name, msg or f"expected to contain: {needle!r}\n"
                                f"--- got ---\n{haystack}\n-----------")
        return False


def check_not_contains(name, haystack, needle):
    if needle not in haystack:
        RESULT.ok(name)
        return True
    else:
        RESULT.fail(name, f"should NOT contain: {needle!r}\n"
                          f"--- got ---\n{haystack}\n-----------")
        return False


# ======================================================================
# Helpers
# ======================================================================
def make_sm_with_cell(source_states, events, transitions,
                      cell_actions=None, cell_relations=None,
                      layer_name="Driver"):
    from statable.state_machine import StateMachine
    from statable.model import State, Event

    sm = StateMachine()
    sm.layer_name = layer_name
    for s in source_states:
        sm.add_state(State(name=s))
    for e in events:
        sm.add_event(Event(name=e))
    for t in transitions:
        sm.add_transition(t)

    if cell_actions:
        sm.set_actions_for_cell(source_states[0], events[0], cell_actions)
    if cell_relations:
        sm.set_relations_for_cell(source_states[0], events[0], cell_relations)

    return sm


def generate_cell(sm):
    from codegen.transition_generator import TransitionGenerator
    gen = TransitionGenerator()
    gen.set_layer(sm.layer_name)
    return gen.generate_transition_cell_functions(sm)


# ======================================================================
# 1. Single Commit transition
# ======================================================================
def test_single_commit():
    print("\n[1] Single Commit transition")
    from statable.model import Transition

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    sm = make_sm_with_cell(["Idle", "Active"], ["START"], [t])
    code = generate_cell(sm)

    # [v2.2.6] Single Commit: `_handled` is not emitted
    # (would trigger knownConditionTrueFalse / variableScope in cppcheck).
    check_not_contains("no _handled flag (single Commit)",
                       code, "bool _handled = false;")
    check_contains("has plain if (no _handled)",
                   code, "if (cond_A) {")
    check_not_contains("no _handled = true (single Commit)",
                       code, "_handled = true;")
    check_contains("has next_state assign",
                   code, "next_state = STATE_Driver_Active;")
    check_not_contains("no return inside if", code, "return next_state;\n        }")
    check_contains("has return at end", code, "return next_state;")
    check_contains("has Commit marker", code, "Transition[T1] (Commit)")


# ======================================================================
# 2. Commit + else
# ======================================================================
def test_commit_with_else():
    print("\n[2] Commit with else")
    from statable.model import Transition

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=True, else_target="Error",
        early_return=True, label="T1",
    )
    sm = make_sm_with_cell(["Idle", "Active", "Error"], ["START"], [t])
    code = generate_cell(sm)

    # [v2.2.6] Single Commit + else: plain `else`, no `_handled` reference.
    check_contains("has plain else",
                   code, "} else {")
    check_contains("then target Active",
                   code, "next_state = STATE_Driver_Active;")
    check_contains("else target Error",
                   code, "next_state = STATE_Driver_Error;")
    check_not_contains("no _handled = true in else (single Commit)",
                       code, "_handled = true;")


# ======================================================================
# 3. Tentative transition
# ======================================================================
def test_tentative():
    print("\n[3] Tentative transition")
    from statable.model import Transition

    t = Transition(
        source="Idle", event="START",
        condition="cond_B", target="Active",
        has_else=False, early_return=False, label="T1",
    )
    sm = make_sm_with_cell(["Idle", "Active"], ["START"], [t])
    code = generate_cell(sm)

    check_contains("has if (cond_B) without _handled",
                   code, "if (cond_B) {")
    check_not_contains("no !_handled check", code, "!_handled && cond_B")
    check_not_contains("no _handled = true", code, "_handled = true;")
    check_contains("has Tentative marker",
                   code, "Transition[T1] (Tentative)")


def test_tentative_with_else():
    print("\n[3b] Tentative with else")
    from statable.model import Transition

    t = Transition(
        source="Idle", event="START",
        condition="cond_B", target="Active",
        has_else=True, else_target="Error",
        early_return=False, label="T1",
    )
    sm = make_sm_with_cell(["Idle", "Active", "Error"], ["START"], [t])
    code = generate_cell(sm)

    check_contains("has plain else", code, "} else {")
    check_not_contains("no !_handled in else",
                       code, "} else if (!_handled")


# ======================================================================
# 4. Unconditional transition
# ======================================================================
def test_unconditional():
    print("\n[4] Unconditional transition (no condition)")
    from statable.model import Transition

    t = Transition(
        source="Idle", event="START",
        condition="", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    sm = make_sm_with_cell(["Idle", "Active"], ["START"], [t])
    code = generate_cell(sm)

    # [v2.2.6] Single Commit: unconditional uses plain `if (1)`.
    check_contains("uses '1' as condition",
                   code, "if (1) {")


# ======================================================================
# 5. Cell actions (before / after)
# ======================================================================
def test_cell_action_before():
    print("\n[5] Cell actions (before_transitions)")
    from statable.model import Transition, ActionStep

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    actions = [
        ActionStep(role_function="Driver.PreCheck",
                   trigger="before_transitions"),
    ]
    sm = make_sm_with_cell(
        ["Idle", "Active"], ["START"], [t], cell_actions=actions
    )
    code = generate_cell(sm)

    check_contains("has Cell actions header (before_transitions)",
                   code, "Cell actions (before_transitions)")
    check_contains("has PreCheck call",
                   code, "RoleFunc_Driver_PreCheck(transition, ctx);")

    pre_idx = code.find("RoleFunc_Driver_PreCheck")
    trans_idx = code.find("Transition[T1]")
    check("PreCheck before first transition",
          pre_idx > 0 and trans_idx > 0 and pre_idx < trans_idx,
          f"pre_idx={pre_idx}, trans_idx={trans_idx}")


def test_cell_action_after():
    print("\n[5b] Cell actions (after_transitions)")
    from statable.model import Transition, ActionStep

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    actions = [
        ActionStep(role_function="Driver.Cleanup",
                   trigger="after_transitions"),
    ]
    sm = make_sm_with_cell(
        ["Idle", "Active"], ["START"], [t], cell_actions=actions
    )
    code = generate_cell(sm)

    check_contains("has Cell actions header (after_transitions)",
                   code, "Cell actions (after_transitions)")
    check_contains("has Cleanup call",
                   code, "RoleFunc_Driver_Cleanup(transition, ctx);")

    cleanup_idx = code.find("RoleFunc_Driver_Cleanup")
    return_idx = code.find("return next_state;")
    check("Cleanup before final return",
          cleanup_idx > 0 and return_idx > 0 and cleanup_idx < return_idx,
          f"cleanup_idx={cleanup_idx}, return_idx={return_idx}")


def test_cell_action_legacy_always():
    """Legacy 'always' trigger is mapped to before_transitions by code_widget."""
    print("\n[5c] Cell actions: legacy 'always' mapped to before_transitions")
    from statable.model import Transition, ActionStep

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    # Even if we pass trigger="always" (legacy), the model default
    # remains "before_transitions"; code_widget also treats it as such.
    actions = [
        ActionStep(role_function="Driver.Legacy",
                   trigger="before_transitions"),
    ]
    sm = make_sm_with_cell(
        ["Idle", "Active"], ["START"], [t], cell_actions=actions
    )
    code = generate_cell(sm)

    check_contains("has Cell actions header (before_transitions)",
                   code, "Cell actions (before_transitions)")
    check_contains("has Legacy call",
                   code, "RoleFunc_Driver_Legacy(transition, ctx);")


# ======================================================================
# 6. Group + shared_condition
# ======================================================================
def test_group_shared_condition():
    print("\n[6] Group with shared_condition")
    from statable.model import Transition, TransitionRelation

    t1 = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    t2 = Transition(
        source="Idle", event="START",
        condition="cond_B", target="Idle",
        has_else=False, early_return=True, label="T2",
    )
    rels = [
        TransitionRelation(kind="group", members=["T1", "T2"],
                           shared_condition="cond_common"),
    ]
    sm = make_sm_with_cell(
        ["Idle", "Active"], ["START"], [t1, t2], cell_relations=rels
    )
    code = generate_cell(sm)

    check_contains("has Group header", code, "Group (shared_condition)")
    check_contains("has shared_condition if",
                   code, "if (cond_common) {")
    # [v2.2.6] Two Commit transitions -> _handled present; MISRA 12.1 parens.
    check_contains("T1 inside group",
                   code, "        if ((!_handled) && (cond_A))")
    check_contains("T2 inside group",
                   code, "        if ((!_handled) && (cond_B))")


def test_group_closed():
    print("\n[6b] Group is properly closed")
    from statable.model import Transition, TransitionRelation

    t1 = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    t2 = Transition(
        source="Idle", event="START",
        condition="cond_B", target="Idle",
        has_else=False, early_return=True, label="T2",
    )
    t3 = Transition(
        source="Idle", event="START",
        condition="cond_C", target="Error",
        has_else=False, early_return=True, label="T3",
    )
    rels = [
        TransitionRelation(kind="group", members=["T1", "T2"],
                           shared_condition="cond_common"),
    ]
    sm = make_sm_with_cell(
        ["Idle", "Active", "Error"], ["START"], [t1, t2, t3],
        cell_relations=rels
    )
    code = generate_cell(sm)

    # [v2.2.6] MISRA 12.1 parens; 4-space indent (outside group).
    check_contains("T3 outside group (no indent)",
                   code, "    if ((!_handled) && (cond_C))")


# ======================================================================
# 7. State entry / exit
# ======================================================================
def test_entry_exit():
    print("\n[7] State entry / exit calls")
    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_state(State(name="Idle", exit=["Driver.IdleExit"]))
    sm.add_state(State(name="Active", entry=["Driver.ActiveEntry"]))
    sm.add_event(Event(name="START"))

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    sm.add_transition(t)
    code = generate_cell(sm)

    check_contains("has IdleExit call",
                   code, "RoleFunc_Driver_IdleExit(transition, ctx);")
    check_contains("has ActiveEntry call",
                   code, "RoleFunc_Driver_ActiveEntry(transition, ctx);")
    check_contains("has exit comment", code, "/* state exit */")
    check_contains("has entry comment", code, "/* state entry */")


def test_entry_exit_multiple():
    print("\n[7b] Multiple entry / exit functions")
    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_state(State(name="Idle",
                       exit=["Driver.Log", "Driver.StopTimer"]))
    sm.add_state(State(name="Active",
                       entry=["Driver.StartTimer", "Driver.Log"]))
    sm.add_event(Event(name="START"))

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    sm.add_transition(t)
    code = generate_cell(sm)

    check_contains("has Log exit",
                   code, "RoleFunc_Driver_Log(transition, ctx);")
    check_contains("has StopTimer exit",
                   code, "RoleFunc_Driver_StopTimer(transition, ctx);")
    check_contains("has StartTimer entry",
                   code, "RoleFunc_Driver_StartTimer(transition, ctx);")


# ======================================================================
# 8. Multiple transitions
# ======================================================================
def test_three_transitions():
    print("\n[8] Three transitions (T1, T2, T3)")
    from statable.model import Transition

    t1 = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    t2 = Transition(
        source="Idle", event="START",
        condition="cond_B", target="Idle",
        has_else=False, early_return=False, label="T2",
    )
    t3 = Transition(
        source="Idle", event="START",
        condition="cond_C", target="Error",
        has_else=False, early_return=True, label="T3",
    )
    sm = make_sm_with_cell(
        ["Idle", "Active", "Error"], ["START"], [t1, t2, t3]
    )
    code = generate_cell(sm)

    i1 = code.find("Transition[T1]")
    i2 = code.find("Transition[T2]")
    i3 = code.find("Transition[T3]")
    check("T1 before T2", 0 < i1 < i2, f"i1={i1}, i2={i2}")
    check("T2 before T3", 0 < i2 < i3, f"i2={i2}, i3={i3}")

    check_contains("T1 has Commit marker", code, "Transition[T1] (Commit)")
    check_contains("T2 has Tentative marker", code,
                   "Transition[T2] (Tentative)")
    check_contains("T3 has Commit marker", code, "Transition[T3] (Commit)")

    # [v2.2.6] Two Commit (T1, T3) -> _handled present; MISRA 12.1 parens.
    check_contains("T1 uses !_handled",
                   code, "if ((!_handled) && (cond_A))")
    check_contains("T2 uses plain cond",
                   code, "if (cond_B)")
    check_contains("T3 uses !_handled",
                   code, "if ((!_handled) && (cond_C))")


# ======================================================================
# 9. Backward compat
# ======================================================================
def test_backward_single_transition():
    print("\n[9] Backward compat: single transition (no cell metadata)")
    from statable.model import Transition

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False,
    )
    sm = make_sm_with_cell(["Idle", "Active"], ["START"], [t])
    code = generate_cell(sm)

    check_contains("has plain if (cond_A)", code, "if (cond_A) {")
    check_contains("has target assign",
                   code, "next_state = STATE_Driver_Active;")
    check_not_contains("no _handled when all Tentative", code, "_handled")


# ======================================================================
# 10. Structure
# ======================================================================
def test_function_structure():
    print("\n[10] Function structure (signature / body / return)")
    from statable.model import Transition

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    sm = make_sm_with_cell(["Idle", "Active"], ["START"], [t])
    code = generate_cell(sm)

    check_contains("has function signature",
                   code, "static STATE_Driver_t t_Idle_START(")
    check_contains("has transition param",
                   code, "const TransitionContext_Driver_t *transition,")
    check_contains("has ctx param", code, "SystemContext_t *ctx")
    check_contains("has next_state init",
                   code, "STATE_Driver_t next_state = transition->from_state;")
    check_contains("has return", code, "return next_state;")
    check_contains("has closing brace", code, "}")


def test_cell_prototypes():
    print("\n[10b] Cell prototypes")
    from statable.model import Transition
    from codegen.transition_generator import TransitionGenerator

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    sm = make_sm_with_cell(["Idle", "Active"], ["START"], [t])
    gen = TransitionGenerator()
    gen.set_layer(sm.layer_name)
    protos = gen.generate_transition_cell_prototypes(sm)

    check_contains("has section comment",
                   protos, "Cell transition function forward declarations")
    check_contains("has prototype",
                   protos, "static STATE_Driver_t t_Idle_START(")


# ======================================================================
# 11. Full integration
# ======================================================================
def test_full_integration():
    print("\n[11] Full integration (all features)")
    from statable.state_machine import StateMachine
    from statable.model import (
        State, Event, Transition, ActionStep, TransitionRelation,
    )

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_state(State(name="Idle", exit=["Driver.IdleExit"]))
    sm.add_state(State(name="Active", entry=["Driver.ActiveEntry"]))
    sm.add_state(State(name="Error"))
    sm.add_event(Event(name="START"))

    t1 = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    t2 = Transition(
        source="Idle", event="START",
        condition="cond_B", target="Error",
        has_else=True, else_target="Idle",
        early_return=True, label="T2",
    )
    sm.add_transition(t1)
    sm.add_transition(t2)

    sm.set_actions_for_cell("Idle", "START", [
        ActionStep(role_function="Driver.PreCheck",
                   trigger="before_transitions"),
        ActionStep(role_function="Driver.Cleanup",
                   trigger="after_transitions"),
    ])

    code = generate_cell(sm)

    check_contains("has PreCheck", code, "RoleFunc_Driver_PreCheck")
    check_contains("has Cleanup", code, "RoleFunc_Driver_Cleanup")
    check_contains("has IdleExit", code, "RoleFunc_Driver_IdleExit")
    check_contains("has ActiveEntry", code, "RoleFunc_Driver_ActiveEntry")
    check_contains("has T1 Commit", code, "Transition[T1] (Commit)")
    check_contains("has T2 Commit", code, "Transition[T2] (Commit)")
    # [v2.2.6] Two Commit -> MISRA 12.1 parens around mixed !/&&.
    check_contains("has else block",
                   code, "else if ((!_handled) && (!(cond_B)))")

    i_pre = code.find("PreCheck")
    i_t1 = code.find("Transition[T1]")
    i_t2 = code.find("Transition[T2]")
    i_cleanup = code.find("Cleanup")
    i_return = code.rfind("return next_state;")
    check("order: PreCheck < T1 < T2 < Cleanup < return",
          0 < i_pre < i_t1 < i_t2 < i_cleanup < i_return,
          f"indices: {i_pre}, {i_t1}, {i_t2}, {i_cleanup}, {i_return}")


# ======================================================================
# 12. No _handled when all Tentative
# ======================================================================
def test_no_handled_when_all_tentative():
    print("\n[12] No _handled when all Tentative")
    from statable.model import Transition

    t1 = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=False, label="T1",
    )
    t2 = Transition(
        source="Idle", event="START",
        condition="cond_B", target="Error",
        has_else=False, early_return=False, label="T2",
    )
    sm = make_sm_with_cell(["Idle", "Active", "Error"], ["START"], [t1, t2])
    code = generate_cell(sm)

    check_not_contains("no _handled declaration", code, "bool _handled")
    check_not_contains("no _handled usage", code, "_handled")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2 P2 (Codegen) test suite")
    print("=" * 70)

    test_single_commit()
    test_commit_with_else()
    test_tentative()
    test_tentative_with_else()
    test_unconditional()

    test_cell_action_before()
    test_cell_action_after()
    test_cell_action_legacy_always()

    test_group_shared_condition()
    test_group_closed()

    test_entry_exit()
    test_entry_exit_multiple()

    test_three_transitions()

    test_backward_single_transition()

    test_function_structure()
    test_cell_prototypes()

    test_full_integration()
    test_no_handled_when_all_tentative()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()