# tests/test_v2_8_p3_response_validator.py
"""
StaTable v2.8 P3 (ResponseValidator) test suite

Covers SPEC_AI_PROMPT_v1.1 §6 (Phase C-1):
  - ResponseValidationResult structure
  - Schema: action / params / reason
  - Parameters: required + type + enum
  - References: add_transition / remove_transition /
                set_initial / add_action_step /
                add_transition_relation / set_early_return
  - Warnings: low confidence
  - Mixed valid / invalid batches
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codegen.validate.change_actions import ChangeRequest, ChangeActionType
from codegen.validate.response_validator import (
    ResponseValidator, ResponseValidationResult,
)

from statable.state_machine import StateMachine
from statable.model import (
    State, Event, Transition, StateType, EventKind, RoleFunction,
)


# ======================================================================
# Helpers
# ======================================================================
_total = 0
_passed = 0
_failed = 0


def check(label: str, condition: bool) -> None:
    global _total, _passed, _failed
    _total += 1
    if condition:
        _passed += 1
        print(f"  [PASS] {label}")
    else:
        _failed += 1
        print(f"  [FAIL] {label}")


def section(title: str) -> None:
    print()
    print(f"[{title}]")


def make_sm() -> StateMachine:
    """Minimal SM: 2 states, 1 event, 1 role func, 1 labelled transition."""
    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.layer_priority = 5
    sm.add_state(State(name="Idle", type=StateType.NORMAL))
    sm.add_state(State(name="Active", type=StateType.NORMAL))
    sm.add_event(Event(name="START", kind=EventKind.SIGNAL))
    sm.add_role_function(RoleFunction(
        name="Init", namespace="Driver", description="init"))
    sm.add_role_function(RoleFunction(
        name="Stop", namespace="Driver", description="stop"))
    sm.add_transition(Transition(
        source="Idle", event="START", target="Active",
        early_return=False, label="T1", has_else=False,
    ))
    sm.set_initial("Idle")
    return sm


def req(action, params, reason="ok", **kw) -> ChangeRequest:
    return ChangeRequest(
        action=action, params=params, reason=reason, source="ai", **kw)


# ======================================================================
# [1] ResponseValidationResult structure
# ======================================================================
section("1 ResponseValidationResult structure")
result = ResponseValidationResult()
check("valid_requests starts empty", result.valid_requests == [])
check("invalid_requests starts empty", result.invalid_requests == [])
check("warnings starts empty", result.warnings == [])
check("total == 0", result.total == 0)
check("ok == True when empty", result.ok is True)

result.valid_requests.append(req(ChangeActionType.ADD_STATE,
                                 {"name": "X"}))
check("total == 1", result.total == 1)
check("ok still True (no invalids)", result.ok is True)

result.invalid_requests.append((
    req(ChangeActionType.ADD_STATE, {"name": "Y"}), "test"))
check("total == 2", result.total == 2)
check("ok == False when invalid present", result.ok is False)


# ======================================================================
# [2] Valid add_transition
# ======================================================================
section("2 Valid add_transition passes")
sm = make_sm()
v = ResponseValidator()
r = v.validate([req(ChangeActionType.ADD_TRANSITION,
                   {"source": "Idle", "event": "START",
                    "target": "Active"})], sm)
check("1 valid", len(r.valid_requests) == 1)
check("0 invalid", len(r.invalid_requests) == 0)


# ======================================================================
# [3] add_transition: unknown source
# ======================================================================
section("3 add_transition: unknown source is rejected")
r = v.validate([req(ChangeActionType.ADD_TRANSITION,
                   {"source": "Ghost", "event": "START",
                    "target": "Active"})], sm)
check("0 valid", len(r.valid_requests) == 0)
check("1 invalid", len(r.invalid_requests) == 1)
if r.invalid_requests:
    msg = r.invalid_requests[0][1]
    check("reason mentions 'Ghost'", "Ghost" in msg)
    check("reason mentions 'does not exist'",
          "does not exist" in msg)


# ======================================================================
# [4] add_transition: unknown event
# ======================================================================
section("4 add_transition: unknown event is rejected")
r = v.validate([req(ChangeActionType.ADD_TRANSITION,
                   {"source": "Idle", "event": "GHOST",
                    "target": "Active"})], sm)
check("1 invalid", len(r.invalid_requests) == 1)
if r.invalid_requests:
    check("reason mentions event",
          "GHOST" in r.invalid_requests[0][1])


# ======================================================================
# [5] Missing required param
# ======================================================================
section("5 Missing required param is rejected")
r = v.validate([req(ChangeActionType.ADD_TRANSITION,
                   {"source": "Idle", "target": "Active"})], sm)
check("1 invalid", len(r.invalid_requests) == 1)
if r.invalid_requests:
    check("reason mentions 'event'",
          "event" in r.invalid_requests[0][1])


# ======================================================================
# [6] set_initial: unknown state
# ======================================================================
section("6 set_initial: unknown state is rejected")
r = v.validate([req(ChangeActionType.SET_INITIAL,
                   {"state": "Nowhere"})], sm)
check("1 invalid", len(r.invalid_requests) == 1)
# Known state passes
r = v.validate([req(ChangeActionType.SET_INITIAL,
                   {"state": "Idle"})], sm)
check("known state passes", len(r.valid_requests) == 1)


# ======================================================================
# [7] remove_transition: nonexistent
# ======================================================================
section("7 remove_transition: nonexistent is rejected")
r = v.validate([req(ChangeActionType.REMOVE_TRANSITION,
                   {"source": "Idle", "event": "START",
                    "target": "Ghost"})], sm)
check("1 invalid", len(r.invalid_requests) == 1)
r = v.validate([req(ChangeActionType.REMOVE_TRANSITION,
                   {"source": "Idle", "event": "START",
                    "target": "Active"})], sm)
check("existing transition passes", len(r.valid_requests) == 1)


# ======================================================================
# [8] add_action_step: unknown role_function
# ======================================================================
section("8 add_action_step: unknown role_function is rejected")
r = v.validate([req(ChangeActionType.ADD_ACTION_STEP,
                   {"source": "Idle", "event": "START",
                    "role_function": "Ghost.Missing"})], sm)
check("1 invalid", len(r.invalid_requests) == 1)
if r.invalid_requests:
    check("reason mentions role function name",
          "Ghost.Missing" in r.invalid_requests[0][1])


# ======================================================================
# [9] add_action_step: role_function accepted as bare or qualified
# ======================================================================
section("9 add_action_step accepts bare and qualified names")
r = v.validate([req(ChangeActionType.ADD_ACTION_STEP,
                   {"source": "Idle", "event": "START",
                    "role_function": "Init"})], sm)
check("bare name 'Init' passes", len(r.valid_requests) == 1)
r = v.validate([req(ChangeActionType.ADD_ACTION_STEP,
                   {"source": "Idle", "event": "START",
                    "role_function": "Driver.Init"})], sm)
check("qualified name 'Driver.Init' passes",
      len(r.valid_requests) == 1)


# ======================================================================
# [10] add_transition_relation: unknown members
# ======================================================================
section("10 add_transition_relation: unknown member is rejected")
r = v.validate([req(ChangeActionType.ADD_TRANSITION_RELATION,
                   {"source": "Idle", "event": "START",
                    "kind": "exclusive", "members": ["T9"]})], sm)
check("1 invalid", len(r.invalid_requests) == 1)
if r.invalid_requests:
    check("reason mentions label T9",
          "T9" in r.invalid_requests[0][1])
# Valid member (T1 exists in (Idle, START))
r = v.validate([req(ChangeActionType.ADD_TRANSITION_RELATION,
                   {"source": "Idle", "event": "START",
                    "kind": "exclusive", "members": ["T1"]})], sm)
check("known member T1 passes", len(r.valid_requests) == 1)


# ======================================================================
# [11] set_early_return: unknown label
# ======================================================================
section("11 set_early_return: unknown label is rejected")
r = v.validate([req(ChangeActionType.SET_EARLY_RETURN,
                   {"source": "Idle", "event": "START",
                    "label": "T99", "early_return": True})], sm)
check("1 invalid", len(r.invalid_requests) == 1)
r = v.validate([req(ChangeActionType.SET_EARLY_RETURN,
                   {"source": "Idle", "event": "START",
                    "label": "T1", "early_return": True})], sm)
check("known label T1 passes", len(r.valid_requests) == 1)


# ======================================================================
# [12] Empty reason rejected
# ======================================================================
section("12 Empty reason is rejected")
r = v.validate([req(ChangeActionType.ADD_STATE,
                   {"name": "New"}, reason="")], sm)
check("1 invalid", len(r.invalid_requests) == 1)
if r.invalid_requests:
    check("reason mentions 'reason'",
          "reason" in r.invalid_requests[0][1])


# ======================================================================
# [13] Type mismatch rejected
# ======================================================================
section("13 Type mismatch is rejected")
r = v.validate([req(ChangeActionType.ADD_STATE, {"name": 123})], sm)
check("non-str name rejected", len(r.invalid_requests) == 1)
r = v.validate([req(ChangeActionType.ADD_FLAG,
                   {"name": "F", "min_value": "abc"})], sm)
check("non-int min_value rejected", len(r.invalid_requests) == 1)


# ======================================================================
# [14] Enum mismatch rejected
# ======================================================================
section("14 Enum mismatch is rejected")
r = v.validate([req(ChangeActionType.ADD_STATE,
                   {"name": "New", "type": "BOGUS"})], sm)
check("bogus enum rejected", len(r.invalid_requests) == 1)
r = v.validate([req(ChangeActionType.ADD_STATE,
                   {"name": "New", "type": "NORMAL"})], sm)
check("valid enum NORMAL passes", len(r.valid_requests) == 1)


# ======================================================================
# [15] Low confidence warning
# ======================================================================
section("15 Low confidence produces a warning")
r = v.validate([req(ChangeActionType.ADD_STATE,
                   {"name": "New"},
                   id="C-001", confidence=0.3)], sm)
check("1 valid", len(r.valid_requests) == 1)
check("1 warning", len(r.warnings) == 1)
if r.warnings:
    check("warning mentions C-001", "C-001" in r.warnings[0])
    check("warning mentions 0.30", "0.30" in r.warnings[0])
# High confidence → no warning
r = v.validate([req(ChangeActionType.ADD_STATE,
                   {"name": "New"},
                   id="C-002", confidence=0.9)], sm)
check("high confidence no warning", len(r.warnings) == 0)


# ======================================================================
# [16] Mixed valid / invalid batch
# ======================================================================
section("16 Mixed valid / invalid batch")
batch = [
    req(ChangeActionType.ADD_TRANSITION,
        {"source": "Idle", "event": "START", "target": "Active"},
        id="C-001"),
    req(ChangeActionType.ADD_TRANSITION,
        {"source": "Ghost", "event": "START", "target": "Active"},
        id="C-002"),
    req(ChangeActionType.SET_INITIAL, {"state": "Idle"}, id="C-003"),
    req(ChangeActionType.SET_INITIAL, {"state": "Nowhere"}, id="C-004"),
]
r = v.validate(batch, sm)
check("2 valid", len(r.valid_requests) == 2)
check("2 invalid", len(r.invalid_requests) == 2)
check("total == 4", r.total == 4)
check("ok == False", r.ok is False)
valid_ids = {c.id for c in r.valid_requests}
invalid_ids = {c.id for c, _ in r.invalid_requests}
check("valid ids {C-001, C-003}",
      valid_ids == {"C-001", "C-003"})
check("invalid ids {C-002, C-004}",
      invalid_ids == {"C-002", "C-004"})


# ======================================================================
# [17] Empty request list
# ======================================================================
section("17 Empty request list returns empty result")
r = v.validate([], sm)
check("0 valid", len(r.valid_requests) == 0)
check("0 invalid", len(r.invalid_requests) == 0)
check("ok == True", r.ok is True)


# ======================================================================
# [18] sm is None: skip reference checks
# ======================================================================
section("18 sm=None skips reference checks")
r = v.validate([req(ChangeActionType.ADD_TRANSITION,
                   {"source": "Ghost", "event": "Ghost",
                    "target": "Ghost"})], None)
check("valid when sm is None", len(r.valid_requests) == 1)


# ======================================================================
# [19] E2E: realistic AI reply validation
# ======================================================================
section("19 E2E: realistic AI reply validation")
sm_e = StateMachine()
sm_e.layer_name = "Application"
sm_e.add_state(State(name="Error", type=StateType.NORMAL))
sm_e.add_state(State(name="Idle", type=StateType.NORMAL))
sm_e.add_event(Event(name="RESET", kind=EventKind.SIGNAL))
sm_e.set_initial("Idle")

batch = [
    req(ChangeActionType.ADD_TRANSITION,
        {"source": "Error", "event": "RESET", "target": "Idle",
         "action_name": "ClearError"},
        reason="Error has no outgoing transition.",
        id="C-001",
        evidence=["STATE_NO_TRANSITION:Error"],
        priority="high",
        confidence=0.95),
    req(ChangeActionType.ADD_TRANSITION_RELATION,
        {"source": "Accumulating", "event": "ITEM_SELECT",
         "kind": "exclusive", "members": ["T1", "T2"]},
        reason="Make mutually exclusive.",
        id="C-002",
        evidence=["CELL_EXCLUSIVE_NO_RETURN:Accumulating"],
        priority="medium",
        confidence=0.85),
]
r = v.validate(batch, sm_e)
check("C-001 valid", r.valid_requests[0].id == "C-001"
      if len(r.valid_requests) >= 1 else False)
check("C-002 invalid (cell absent)",
      any(c.id == "C-002" for c, _ in r.invalid_requests))
check("1 valid, 1 invalid",
      len(r.valid_requests) == 1 and len(r.invalid_requests) == 1)


# ======================================================================
# Summary
# ======================================================================
print()
print("=" * 70)
print(f"  TOTAL: {_total}  PASSED: {_passed}  FAILED: {_failed}")
print("=" * 70)

sys.exit(0 if _failed == 0 else 1)