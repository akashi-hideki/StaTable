#!/usr/bin/env python3
"""StaTable F-3 test suite: pending_event atomic read-then-clear.

Verifies the generated GetNextEvent body:
  - Read-then-clear is wrapped in STATABLE_ENTER/EXIT_CRITICAL
  - pending_event is declared at function top (not inside if-block)
  - Consecutive-count overflow still works
  - Queue drain still protected

Run:
  python tests/test_v2_5_p10.py
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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
        return self.failed == 0


R = TestResult()


def check(name, cond, msg=""):
    if cond:
        R.ok(name)
    else:
        R.fail(name, msg)
    return cond


def _make_sm():
    from statable.state_machine import StateMachine
    from statable.model import State, Event
    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_state(State(name="Idle"))
    sm.add_event(Event(name="START"))
    return sm


# ======================================================================
# [1] Generated body contains atomic read-then-clear
# ======================================================================
def test_atomic_read_clear():
    print("\n[1] Atomic read-then-clear")

    from codegen.transition_generator import TransitionGenerator
    gen = TransitionGenerator()
    gen.set_layer("Driver")
    out = gen.generate_get_next_event_function(_make_sm())

    check("has [F-3] comment",
          "[F-3] Read-then-clear pending_event atomically." in out,
          f"got:\n{out}")
    check("evt declared at top",
          "    EVENT_Driver_t evt = EVENT_Driver_NONE;\n" in out,
          f"got:\n{out}")

    # Verify order: ENTER_CRITICAL -> read -> clear -> EXIT_CRITICAL
    i_enter = out.find("STATABLE_ENTER_CRITICAL()")
    i_read = out.find("evt = (EVENT_Driver_t)ctx->pending_event")
    i_clear = out.find("ctx->pending_event_valid = false")
    i_exit = out.find("STATABLE_EXIT_CRITICAL()")

    check("ENTER_CRITICAL before read",
          0 < i_enter < i_read,
          f"i_enter={i_enter}, i_read={i_read}")
    check("read before clear",
          0 < i_read < i_clear,
          f"i_read={i_read}, i_clear={i_clear}")
    check("clear before EXIT_CRITICAL",
          0 < i_clear < i_exit,
          f"i_clear={i_clear}, i_exit={i_exit}")


# ======================================================================
# [2] Consecutive-count overflow behavior preserved
# ======================================================================
def test_overflow_still_works():
    print("\n[2] Consecutive-count overflow preserved")

    from codegen.transition_generator import TransitionGenerator
    gen = TransitionGenerator()
    gen.set_layer("Driver")
    out = gen.generate_get_next_event_function(_make_sm())

    check("MAX_CONSECUTIVE_PENDING_EVENTS check",
          "consecutive_count > MAX_CONSECUTIVE_PENDING_EVENTS" in out)
    check("returns NONE on overflow",
          out.count("return EVENT_Driver_NONE;") >= 2,
          f"count={out.count('return EVENT_Driver_NONE;')}")


# ======================================================================
# [3] Queue drain still protected
# ======================================================================
def test_queue_drain_still_protected():
    print("\n[3] Queue drain still protected")

    from codegen.transition_generator import TransitionGenerator
    gen = TransitionGenerator()
    gen.set_layer("Driver")
    out = gen.generate_get_next_event_function(_make_sm())

    check("queue_Driver referenced",
          "ctx->queue_Driver" in out)
    check("queue drain has STATABLE_ENTER_CRITICAL",
          out.count("STATABLE_ENTER_CRITICAL()") >= 2,
          f"count={out.count('STATABLE_ENTER_CRITICAL()')}")
    check("queue drain has STATABLE_EXIT_CRITICAL",
          out.count("STATABLE_EXIT_CRITICAL()") >= 2,
          f"count={out.count('STATABLE_EXIT_CRITICAL()')}")


# ======================================================================
# [4] Structure sanity
# ======================================================================
def test_structure():
    print("\n[4] Structure sanity")

    from codegen.transition_generator import TransitionGenerator
    gen = TransitionGenerator()
    gen.set_layer("Driver")
    out = gen.generate_get_next_event_function(_make_sm())

    check("braces balanced",
          out.count("{") == out.count("}"),
          f"open={out.count('{')}, close={out.count('}')}")
    check("has function signature",
          "EVENT_Driver_t StateMachine_GetNextEvent_Driver(" in out)


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable F-3 (pending_event atomic read-then-clear)")
    print("=" * 70)

    test_atomic_read_clear()
    test_overflow_still_works()
    test_queue_drain_still_protected()
    test_structure()

    ok = R.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()