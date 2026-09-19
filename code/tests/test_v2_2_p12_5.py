#!/usr/bin/env python3
"""
P12-5 (Group nesting) test suite for StaTable v2.2.

Verifies that TransitionRelation supports recursive nesting via
children: List[TransitionRelation]:

  1. Data model: children field exists, defaults to []
  2. XML round-trip preserves children
  3. Codegen emits nested ifs correctly
  4. Nested group with members at multiple levels
  5. Deep nesting (3 levels)
  6. Coverage analyzer handles nested labels
  7. Backward compat: relation without children

Run:
  python tests/test_v2_2_p12_5.py
"""

import os
import sys
import xml.etree.ElementTree as ET
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


# ======================================================================
# Helpers
# ======================================================================
def make_sm(layer="Driver"):
    from statable.state_machine import StateMachine
    from statable.model import State, Event
    sm = StateMachine()
    sm.layer_name = layer
    for s in ("Idle", "Active", "Error", "Halt"):
        sm.add_state(State(name=s))
    sm.add_event(Event(name="START"))
    return sm


def generate_cell(sm, source="Idle", event="START"):
    from codegen.transition_generator import TransitionGenerator
    gen = TransitionGenerator()
    gen.set_layer(sm.layer_name)
    return gen.generate_transition_cell_functions(sm)


# ======================================================================
# 1. Data model
# ======================================================================
def test_children_field_exists():
    print("\n[1] TransitionRelation.children field")
    from statable.model import TransitionRelation

    r = TransitionRelation()
    check("children attribute exists", hasattr(r, "children"),
          f"attrs={list(vars(r).keys())}")
    check("children defaults to []",
          getattr(r, "children", None) == [])


def test_children_construction():
    print("\n[2] Construct with children")
    from statable.model import TransitionRelation

    child = TransitionRelation(
        kind="group", members=["T3", "T4"],
        shared_condition="cond_B",
    )
    parent = TransitionRelation(
        kind="group", members=["T1", "T2"],
        shared_condition="cond_A",
        children=[child],
    )
    check("parent has 1 child", len(parent.children) == 1)
    check("child shared_condition",
          parent.children[0].shared_condition == "cond_B")
    check("child members",
          parent.children[0].members == ["T3", "T4"])


# ======================================================================
# 3. XML round-trip
# ======================================================================
def test_xml_roundtrip_nested():
    print("\n[3] XML round-trip with nested children")
    from statable.state_machine import StateMachine
    from statable.xml_io import (
        state_machine_to_element, state_machine_from_element,
    )
    from statable.model import (
        State, Event, Transition, TransitionRelation,
    )

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_state(State(name="Error"))
    sm.add_state(State(name="Halt"))
    sm.add_event(Event(name="START"))

    for i, target in enumerate(["Active", "Error", "Halt"], start=1):
        sm.add_transition(Transition(
            source="Idle", event="START",
            condition=f"c{i}", target=target,
            has_else=False, early_return=True, label=f"T{i}",
        ))

    child = TransitionRelation(
        kind="group", members=["T3"],
        shared_condition="cond_B",
    )
    parent = TransitionRelation(
        kind="group", members=["T1", "T2"],
        shared_condition="cond_A",
        children=[child],
    )
    sm.set_relations_for_cell("Idle", "START", [parent])

    elem = state_machine_to_element(sm)
    sm2 = state_machine_from_element(elem)

    rels = sm2.get_relations_for_cell("Idle", "START")
    check("1 relation loaded", len(rels) == 1, f"got {len(rels)}")
    if rels:
        r = rels[0]
        check("parent shared_condition",
              r.shared_condition == "cond_A")
        check("parent members", r.members == ["T1", "T2"])
        check("parent has 1 child", len(r.children) == 1,
              f"got {len(r.children)}")
        if r.children:
            c = r.children[0]
            check("child shared_condition",
                  c.shared_condition == "cond_B")
            check("child members", c.members == ["T3"])


# ======================================================================
# 4. Codegen: 2-level nesting
# ======================================================================
def test_codegen_two_levels():
    print("\n[4] Codegen: 2-level nested group")
    from statable.model import Transition, TransitionRelation

    sm = make_sm()
    for i, target in enumerate(["Active", "Error", "Halt"], start=1):
        sm.add_transition(Transition(
            source="Idle", event="START",
            condition=f"c{i}", target=target,
            has_else=False, early_return=True, label=f"T{i}",
        ))

    child = TransitionRelation(
        kind="group", members=["T3"],
        shared_condition="cond_B",
    )
    parent = TransitionRelation(
        kind="group", members=["T1", "T2"],
        shared_condition="cond_A",
        children=[child],
    )
    sm.set_relations_for_cell("Idle", "START", [parent])

    code = generate_cell(sm)

    check_contains("has outer if (cond_A)", code, "if (cond_A) {")
    check_contains("has inner if (cond_B)", code, "if (cond_B) {")
    check_contains("T1 inside", code, "Transition[T1]")
    check_contains("T2 inside", code, "Transition[T2]")
    check_contains("T3 inside", code, "Transition[T3]")

    # Structural: cond_A before cond_B
    i_a = code.find("if (cond_A)")
    i_b = code.find("if (cond_B)")
    check("cond_A before cond_B", 0 < i_a < i_b,
          f"i_a={i_a}, i_b={i_b}")


# ======================================================================
# 5. Codegen: 3-level nesting
# ======================================================================
def test_codegen_three_levels():
    print("\n[5] Codegen: 3-level nesting")
    from statable.model import Transition, TransitionRelation

    sm = make_sm()
    for i, target in enumerate(["Active", "Error", "Halt"], start=1):
        sm.add_transition(Transition(
            source="Idle", event="START",
            condition=f"c{i}", target=target,
            has_else=False, early_return=True, label=f"T{i}",
        ))

    level3 = TransitionRelation(
        kind="group", members=["T3"], shared_condition="cond_C",
    )
    level2 = TransitionRelation(
        kind="group", members=["T2"], shared_condition="cond_B",
        children=[level3],
    )
    level1 = TransitionRelation(
        kind="group", members=["T1"], shared_condition="cond_A",
        children=[level2],
    )
    sm.set_relations_for_cell("Idle", "START", [level1])

    code = generate_cell(sm)

    check_contains("has cond_A", code, "if (cond_A)")
    check_contains("has cond_B", code, "if (cond_B)")
    check_contains("has cond_C", code, "if (cond_C)")

    i_a = code.find("if (cond_A)")
    i_b = code.find("if (cond_B)")
    i_c = code.find("if (cond_C)")
    check("order A < B < C", 0 < i_a < i_b < i_c,
          f"i_a={i_a}, i_b={i_b}, i_c={i_c}")


# ======================================================================
# 6. Codegen: sibling children (2 children at same level)
# ======================================================================
def test_codegen_sibling_children():
    print("\n[6] Codegen: sibling children under one parent")
    from statable.model import Transition, TransitionRelation

    sm = make_sm()
    for i, target in enumerate(["Active", "Error", "Halt"], start=1):
        sm.add_transition(Transition(
            source="Idle", event="START",
            condition=f"c{i}", target=target,
            has_else=False, early_return=True, label=f"T{i}",
        ))

    c1 = TransitionRelation(
        kind="group", members=["T2"], shared_condition="cond_B")
    c2 = TransitionRelation(
        kind="group", members=["T3"], shared_condition="cond_C")
    parent = TransitionRelation(
        kind="group", members=["T1"], shared_condition="cond_A",
        children=[c1, c2],
    )
    sm.set_relations_for_cell("Idle", "START", [parent])

    code = generate_cell(sm)

    check_contains("has cond_A", code, "if (cond_A)")
    check_contains("has cond_B", code, "if (cond_B)")
    check_contains("has cond_C", code, "if (cond_C)")

    i_a = code.find("if (cond_A)")
    i_b = code.find("if (cond_B)")
    i_c = code.find("if (cond_C)")
    check("order A < B < C (siblings in order)",
          0 < i_a < i_b < i_c,
          f"i_a={i_a}, i_b={i_b}, i_c={i_c}")
def test_backward_compat_no_children():
    print("\n[7] Backward compat: relation without children")
    from statable.model import Transition, TransitionRelation

    sm = make_sm()
    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="c1", target="Active",
        has_else=False, early_return=True, label="T1"))
    sm.set_relations_for_cell("Idle", "START", [
        TransitionRelation(kind="group", members=["T1"],
                           shared_condition="cond_A"),
    ])

    code = generate_cell(sm)
    check_contains("has cond_A", code, "if (cond_A)")
    check_contains("has T1", code, "Transition[T1]")

    # No children -> only one "if (cond_" occurrence (the group itself)
    n = code.count("if (cond_")
    check("only one group if for empty children", n == 1,
          f"got {n} group-level 'if (cond_' in:\n{code}")


# ======================================================================
# 8. Codegen: mixed members + children
# ======================================================================
def test_codegen_members_then_children():
    print("\n[8] Codegen: members emitted before children")
    from statable.model import Transition, TransitionRelation

    sm = make_sm()
    for i, target in enumerate(["Active", "Error", "Halt"], start=1):
        sm.add_transition(Transition(
            source="Idle", event="START",
            condition=f"c{i}", target=target,
            has_else=False, early_return=True, label=f"T{i}",
        ))

    child = TransitionRelation(
        kind="group", members=["T3"], shared_condition="cond_C")
    parent = TransitionRelation(
        kind="group", members=["T1", "T2"], shared_condition="cond_A",
        children=[child],
    )
    sm.set_relations_for_cell("Idle", "START", [parent])

    code = generate_cell(sm)

    i_t1 = code.find("Transition[T1]")
    i_t2 = code.find("Transition[T2]")
    i_t3 = code.find("Transition[T3]")
    i_c = code.find("if (cond_C)")
    check("T1 < T2 < T3",
          0 < i_t1 < i_t2 < i_t3,
          f"i_t1={i_t1}, i_t2={i_t2}, i_t3={i_t3}")
    check("members before inner group",
          i_t1 < i_c and i_t2 < i_c,
          f"i_t1={i_t1}, i_t2={i_t2}, i_c={i_c}")


# ======================================================================
# 9. Coverage analyzer
# ======================================================================
def test_coverage_analyzer_handles_nested():
    print("\n[9] CoverageAnalyzer: nested relations do not crash")
    try:
        from statable_gui.transition_editor_direct.coverage_analyzer import (
            CoverageAnalyzer,
        )
    except ImportError as e:
        RESULT.fail("import CoverageAnalyzer", str(e))
        return

    from statable.model import Transition, TransitionRelation

    sm = make_sm()
    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="c1", target="Active",
        has_else=False, early_return=True, label="T1"))
    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="c2", target="Error",
        has_else=False, early_return=True, label="T2"))

    child = TransitionRelation(
        kind="group", members=["T2"], shared_condition="cond_B")
    parent = TransitionRelation(
        kind="group", members=["T1"], shared_condition="cond_A",
        children=[child],
    )
    sm.set_relations_for_cell("Idle", "START", [parent])

    analyzer = CoverageAnalyzer()
    report = analyzer.analyze_cell(sm, "Idle", "START")
    check("analysis returns report", report is not None)
    check("no crash on nested relations", True)


# ======================================================================
# 10. Deep structure sanity: 4-level
# ======================================================================
def test_codegen_four_levels():
    print("\n[10] Codegen: 4-level nesting (sanity)")
    from statable.model import Transition, TransitionRelation

    sm = make_sm()
    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="c1", target="Active",
        has_else=False, early_return=True, label="T1"))

    l4 = TransitionRelation(
        kind="group", members=["T1"], shared_condition="cond_D")
    l3 = TransitionRelation(
        kind="group", members=[], shared_condition="cond_C",
        children=[l4])
    l2 = TransitionRelation(
        kind="group", members=[], shared_condition="cond_B",
        children=[l3])
    l1 = TransitionRelation(
        kind="group", members=[], shared_condition="cond_A",
        children=[l2])
    sm.set_relations_for_cell("Idle", "START", [l1])

    code = generate_cell(sm)

    check_contains("has cond_A", code, "if (cond_A)")
    check_contains("has cond_B", code, "if (cond_B)")
    check_contains("has cond_C", code, "if (cond_C)")
    check_contains("has cond_D", code, "if (cond_D)")

    i_a = code.find("if (cond_A)")
    i_b = code.find("if (cond_B)")
    i_c = code.find("if (cond_C)")
    i_d = code.find("if (cond_D)")
    check("order A < B < C < D",
          0 < i_a < i_b < i_c < i_d,
          f"i_a={i_a}, i_b={i_b}, i_c={i_c}, i_d={i_d}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2 P12-5 (Group nesting) test suite")
    print("=" * 70)

    test_children_field_exists()
    test_children_construction()
    test_xml_roundtrip_nested()
    test_codegen_two_levels()
    test_codegen_three_levels()
    test_codegen_sibling_children()
    test_backward_compat_no_children()
    test_codegen_members_then_children()
    test_coverage_analyzer_handles_nested()
    test_codegen_four_levels()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()