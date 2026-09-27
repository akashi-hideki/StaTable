#!/usr/bin/env python3
"""
P5 (Validation regressions) test suite for StaTable v2.7.2.

Verifies that TUTORIAL validation does not produce false positives:

  [1] Variable type: uint32_t / uint8_t / volatile uint32_t accepted
  [2] Role function usage: Entry / Exit / PreAction / CellAction counted
  [3] Timer duplicate: group='Timer' SystemVariable + TimerBase is OK
  [4] Integration: vending_machine.xml produces 0 false positives

Run:
  python tests/test_v2_7_p5_validation.py
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class R:
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
        for n, m in self.errors:
            print(f"  - {n}")
            if m:
                print(f"      {m}")
        return self.failed == 0


RESULT = R()


def check(name, cond, msg=""):
    if cond:
        RESULT.ok(name)
    else:
        RESULT.fail(name, msg)
    return cond


# ---------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------
class _FakeVar:
    def __init__(self, name, type="", group="", array_size=0):
        self.name = name
        self.type = type
        self.group = group
        self.array_size = array_size


class _FakeCustomType:
    def __init__(self, name):
        self.name = name


class _FakeTimerBase:
    def __init__(self, name="", derived=None):
        self.variable_name = name
        self.derived = derived or []


class _FakeRoleFunc:
    def __init__(self, name, namespace=""):
        self.name = name
        self.namespace = namespace
        self.qualified_name = (
            f"{namespace}.{name}" if namespace else name)
        self.return_type = "int"
        self.arg1_type = ""
        self.arg1_name = ""
        self.arg2_type = ""
        self.arg2_name = ""


class _FakeActionStep:
    def __init__(self, role_function):
        self.role_function = role_function


class _FakeState:
    def __init__(self, name, entry=None, exit=None, do_actions=None):
        self.name = name
        self.entry = entry or []
        self.exit = exit or []
        self.do_actions = do_actions or []


class _FakeTransition:
    def __init__(self, action="", condition="", pre_actions=None,
                 else_actions=None):
        self.action = action
        self.condition = condition
        self.pre_actions = pre_actions or []
        self.else_actions = else_actions or []


class _FakeSM:
    def __init__(self, states=None, events=None, transitions=None,
                 role_functions=None, cell_actions=None):
        self.states = states or {}
        self.events = events or {}
        self.transitions = transitions or []
        self.role_functions = role_functions or {}
        self._cell_actions = cell_actions or {}
    def get_cell_keys(self):
        return list(self._cell_actions.keys())
    def get_actions_for_cell(self, source, event):
        return self._cell_actions.get((source, event), [])


class _FakeContext:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


# ---------------------------------------------------------------
# [1] Variable type validation
# ---------------------------------------------------------------
def test_variable_types():
    print("\n[1] Variable type validation (uint32_t etc.)")
    from codegen.validate.items.variable_validator import VariableValidator
    v = VariableValidator()

    cases = [
        ("balance", "uint32_t", True),
        ("stock", "uint8_t", True),
        ("tick", "volatile uint32_t", True),
        ("flag", "volatile bool", True),
        ("data", "const uint8_t *", True),
        ("buf", "uint8_t[16]", True),
        ("ptr", "const char *", True),
        ("weird", "unknown_type_t", False),
    ]
    for name, vtype, should_be_valid in cases:
        ctx = _FakeContext(
            variables=[_FakeVar(name, type=vtype, group="Test")],
            custom_types=[],
        )
        issues = v._check_invalid_type(ctx)
        flagged = any(i.code == "VAR_INVALID_TYPE" for i in issues)
        if should_be_valid:
            check(f"'{vtype}' accepted",
                  not flagged,
                  f"got VAR_INVALID_TYPE")
        else:
            check(f"'{vtype}' rejected", flagged)


# ---------------------------------------------------------------
# [2] Unused role function detection
# ---------------------------------------------------------------
def test_unused_role_functions():
    print("\n[2] Role function usage detection")
    from codegen.validate.items.role_function_validator import (
        RoleFunctionValidator,
    )
    v = RoleFunctionValidator()

    rf_entry = _FakeRoleFunc("ClearHwFault", namespace="Driver")
    rf_exit = _FakeRoleFunc("Cleanup", namespace="Driver")
    rf_pre = _FakeRoleFunc("PreCheck", namespace="Vending")
    rf_cond = _FakeRoleFunc("CheckMotorStatus", namespace="Driver")
    rf_cell = _FakeRoleFunc("ReadCoinSensor", namespace="Driver")
    rf_unused = _FakeRoleFunc("NeverUsed", namespace="Driver")

    role_funcs = {rf.name: rf for rf in
                  (rf_entry, rf_exit, rf_pre, rf_cond,
                   rf_cell, rf_unused)}

    states = {
        "Idle": _FakeState(
            "Idle",
            entry=[_FakeActionStep("Driver.ClearHwFault")],
            exit=[_FakeActionStep("Driver.Cleanup")],
        ),
    }
    transitions = [
        _FakeTransition(
            pre_actions=["Vending.PreCheck"],
            condition=("RoleFunc_Driver_CheckMotorStatus"
                       "(transition, ctx) == 0"),
        ),
    ]
    cell_actions = {
        ("Idle", "COIN"): [_FakeActionStep("Driver.ReadCoinSensor")],
    }
    sm = _FakeSM(
        states=states, transitions=transitions,
        role_functions=role_funcs,
        cell_actions=cell_actions,
    )
    ctx = _FakeContext(
        role_functions=role_funcs,
        transitions=transitions,
        state_machine=sm,
    )
    issues = v._check_unused_functions(ctx)
    unused_names = {i.target for i in issues}

    check("Entry action not flagged",
          "ClearHwFault" not in unused_names)
    check("Exit action not flagged",
          "Cleanup" not in unused_names)
    check("PreAction not flagged",
          "PreCheck" not in unused_names)
    check("Condition RoleFunc not flagged",
          "CheckMotorStatus" not in unused_names)
    check("Cell action not flagged",
          "ReadCoinSensor" not in unused_names)
    check("Genuinely unused IS flagged",
          "NeverUsed" in unused_names)


# ---------------------------------------------------------------
# [3] Timer duplicate detection
# ---------------------------------------------------------------
def test_timer_duplicate():
    print("\n[3] Timer duplicate variable detection")
    from codegen.validate.items.timer_validator import TimerValidator
    v = TimerValidator()

    # Case A: group='Timer' SystemVariable + TimerBase (expected)
    ctx_ok = _FakeContext(
        variables=[_FakeVar("g_system_tick",
                            type="uint32_t", group="Timer")],
        timer_base=_FakeTimerBase("g_system_tick"),
        extra_timers=[],
    )
    issues_ok = v._check_duplicate_variables(ctx_ok)
    check("group='Timer' SystemVariable not flagged",
          len(issues_ok) == 0,
          f"got {[i.message for i in issues_ok]}")

    # Case B: non-Timer conflict (real issue)
    ctx_bad = _FakeContext(
        variables=[_FakeVar("counter", type="uint32_t", group="Counter")],
        timer_base=_FakeTimerBase("counter"),
        extra_timers=[],
    )
    issues_bad = v._check_duplicate_variables(ctx_bad)
    check("non-Timer conflict IS flagged",
          any(i.code == "TIMER_DUPLICATE_VARIABLE" for i in issues_bad))

    # Case C: two timer bases share a name (real issue)
    ctx_two = _FakeContext(
        variables=[],
        timer_base=_FakeTimerBase("tick"),
        extra_timers=[_FakeTimerBase("tick")],
    )
    issues_two = v._check_duplicate_variables(ctx_two)
    check("Two timer bases same name IS flagged",
          any(i.code == "TIMER_DUPLICATE_VARIABLE" for i in issues_two))


# ---------------------------------------------------------------
# [4] Integration: vending_machine.xml
# ---------------------------------------------------------------
def test_integration_tutorial():
    print("\n[4] Integration: vending_machine.xml")
    from statable.xml_io import project_from_xml
    from codegen.validate.validator import CodeGenerationValidator

    xml = PROJECT_ROOT / "docs" / "tutorial" / "vending_machine.xml"
    if not xml.exists():
        RESULT.fail("vending_machine.xml exists", f"not found: {xml}")
        return

    tabs, gd, rl, cl, ll, ps = project_from_xml(str(xml))
    check("loaded 3 tabs", len(tabs) == 3)

    all_issues = []
    for tab_name, sm in tabs:
        v = CodeGenerationValidator()
        try:
            result = v.validate(sm, gd)
        except Exception as e:
            RESULT.fail(f"{tab_name}: validation runs",
                        f"{type(e).__name__}: {e}")
            continue
        for issue in (getattr(result, 'issues', []) or []):
            all_issues.append((tab_name, issue.code,
                               getattr(issue, 'target', '')))

    bad_types = [(t, c, n) for (t, c, n) in all_issues
                 if c == "VAR_INVALID_TYPE"]
    check("No VAR_INVALID_TYPE",
          not bad_types,
          f"got {len(bad_types)}: {bad_types[:3]}")

    # [v2.7.2] Some role functions are intentionally defined as
    # public / cross-layer APIs but not called from transitions
    # within the same layer. Accept those via a small whitelist.
    KNOWN_UNUSED_WHITELIST = set()
    unused = [(t, c, n) for (t, c, n) in all_issues
              if c == "ROLE_FUNC_UNUSED"
              and n not in KNOWN_UNUSED_WHITELIST]
    check("No ROLE_FUNC_UNUSED (excluding whitelist)",
          not unused,
          f"got {len(unused)}: {unused[:5]}")

    timer_dups = [(t, c, n) for (t, c, n) in all_issues
                  if c == "TIMER_DUPLICATE_VARIABLE"]
    check("No TIMER_DUPLICATE_VARIABLE",
          not timer_dups,
          f"got {len(timer_dups)}: {timer_dups[:3]}")

    # Debug: print remaining issues (informational)
    print(f"\n  (remaining issues after fix: {len(all_issues)})")
    from collections import Counter
    counts = Counter(c for _, c, _ in all_issues)
    for code, n in sorted(counts.items()):
        print(f"    {code}: {n}")


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
def main():
    print("=" * 70)
    print("  StaTable v2.7.2 P5 (Validation regressions) test suite")
    print("=" * 70)

    test_variable_types()
    test_unused_role_functions()
    test_timer_duplicate()
    test_integration_tutorial()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()