#!/usr/bin/env python3
"""
P5 (Cell validation) test suite for StaTable v2.2.

Verifies 8 cell-level rules:
  CELL_EMPTY_CONDITION
  CELL_DUPLICATE_LABEL
  CELL_DANGLING_RELATION
  CELL_UNREACHABLE_TRANSITION
  CELL_OVERLAP_POSSIBLE
  CELL_DUPLICATE_TARGET
  CELL_EXCLUSIVE_NO_RETURN
  CELL_EMPTY_TARGET

Import path: codegen.cell_validator (NOT codegen.validate.items.cell_validator)
  because the legacy codegen/validate/__init__.py has a broken import chain.

Run:
  python tests/test_v2_2_p5.py
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
    from statable.model import State, Event
    sm = StateMachine()
    sm.layer_name = "Driver"
    for s in ("Idle", "Active", "Error", "Halt"):
        sm.add_state(State(name=s))
    sm.add_event(Event(name="START"))
    sm.add_event(Event(name="STOP"))
    return sm


def rule_codes(issues, code):
    return [i for i in issues if getattr(i, "code", "") == code]


# ======================================================================
# 1. CELL_EMPTY_CONDITION
# ======================================================================
def test_empty_condition():
    print("\n[1] CELL_EMPTY_CONDITION")
    from statable.model import Transition
    from codegen.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="", target="",
                                 early_return=False, label="T1"))
    issues = CellValidator().validate(sm)
    hits = rule_codes(issues, "CELL_EMPTY_CONDITION")
    check("warning emitted", len(hits) == 1, f"got {len(hits)}")
    if hits:
        check("level is Warning", hits[0].level == "Warning",
              f"got {hits[0].level}")


# ======================================================================
# 2. CELL_DUPLICATE_LABEL
# ======================================================================
def test_duplicate_label():
    print("\n[2] CELL_DUPLICATE_LABEL")
    from statable.model import Transition
    from codegen.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 early_return=True, label="T1"))
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cB", target="Error",
                                 early_return=True, label="T1"))
    issues = CellValidator().validate(sm)
    hits = rule_codes(issues, "CELL_DUPLICATE_LABEL")
    check("error emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("level is Error", hits[0].level == "Error",
              f"got {hits[0].level}")


# ======================================================================
# 3. CELL_DANGLING_RELATION
# ======================================================================
def test_dangling_relation():
    print("\n[3] CELL_DANGLING_RELATION")
    from statable.model import Transition, TransitionRelation
    from codegen.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 early_return=True, label="T1"))
    sm.set_relations_for_cell("Idle", "START", [
        TransitionRelation(kind="sequential", members=["T1", "T99"]),
    ])
    issues = CellValidator().validate(sm)
    hits = rule_codes(issues, "CELL_DANGLING_RELATION")
    check("error emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("level is Error", hits[0].level == "Error",
              f"got {hits[0].level}")
        check("mentions T99", "T99" in hits[0].message,
              f"got {hits[0].message}")


# ======================================================================
# 4. CELL_UNREACHABLE_TRANSITION
# ======================================================================
def test_unreachable_transition():
    print("\n[4] CELL_UNREACHABLE_TRANSITION")
    from statable.model import Transition
    from codegen.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 has_else=True, else_target="Error",
                                 early_return=True, label="T1"))
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cB", target="Halt",
                                 has_else=False,
                                 early_return=True, label="T2"))
    issues = CellValidator().validate(sm)
    hits = rule_codes(issues, "CELL_UNREACHABLE_TRANSITION")
    check("warning emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("mentions T2", "T2" in hits[0].message,
              f"got {hits[0].message}")


# ======================================================================
# 5. CELL_OVERLAP_POSSIBLE
# ======================================================================
def test_overlap_possible():
    print("\n[5] CELL_OVERLAP_POSSIBLE")
    from statable.model import Transition
    from codegen.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 early_return=True, label="T1"))
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Error",
                                 early_return=True, label="T2"))
    issues = CellValidator().validate(sm)
    hits = rule_codes(issues, "CELL_OVERLAP_POSSIBLE")
    check("warning emitted", len(hits) >= 1, f"got {len(hits)}")


# ======================================================================
# 6. CELL_DUPLICATE_TARGET
# ======================================================================
def test_duplicate_target():
    print("\n[6] CELL_DUPLICATE_TARGET")
    from statable.model import Transition
    from codegen.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 early_return=True, label="T1"))
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cB", target="Active",
                                 early_return=True, label="T2"))
    issues = CellValidator().validate(sm)
    hits = rule_codes(issues, "CELL_DUPLICATE_TARGET")
    check("info emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("level is Info", hits[0].level == "Info",
              f"got {hits[0].level}")
        check("mentions Active", "Active" in hits[0].message,
              f"got {hits[0].message}")


# ======================================================================
# 7. CELL_EXCLUSIVE_NO_RETURN
# ======================================================================
def test_exclusive_no_return():
    print("\n[7] CELL_EXCLUSIVE_NO_RETURN")
    from statable.model import Transition, TransitionRelation
    from codegen.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 early_return=False, label="T1"))
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cB", target="Error",
                                 early_return=True, label="T2"))
    sm.set_relations_for_cell("Idle", "START", [
        TransitionRelation(kind="exclusive", members=["T1", "T2"]),
    ])
    issues = CellValidator().validate(sm)
    hits = rule_codes(issues, "CELL_EXCLUSIVE_NO_RETURN")
    check("info emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("mentions T1", "T1" in hits[0].message,
              f"got {hits[0].message}")


# ======================================================================
# 8. CELL_EMPTY_TARGET
# ======================================================================
def test_empty_target():
    print("\n[8] CELL_EMPTY_TARGET")
    from statable.model import Transition
    from codegen.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="",
                                 early_return=False, label="T1"))
    issues = CellValidator().validate(sm)
    hits = rule_codes(issues, "CELL_EMPTY_TARGET")
    check("warning emitted", len(hits) >= 1, f"got {len(hits)}")


# ======================================================================
# 9. Clean sample (no false positives)
# ======================================================================
def test_clean_sample():
    print("\n[9] Clean sample: no errors")
    from statable.sample_data import create_sample_state_machine
    from codegen.cell_validator import CellValidator

    sm = create_sample_state_machine()
    issues = CellValidator().validate(sm)
    errors = [i for i in issues if i.level == "Error"]
    check("no errors in sample", len(errors) == 0,
          f"got {[(i.code, i.message) for i in errors]}")


# ======================================================================
# 10. Issue structure
# ======================================================================
def test_issue_structure():
    print("\n[10] Issue structure")
    from statable.model import Transition
    from codegen.cell_validator import CellValidator, Issue

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="", target="",
                                 early_return=False, label="T1"))
    issues = CellValidator().validate(sm)
    check("returns list", isinstance(issues, list))
    check("at least one issue", len(issues) >= 1)
    if issues:
        i = issues[0]
        check("is Issue instance", isinstance(i, Issue))
        check("has code", hasattr(i, "code") and i.code)
        check("has level", hasattr(i, "level") and i.level)
        check("has message", hasattr(i, "message") and i.message)
        check("has location", hasattr(i, "location"))


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2 P5 (Cell validation) test suite")
    print("=" * 70)

    test_empty_condition()
    test_duplicate_label()
    test_dangling_relation()
    test_unreachable_transition()
    test_overlap_possible()
    test_duplicate_target()
    test_exclusive_no_return()
    test_empty_target()
    test_clean_sample()
    test_issue_structure()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()