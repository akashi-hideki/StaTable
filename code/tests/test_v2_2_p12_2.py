#!/usr/bin/env python3
"""
P12-2 (Cell validator integration) test suite for StaTable v2.2.

Verifies that the cell_validator is now integrated into the
existing validate layer (codegen/validate/):

  1. codegen.validate.items.cell_validator.CellValidator exists
  2. category = 'cell', 8 rules registered
  3. Each rule fires on the appropriate input
  4. Issues are ValidationIssue (not the standalone Issue)
  5. Severity uses ValidationSeverity enum
  6. CodeGenerationValidator picks up the 'cell' category
  7. Clean sample produces no errors
  8. Rules defined in VALIDATION_RULES['cell']

Run:
  python tests/test_v2_2_p12_2.py
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


# ======================================================================
# Helpers
# ======================================================================
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


def make_context(sm):
    from codegen.validate.models import ValidationContext
    return ValidationContext(state_machine=sm, global_defs=None)


def rule_issues(issues, code):
    return [i for i in issues if getattr(i, "code", "") == code]


# ======================================================================
# 1. Import / structure
# ======================================================================
def test_import():
    print("\n[1] CellValidator importable from validate.items")
    try:
        from codegen.validate.items.cell_validator import CellValidator
        check("CellValidator imported", True)
    except ImportError as e:
        check("CellValidator imported", False, str(e))


def test_category():
    print("\n[2] CellValidator.category == 'cell'")
    from codegen.validate.items.cell_validator import CellValidator
    check("category is 'cell'", CellValidator.category == "cell",
          f"got {CellValidator.category!r}")


def test_rules_registered():
    print("\n[3] 8 rules registered")
    from codegen.validate.items.cell_validator import CellValidator
    v = CellValidator()
    expected = {
        "CELL_EMPTY_CONDITION",
        "CELL_DUPLICATE_LABEL",
        "CELL_DANGLING_RELATION",
        "CELL_UNREACHABLE_TRANSITION",
        "CELL_OVERLAP_POSSIBLE",
        "CELL_DUPLICATE_TARGET",
        "CELL_EXCLUSIVE_NO_RETURN",
        "CELL_EMPTY_TARGET",
    }
    actual = set(v.rules.keys())
    check("all 8 codes registered", actual == expected,
          f"missing={expected - actual}, extra={actual - expected}")


def test_base_validator_subclass():
    print("\n[4] Subclass of BaseValidator")
    from codegen.validate.items.cell_validator import CellValidator
    from codegen.validate.items.base_validator import BaseValidator
    check("is BaseValidator subclass",
          issubclass(CellValidator, BaseValidator))


# ======================================================================
# 5. Individual rules
# ======================================================================
def test_empty_condition():
    print("\n[5] CELL_EMPTY_CONDITION")
    from statable.model import Transition
    from codegen.validate.items.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="", target="",
                                 early_return=False, label="T1"))
    v = CellValidator()
    issues = v.validate(make_context(sm))
    hits = rule_issues(issues, "CELL_EMPTY_CONDITION")
    check("warning emitted", len(hits) == 1, f"got {len(hits)}")
    if hits:
        check("severity is WARNING",
              hits[0].severity.name == "WARNING",
              f"got {hits[0].severity}")
        check("category is 'cell'", hits[0].category == "cell")


def test_duplicate_label():
    print("\n[6] CELL_DUPLICATE_LABEL")
    from statable.model import Transition
    from codegen.validate.items.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 early_return=True, label="T1"))
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cB", target="Error",
                                 early_return=True, label="T1"))
    v = CellValidator()
    issues = v.validate(make_context(sm))
    hits = rule_issues(issues, "CELL_DUPLICATE_LABEL")
    check("error emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("severity is ERROR",
              hits[0].severity.name == "ERROR",
              f"got {hits[0].severity}")


def test_dangling_relation():
    print("\n[7] CELL_DANGLING_RELATION")
    from statable.model import Transition, TransitionRelation
    from codegen.validate.items.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 early_return=True, label="T1"))
    sm.set_relations_for_cell("Idle", "START", [
        TransitionRelation(kind="sequential", members=["T1", "T99"]),
    ])
    v = CellValidator()
    issues = v.validate(make_context(sm))
    hits = rule_issues(issues, "CELL_DANGLING_RELATION")
    check("error emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("mentions T99", "T99" in hits[0].message,
              f"got {hits[0].message}")


def test_unreachable():
    print("\n[8] CELL_UNREACHABLE_TRANSITION")
    from statable.model import Transition
    from codegen.validate.items.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 has_else=True, else_target="Error",
                                 early_return=True, label="T1"))
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cB", target="Halt",
                                 has_else=False,
                                 early_return=True, label="T2"))
    v = CellValidator()
    issues = v.validate(make_context(sm))
    hits = rule_issues(issues, "CELL_UNREACHABLE_TRANSITION")
    check("warning emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("mentions T2", "T2" in hits[0].message,
              f"got {hits[0].message}")


def test_overlap():
    print("\n[9] CELL_OVERLAP_POSSIBLE")
    from statable.model import Transition
    from codegen.validate.items.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 early_return=True, label="T1"))
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Error",
                                 early_return=True, label="T2"))
    v = CellValidator()
    issues = v.validate(make_context(sm))
    hits = rule_issues(issues, "CELL_OVERLAP_POSSIBLE")
    check("warning emitted", len(hits) >= 1, f"got {len(hits)}")


def test_duplicate_target():
    print("\n[10] CELL_DUPLICATE_TARGET")
    from statable.model import Transition
    from codegen.validate.items.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="Active",
                                 early_return=True, label="T1"))
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cB", target="Active",
                                 early_return=True, label="T2"))
    v = CellValidator()
    issues = v.validate(make_context(sm))
    hits = rule_issues(issues, "CELL_DUPLICATE_TARGET")
    check("info emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("severity is INFO", hits[0].severity.name == "INFO",
              f"got {hits[0].severity}")
        check("mentions Active", "Active" in hits[0].message)


def test_exclusive_no_return():
    print("\n[11] CELL_EXCLUSIVE_NO_RETURN")
    from statable.model import Transition, TransitionRelation
    from codegen.validate.items.cell_validator import CellValidator

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
    v = CellValidator()
    issues = v.validate(make_context(sm))
    hits = rule_issues(issues, "CELL_EXCLUSIVE_NO_RETURN")
    check("info emitted", len(hits) >= 1, f"got {len(hits)}")
    if hits:
        check("mentions T1", "T1" in hits[0].message)


def test_empty_target():
    print("\n[12] CELL_EMPTY_TARGET")
    from statable.model import Transition
    from codegen.validate.items.cell_validator import CellValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="cA", target="",
                                 early_return=False, label="T1"))
    v = CellValidator()
    issues = v.validate(make_context(sm))
    hits = rule_issues(issues, "CELL_EMPTY_TARGET")
    check("warning emitted", len(hits) >= 1, f"got {len(hits)}")


# ======================================================================
# 13. Issue type / severity
# ======================================================================
def test_issue_is_validation_issue():
    print("\n[13] Issues are ValidationIssue (validate.models)")
    from statable.model import Transition
    from codegen.validate.items.cell_validator import CellValidator
    from codegen.validate.models import ValidationIssue

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="", target="",
                                 early_return=False, label="T1"))
    v = CellValidator()
    issues = v.validate(make_context(sm))
    check("at least one issue", len(issues) >= 1)
    if issues:
        i = issues[0]
        check("is ValidationIssue", isinstance(i, ValidationIssue))
        check("has category", hasattr(i, "category") and i.category == "cell")
        check("has code", hasattr(i, "code") and bool(i.code))
        check("has message", hasattr(i, "message") and bool(i.message))
        check("has severity", hasattr(i, "severity"))


# ======================================================================
# 14. Integration with CodeGenerationValidator
# ======================================================================
def test_code_generation_validator_picks_up_cell():
    print("\n[14] CodeGenerationValidator registers 'cell'")
    from codegen.validate.validator import CodeGenerationValidator

    v = CodeGenerationValidator()
    cats = v.get_categories()
    check("'cell' in categories", "cell" in cats, f"got {cats}")


def test_integrated_run():
    print("\n[15] Integrated validation runs cell rules")
    from statable.model import Transition
    from codegen.validate.validator import CodeGenerationValidator

    sm = make_sm()
    sm.add_transition(Transition(source="Idle", event="START",
                                 condition="", target="",
                                 early_return=False, label="T1"))

    v = CodeGenerationValidator()
    result = v.validate(sm, None)
    cell_issues = [i for i in result.issues if i.category == "cell"]
    check("cell issues present in result",
          len(cell_issues) >= 1,
          f"got {len(cell_issues)} cell issues")


# ======================================================================
# 16. VALIDATION_RULES['cell'] defined
# ======================================================================
def test_validation_rules_has_cell():
    print("\n[16] VALIDATION_RULES has 'cell' category")
    from codegen.validate.data.validation_rules import VALIDATION_RULES

    check("'cell' in VALIDATION_RULES", "cell" in VALIDATION_RULES,
          f"keys={list(VALIDATION_RULES.keys())}")
    if "cell" in VALIDATION_RULES:
        expected = {
            "CELL_EMPTY_CONDITION",
            "CELL_DUPLICATE_LABEL",
            "CELL_DANGLING_RELATION",
            "CELL_UNREACHABLE_TRANSITION",
            "CELL_OVERLAP_POSSIBLE",
            "CELL_DUPLICATE_TARGET",
            "CELL_EXCLUSIVE_NO_RETURN",
            "CELL_EMPTY_TARGET",
        }
        actual = set(VALIDATION_RULES["cell"].keys())
        check("all 8 rules defined", actual == expected,
              f"missing={expected - actual}, extra={actual - expected}")


# ======================================================================
# 17. Clean sample
# ======================================================================
def test_clean_sample():
    print("\n[17] Clean sample: no cell errors")
    from statable.sample_data import create_sample_state_machine
    from codegen.validate.items.cell_validator import CellValidator

    sm = create_sample_state_machine()
    v = CellValidator()
    issues = v.validate(make_context(sm))
    errors = [i for i in issues if i.severity.name == "ERROR"]
    check("no errors in sample", len(errors) == 0,
          f"got {[(i.code, i.message) for i in errors]}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2 P12-2 (Cell validator integration) test suite")
    print("=" * 70)

    test_import()
    test_category()
    test_rules_registered()
    test_base_validator_subclass()

    test_empty_condition()
    test_duplicate_label()
    test_dangling_relation()
    test_unreachable()
    test_overlap()
    test_duplicate_target()
    test_exclusive_no_return()
    test_empty_target()

    test_issue_is_validation_issue()
    test_code_generation_validator_picks_up_cell()
    test_integrated_run()
    test_validation_rules_has_cell()
    test_clean_sample()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()