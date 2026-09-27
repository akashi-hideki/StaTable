# tests/test_v2_8_p2_response_parser.py
"""
StaTable v2.8 P2 (AI response parser) test suite

Covers SPEC_AI_PROMPT_v1.1 Phase B:
  - ChangeRequest extended fields (id / evidence / priority / confidence)
  - to_dict / from_dict round-trip
  - Backward-compatible from_dict (missing new fields)
  - ACTION_MAPPING covers all 17 ChangeActionType values
  - <response>...</response> extraction
  - <json>...</json> extraction (legacy)
  - { ... } fallback extraction
  - 17 actions parsed end-to-end
  - Extended fields preserved through parse
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codegen.validate.change_actions import ChangeRequest, ChangeActionType
from codegen.validate.response_parser import AIResponseParser


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


# ======================================================================
# [1] ChangeRequest extended fields
# ======================================================================
section("1 ChangeRequest has extended fields with defaults")
cr = ChangeRequest(action=ChangeActionType.ADD_TRANSITION,
                   params={"source": "A", "event": "E", "target": "B"},
                   reason="test")
check("default id == ''", cr.id == "")
check("default evidence == []", cr.evidence == [])
check("default priority == 'medium'", cr.priority == "medium")
check("default confidence == 1.0", cr.confidence == 1.0)
check("original fields preserved (action)",
      cr.action == ChangeActionType.ADD_TRANSITION)
check("original fields preserved (params)", cr.params["source"] == "A")
check("original fields preserved (reason)", cr.reason == "test")
check("original fields preserved (source)", cr.source == "ai")


# ======================================================================
# [2] ChangeRequest full construction
# ======================================================================
section("2 ChangeRequest with all extended fields")
cr_full = ChangeRequest(
    action=ChangeActionType.ADD_TRANSITION,
    params={"source": "Error", "event": "RESET", "target": "Idle"},
    reason="Error has no outgoing transition.",
    source="ai",
    id="C-001",
    evidence=["STATE_NO_TRANSITION:Error"],
    priority="high",
    confidence=0.95,
)
check("id == 'C-001'", cr_full.id == "C-001")
check("evidence list",
      cr_full.evidence == ["STATE_NO_TRANSITION:Error"])
check("priority == 'high'", cr_full.priority == "high")
check("confidence == 0.95",
      abs(cr_full.confidence - 0.95) < 1e-9)


# ======================================================================
# [3] to_dict / from_dict round-trip
# ======================================================================
section("3 to_dict / from_dict round-trip")
d = cr_full.to_dict()
check("dict has 'id'", d.get("id") == "C-001")
check("dict has 'evidence'",
      d.get("evidence") == ["STATE_NO_TRANSITION:Error"])
check("dict has 'priority'", d.get("priority") == "high")
check("dict has 'confidence'", d.get("confidence") == 0.95)
check("dict has 'action'", d.get("action") == "add_transition")
check("dict has 'params'", d.get("params", {}).get("source") == "Error")
check("dict has 'reason'",
      d.get("reason") == "Error has no outgoing transition.")
check("dict has 'source'", d.get("source") == "ai")

cr_restored = ChangeRequest.from_dict(d)
check("restored id matches", cr_restored.id == cr_full.id)
check("restored evidence matches",
      cr_restored.evidence == cr_full.evidence)
check("restored priority matches",
      cr_restored.priority == cr_full.priority)
check("restored confidence matches",
      abs(cr_restored.confidence - cr_full.confidence) < 1e-9)
check("restored action matches", cr_restored.action == cr_full.action)
check("restored params match", cr_restored.params == cr_full.params)
check("restored reason matches", cr_restored.reason == cr_full.reason)
check("restored source matches", cr_restored.source == cr_full.source)


# ======================================================================
# [4] from_dict backward compatibility
# ======================================================================
section("4 from_dict backward compatibility (old format)")
old_dict = {
    "action": "set_initial",
    "params": {"state": "INIT"},
    "reason": "Initial not set",
}
cr_old = ChangeRequest.from_dict(old_dict)
check("old format id defaults to ''", cr_old.id == "")
check("old format evidence defaults to []", cr_old.evidence == [])
check("old format priority defaults to 'medium'",
      cr_old.priority == "medium")
check("old format confidence defaults to 1.0",
      cr_old.confidence == 1.0)
check("old format action parsed",
      cr_old.action == ChangeActionType.SET_INITIAL)

# Malformed confidence
cr_bad = ChangeRequest.from_dict({
    "action": "add_state",
    "params": {"name": "X"},
    "confidence": "not-a-number",
})
check("bad confidence falls back to 1.0",
      cr_bad.confidence == 1.0)


# ======================================================================
# [5] ACTION_MAPPING covers all 17 actions
# ======================================================================
section("5 ACTION_MAPPING covers all 17 ChangeActionType values")
parser = AIResponseParser()
check("17 entries in ACTION_MAPPING",
      len(parser.ACTION_MAPPING) == 17)
for t in ChangeActionType:
    check(f"'{t.value}' in ACTION_MAPPING",
          t.value in parser.ACTION_MAPPING)
    check(f"maps to {t.name}",
          parser.ACTION_MAPPING.get(t.value) == t)


# ======================================================================
# [6] <response>...</response> extraction
# ======================================================================
section("6 <response> marker extraction")
text_response = '''Sure, here is my diagnosis:

<response>
{
  "version": "1.0",
  "summary": "Fix the error state.",
  "changes": [
    {
      "id": "C-001",
      "action": "add_transition",
      "params": {"source": "Error", "event": "RESET", "target": "Idle"},
      "reason": "No error recovery.",
      "evidence": ["STATE_NO_TRANSITION:Error"],
      "priority": "high",
      "confidence": 0.95
    }
  ]
}
</response>

Let me know if you need more details.'''

changes = parser.parse(text_response)
check("1 change parsed", len(changes) == 1)
if changes:
    c = changes[0]
    check("action == ADD_TRANSITION",
          c.action == ChangeActionType.ADD_TRANSITION)
    check("id preserved", c.id == "C-001")
    check("evidence preserved",
          c.evidence == ["STATE_NO_TRANSITION:Error"])
    check("priority preserved", c.priority == "high")
    check("confidence preserved",
          abs(c.confidence - 0.95) < 1e-9)


# ======================================================================
# [7] <json>...</json> legacy extraction
# ======================================================================
section("7 <json> marker extraction (legacy)")
text_json = '''<json>
{
  "changes": [
    {"action": "set_initial", "params": {"state": "INIT"},
     "reason": "Initial not set"}
  ]
}
</json>'''
changes = parser.parse(text_json)
check("legacy <json> parsed", len(changes) == 1)
if changes:
    check("legacy action SET_INITIAL",
          changes[0].action == ChangeActionType.SET_INITIAL)


# ======================================================================
# [8] Brace-matching fallback
# ======================================================================
section("8 Brace-matching fallback")
text_brace = '''Here's my answer:
{
  "changes": [
    {"action": "add_state", "params": {"name": "X"}, "reason": "..."}
  ]
}'''
changes = parser.parse(text_brace)
check("brace-matching parsed", len(changes) == 1)
if changes:
    check("brace action ADD_STATE",
          changes[0].action == ChangeActionType.ADD_STATE)


# ======================================================================
# [9] All 17 actions parsed via <response>
# ======================================================================
section("9 All 17 actions parsed through <response>")
for t in ChangeActionType:
    payload = (
        '<response>\n'
        '{"changes": [{"action": "' + t.value + '", '
        '"params": {}, "reason": "test"}]}\n'
        '</response>'
    )
    result = parser.parse(payload)
    ok = len(result) == 1 and result[0].action == t
    check(f"{t.value} parsed", ok)


# ======================================================================
# [10] Unknown action rejected
# ======================================================================
section("10 Unknown action is dropped")
text_unknown = '''<response>
{"changes": [
  {"action": "no_such_action", "params": {}, "reason": "x"},
  {"action": "add_state", "params": {"name": "Y"}, "reason": "y"}
]}
</response>'''
changes = parser.parse(text_unknown)
check("unknown dropped, 1 valid remains", len(changes) == 1)
if changes:
    check("valid is ADD_STATE",
          changes[0].action == ChangeActionType.ADD_STATE)


# ======================================================================
# [11] E2E: full AI reply with 2 changes
# ======================================================================
section("11 E2E: full AI reply with 2 changes")
e2e_text = '''I diagnosed the design.

<response>
{
  "version": "1.0",
  "summary": "Add recovery and fix exclusivity.",
  "changes": [
    {
      "id": "C-001",
      "action": "add_transition",
      "params": {"source": "Error", "event": "RESET", "target": "Idle"},
      "reason": "No error recovery.",
      "evidence": ["STATE_NO_TRANSITION:Error"],
      "priority": "high",
      "confidence": 0.95
    },
    {
      "id": "C-002",
      "action": "add_transition_relation",
      "params": {
        "source": "Accumulating",
        "event": "ITEM_SELECT",
        "kind": "exclusive",
        "members": ["T1", "T2"]
      },
      "reason": "Make mutually exclusive.",
      "evidence": ["CELL_EXCLUSIVE_NO_RETURN:Accumulating"],
      "priority": "medium",
      "confidence": 0.85
    }
  ]
}
</response>'''

changes = parser.parse(e2e_text)
check("2 changes parsed", len(changes) == 2)
if len(changes) == 2:
    c1, c2 = changes
    check("c1 action ADD_TRANSITION",
          c1.action == ChangeActionType.ADD_TRANSITION)
    check("c1 id", c1.id == "C-001")
    check("c1 priority high", c1.priority == "high")
    check("c1 confidence 0.95",
          abs(c1.confidence - 0.95) < 1e-9)
    check("c2 action ADD_TRANSITION_RELATION",
          c2.action == ChangeActionType.ADD_TRANSITION_RELATION)
    check("c2 members preserved",
          c2.params.get("members") == ["T1", "T2"])
    check("c2 evidence preserved",
          c2.evidence == ["CELL_EXCLUSIVE_NO_RETURN:Accumulating"])


# ======================================================================
# Summary
# ======================================================================
print()
print("=" * 70)
print(f"  TOTAL: {_total}  PASSED: {_passed}  FAILED: {_failed}")
print("=" * 70)

sys.exit(0 if _failed == 0 else 1)