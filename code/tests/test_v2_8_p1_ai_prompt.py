# tests/test_v2_8_p1_ai_prompt.py
"""
StaTable v2.8 P1 (AI prompt refresh) test suite

Covers SPEC_AI_PROMPT_v1.1 Phase A:
  - XML-style prompt template structure
  - Two few-shot examples
  - _format_data: <context> sub-sections
  - _format_validation: structured <issue>
  - _format_actions: 17 ACTION_DEFINITIONS as XML
  - _format_trigger: type-specific attributes
  - _format_relation: recursive children
  - XML escaping
  - Reserved / non-actionable fields excluded
  - action_type="custom" skipped

Phase B / C sections will be appended here later.

[v1 fix]
  - Test [9]: check 'return_type="' instead of 'return_type' because
    the <actions> section legitimately contains a param named
    "return_type" for add_role_function.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codegen.validate.prompt_generator import AIPromptGenerator
from codegen.validate.data.prompt_templates import (
    PROMPT_TEMPLATES, OUTPUT_SCHEMA,
    FEW_SHOT_EXAMPLE_1, FEW_SHOT_EXAMPLE_2,
)
from codegen.validate.data.action_definitions import ACTION_DEFINITIONS

from statable.state_machine import StateMachine
from statable.model import (
    State, Event, Transition, StateType, EventKind,
    EventTrigger, ActionStep, TransitionRelation, RoleFunction,
    EventDeliveryType, EventSourceLayer,
)
from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
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


def make_basic_sm() -> StateMachine:
    """Minimal SM with 2 states / 1 event / 1 transition / 1 role func."""
    sm = StateMachine()
    sm.layer_name = "Application"
    sm.layer_priority = 5
    sm.add_state(State(name="Idle", type=StateType.NORMAL,
                       description="Waiting"))
    sm.add_state(State(name="Active", type=StateType.NORMAL,
                       description="Running"))
    sm.add_event(Event(name="START", kind=EventKind.SIGNAL,
                       description="Start signal"))
    sm.add_role_function(RoleFunction(
        name="InitHw", namespace="Application",
        description="Initialize hardware"))
    sm.add_transition(Transition(
        source="Idle", event="START", target="Active",
        early_return=True, label="T1", has_else=False,
    ))
    sm.set_initial("Idle")
    return sm


# ======================================================================
# [1] Template structure
# ======================================================================
section("1 Template has 10 XML sections")
template = PROMPT_TEMPLATES['diagnosis']['template']
for tag in [
    '<system>', '<workflow>', '<task>', '<output_schema>',
    '<examples>', '<constraints>', '<context>',
    '<validation>', '<actions>', '<response_format>',
]:
    check(f"{tag} present in template", tag in template)

# Few-shot examples
check("FEW_SHOT_EXAMPLE_1 is non-empty", bool(FEW_SHOT_EXAMPLE_1.strip()))
check("FEW_SHOT_EXAMPLE_2 is non-empty", bool(FEW_SHOT_EXAMPLE_2.strip()))
check("Example 1 uses 'set_initial'",
      '"set_initial"' in FEW_SHOT_EXAMPLE_1)
check("Example 2 uses 'remove_transition'",
      '"remove_transition"' in FEW_SHOT_EXAMPLE_2)
check("Example 2 includes evidence array",
      '"evidence"' in FEW_SHOT_EXAMPLE_2)
check("Example 2 includes confidence",
      '"confidence"' in FEW_SHOT_EXAMPLE_2)
check("OUTPUT_SCHEMA mentions version",
      '"version"' in OUTPUT_SCHEMA)
check("OUTPUT_SCHEMA mentions evidence",
      '"evidence"' in OUTPUT_SCHEMA)


# ======================================================================
# [2] <context> sections on a basic SM
# ======================================================================
section("2 _format_data emits every <context> sub-section")
sm = make_basic_sm()
gd = GlobalDefinitions()
gen = AIPromptGenerator()
prompt = gen.generate_diagnosis_prompt(sm, gd, None)

for prefix in [
    '<layer', '<states', '<events', '<transitions',
    '<role_functions', '<cells', '<global_definitions',
]:
    check(f"{prefix}> present", prefix in prompt)

# Content sanity
check("State name 'Idle' in prompt", 'name="Idle"' in prompt)
check("Event name 'START' in prompt", 'name="START"' in prompt)
check("Transition label 'T1' in prompt", 'label="T1"' in prompt)
check("Role function 'InitHw' in prompt", 'name="InitHw"' in prompt)
check("Role function namespace in prompt",
      'namespace="Application"' in prompt)


# ======================================================================
# [3] <context> empty sections emit self-closing tags
# ======================================================================
section("3 Empty sections still emit self-closing tags")
sm_empty = StateMachine()
sm_empty.layer_name = "Empty"
prompt_empty = gen.generate_diagnosis_prompt(sm_empty, GlobalDefinitions(), None)

for tag in ['<states/>', '<events/>', '<transitions/>',
            '<role_functions/>', '<cells/>',
            '<global_definitions/>']:
    check(f"{tag} present when empty", tag in prompt_empty)


# ======================================================================
# [4] _format_actions renders all 17 actions
# ======================================================================
section("4 _format_actions covers all 17 ACTION_DEFINITIONS")
actions_xml = gen._format_actions()
for action_name in ACTION_DEFINITIONS.keys():
    check(f"<action name=\"{action_name}\"",
          f'name="{action_name}"' in actions_xml)
check("Param required=\"true\" present",
      'required="true"' in actions_xml)
check("Param required=\"false\" present",
      'required="false"' in actions_xml)
check("Enum 'values=' present (add_state)",
      'values="' in actions_xml)


# ======================================================================
# [5] <validation> structured <issue>
# ======================================================================
section("5 _format_validation emits <issue> with attributes")
class FakeIssue:
    def __init__(self, sev, cat, code, target, sug, msg):
        self.severity = type("S", (), {"value": sev})()
        self.category = cat
        self.code = code
        self.target = target
        self.suggestion = sug
        self.message = msg


class FakeResult:
    def __init__(self, issues):
        self.issues = issues


issues = [
    FakeIssue("error", "state", "STATE_UNREACHABLE", "Halt",
              "Add a transition.", "State Halt is unreachable"),
    FakeIssue("warning", "event", "EVENT_UNUSED", "TIMER_0",
              "Remove it.", "Event TIMER_0 unused"),
]
val_xml = gen._format_validation(FakeResult(issues))
check("severity=\"ERROR\"", 'severity="ERROR"' in val_xml)
check("severity=\"WARNING\"", 'severity="WARNING"' in val_xml)
check("category attribute", 'category="state"' in val_xml)
check("code attribute", 'code="STATE_UNREACHABLE"' in val_xml)
check("target attribute", 'target="Halt"' in val_xml)
check("suggestion attribute", 'suggestion="Add a transition."' in val_xml)
check("message text inside tag",
      "State Halt is unreachable</issue>" in val_xml)
check("No issues → comment",
      "No issues" in gen._format_validation(None))


# ======================================================================
# [6] _format_trigger type-specific attributes
# ======================================================================
section("6 _format_trigger emits type-specific attributes")

def make_event_with_trigger(td):
    ev = Event(name="EVT", kind=EventKind.SIGNAL)
    ev.trigger_detail = td
    return ev

# edge
e_edge = make_event_with_trigger(EventTrigger(
    type="edge", source="GPIO_1", edge="falling", debounce_ms=20))
t = gen._format_trigger(e_edge)
check("edge: type attribute", 'type="edge"' in t)
check("edge: source", 'source="GPIO_1"' in t)
check("edge: edge", 'edge="falling"' in t)
check("edge: debounce_ms", 'debounce_ms="20"' in t)
check("edge: no period_ms", 'period_ms' not in t)

# timer with auto_reload=False
e_timer = make_event_with_trigger(EventTrigger(
    type="timer", source="TICK", period_ms=100, auto_reload=False))
t = gen._format_trigger(e_timer)
check("timer: period_ms", 'period_ms="100"' in t)
check("timer: auto_reload=false", 'auto_reload="false"' in t)

# call
e_call = make_event_with_trigger(EventTrigger(
    type="call", caller="main_init"))
t = gen._format_trigger(e_call)
check("call: caller", 'caller="main_init"' in t)
check("call: no source", 'source=' not in t)

# manual fallback from trigger text only
e_manual = Event(name="M", kind=EventKind.SIGNAL)
e_manual.trigger = "Fired by Middleware"
t = gen._format_trigger(e_manual)
check("manual: type=\"manual\"", 'type="manual"' in t)
check("manual: description",
      'description="Fired by Middleware"' in t)

# no trigger at all
e_none = Event(name="N", kind=EventKind.SIGNAL)
check("no trigger → empty string", gen._format_trigger(e_none) == "")


# ======================================================================
# [7] _format_relation recursive children
# ======================================================================
section("7 _format_relation nests children recursively")
rel = TransitionRelation(
    kind="group", members=["T1", "T2"],
    shared_condition="running == true",
    children=[
        TransitionRelation(kind="exclusive", members=["T1", "T2"]),
    ],
)
rel_lines = gen._format_relation(rel, indent=8)
rel_xml = "\n".join(rel_lines)
check("parent kind=group", 'kind="group"' in rel_xml)
check("parent members", 'members="T1,T2"' in rel_xml)
check("parent shared_condition",
      'shared_condition="running == true"' in rel_xml)
check("child kind=exclusive", 'kind="exclusive"' in rel_xml)
# Nesting depth: child indented deeper than parent
parent_open = next(l for l in rel_lines if 'kind="group"' in l)
child_open = next(l for l in rel_lines if 'kind="exclusive"' in l)
check("child indented deeper than parent",
      len(child_open) - len(child_open.lstrip())
      > len(parent_open) - len(parent_open.lstrip()))


# ======================================================================
# [8] XML attribute escaping
# ======================================================================
section("8 XML attribute escaping")
sm_x = StateMachine()
sm_x.layer_name = "L"
sm_x.add_state(State(name="A&B", description='Has "quotes"'))
sm_x.add_event(Event(name="E<1>", kind=EventKind.SIGNAL))
sm_x.add_transition(Transition(source="A&B", event="E<1>", target="A&B"))
prompt_x = gen.generate_diagnosis_prompt(sm_x, GlobalDefinitions(), None)
check("& escaped to &amp;", "&amp;" in prompt_x)
check("< escaped to &lt;", "&lt;" in prompt_x)
check("> escaped to &gt;", "&gt;" in prompt_x)
check("\" escaped to &quot;", "&quot;" in prompt_x)


# ======================================================================
# [9] Reserved fields excluded
# ======================================================================
# Note: the <actions> section legitimately contains a param named
# "return_type" for add_role_function. So we check that
# return_type is not emitted as an XML *attribute* on a
# <role_function .../> element, which is what "Reserved field
# excluded" really means.
section("9 Reserved / non-actionable fields are not sent")
rf = RoleFunction(
    name="F", namespace="NS",
    return_type="uint32_t", arg1_type="int", arg1_name="a1",
    arg2_type="int", arg2_name="a2",
)
sm_r = StateMachine()
sm_r.layer_name = "L"
sm_r.add_state(State(name="S"))
sm_r.add_role_function(rf)
prompt_r = gen.generate_diagnosis_prompt(sm_r, GlobalDefinitions(), None)
check("return_type NOT as attribute",
      'return_type="' not in prompt_r)
check("arg1_type NOT as attribute",
      'arg1_type="' not in prompt_r)
check("arg1_name NOT as attribute",
      'arg1_name="' not in prompt_r)
check("arg2_type NOT as attribute",
      'arg2_type="' not in prompt_r)
check("arg2_name NOT as attribute",
      'arg2_name="' not in prompt_r)
check("used_global_vars NOT as attribute",
      'used_global_vars="' not in prompt_r)
check("used_events NOT as attribute",
      'used_events="' not in prompt_r)
check("used_literals NOT as attribute",
      'used_literals="' not in prompt_r)


# ======================================================================
# [10] action_type="custom" is skipped
# ======================================================================
section("10 action_type=\"custom\" is skipped in state actions")
sm_c = StateMachine()
sm_c.layer_name = "L"
st = State(name="S")
st.entry = [
    ActionStep(role_function="R1"),
    ActionStep(action_type="custom"),  # should be skipped
    ActionStep(role_function="R2", condition="flag == 1"),
]
sm_c.add_state(st)
prompt_c = gen.generate_diagnosis_prompt(sm_c, GlobalDefinitions(), None)
check("role_function R1 sent", 'role_function="R1"' in prompt_c)
check("role_function R2 sent", 'role_function="R2"' in prompt_c)
check("condition sent", 'condition="flag == 1"' in prompt_c)
# No <action> with action_type="custom"
check("no action_type=\"custom\" sent",
      'action_type="custom"' not in prompt_c)


# ======================================================================
# [11] E2E: full prompt has all major sections
# ======================================================================
section("11 E2E: full prompt sanity")
sm_e = make_basic_sm()
gd_e = GlobalDefinitions()
gd_e.variables.append(SystemVariable(
    name="counter", type="uint16_t", group="Timer"))
gd_e.flags.append(EventFlag(
    name="error_flag", min_value=0, max_value=1))
prompt_e = gen.generate_diagnosis_prompt(sm_e, gd_e, None)

check("<system> in prompt", '<system>' in prompt_e)
check("<workflow> in prompt", '<workflow>' in prompt_e)
check("<task> in prompt", '<task>' in prompt_e)
check("<output_schema> in prompt", '<output_schema>' in prompt_e)
check("<examples> in prompt", '<examples>' in prompt_e)
check("<constraints> in prompt", '<constraints>' in prompt_e)
check("<context> in prompt", '<context>' in prompt_e)
check("<validation> in prompt", '<validation>' in prompt_e)
check("<actions> in prompt", '<actions>' in prompt_e)
check("<response_format> in prompt", '<response_format>' in prompt_e)
check("Two <example id=...> blocks",
      prompt_e.count('<example id=') == 2)
check("Variable counter present", 'name="counter"' in prompt_e)
check("Flag error_flag present", 'name="error_flag"' in prompt_e)


# ======================================================================
# [12] ResponseValidator integration
# ======================================================================
section("12 ResponseValidator integrates with prompt workflow")

from codegen.validate.change_actions import (
    ChangeRequest, ChangeActionType,
)
from codegen.validate.response_validator import ResponseValidator

sm_v = make_basic_sm()
v = ResponseValidator()

# Valid request
r = v.validate([
    ChangeRequest(
        action=ChangeActionType.ADD_TRANSITION,
        params={"source": "Idle", "event": "START", "target": "Active"},
        reason="ok",
    ),
], sm_v)
check("valid request accepted", len(r.valid_requests) == 1)
check("invalid empty", len(r.invalid_requests) == 0)

# Invalid request
r = v.validate([
    ChangeRequest(
        action=ChangeActionType.ADD_TRANSITION,
        params={"source": "Ghost", "event": "START", "target": "Active"},
        reason="test",
    ),
], sm_v)
check("invalid request rejected", len(r.valid_requests) == 0)
check("invalid captured with reason",
      len(r.invalid_requests) == 1
      and "Ghost" in r.invalid_requests[0][1])

# Low-confidence warning
r = v.validate([
    ChangeRequest(
        action=ChangeActionType.ADD_STATE,
        params={"name": "New"},
        reason="test",
        id="C-001",
        confidence=0.3,
    ),
], sm_v)
check("low-confidence warning emitted", len(r.warnings) == 1)


# ======================================================================
# [13] validation_dialog exposes ResponseValidator
# ======================================================================
section("13 validation_dialog wires ResponseValidator")
from pathlib import Path as _P

_vd_path = _P(__file__).resolve().parent.parent \
    / "codegen" / "validate" / "validation_dialog.py"
_vd_src = _vd_path.read_text(encoding="utf-8")
check("imports ResponseValidator",
      "from .response_validator import ResponseValidator" in _vd_src)
check("instantiates response_validator",
      "self.response_validator = ResponseValidator()" in _vd_src)
check("stores validation_outcome",
      "self.validation_outcome = None" in _vd_src)
check("validates in _parse_response",
      "self.response_validator.validate(" in _vd_src)
check("change_tree has Priority column",
      '"Priority"' in _vd_src)
check("change_tree has Confidence column",
      '"Confidence"' in _vd_src)
check("change_tree has Status column",
      '"Status"' in _vd_src)
check("invalid rows marked EXCLUDED",
      'EXCLUDED:' in _vd_src)


# ======================================================================
# Summary
# ======================================================================
print()
print("=" * 70)
print(f"  TOTAL: {_total}  PASSED: {_passed}  FAILED: {_failed}")
print("=" * 70)

sys.exit(0 if _failed == 0 else 1)