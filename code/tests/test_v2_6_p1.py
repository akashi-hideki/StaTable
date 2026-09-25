# tests/test_v2_6_p1.py
"""StaTable v2.6 / C-51 Step 3 (structured EventTrigger) test suite.

Covers:
  - EventTrigger dataclass (defaults, to_dict, from_dict)
  - Event.trigger_detail field
  - XML write: <Trigger> child element (only when trigger_detail is set)
  - XML read: <Trigger> child -> EventTrigger instance
  - Backward compat: no <Trigger> child -> trigger_detail is None
  - Full round-trip with all trigger types
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_THIS_DIR)
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from statable.model import Event, EventKind, EventTrigger
from statable.state_machine import StateMachine
from statable.xml_io import state_machine_to_element, state_machine_from_element


# ======================================================================
# Test harness
# ======================================================================
class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []

    def check(self, name, condition):
        if condition:
            self.passed += 1
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            print(f"  [FAIL] {name}")
            self.failures.append(name)


R = TestResult()


def section(title):
    print(f"\n[{title}]")


# ======================================================================
# [1] EventTrigger defaults
# ======================================================================
section("1. EventTrigger defaults")

t = EventTrigger()
R.check("default type == 'manual'", t.type == "manual")
R.check("default source == ''", t.source == "")
R.check("default edge == ''", t.edge == "")
R.check("default debounce_ms == 0", t.debounce_ms == 0)
R.check("default auto_reload == True", t.auto_reload is True)


# ======================================================================
# [2] to_dict omits empty fields
# ======================================================================
section("2. to_dict omits empty fields")

t = EventTrigger(type="edge", source="GPIO_B1", edge="falling",
                 debounce_ms=20, description="Button")
d = t.to_dict()
R.check("type present", d.get("type") == "edge")
R.check("source present", d.get("source") == "GPIO_B1")
R.check("edge present", d.get("edge") == "falling")
R.check("debounce_ms present", d.get("debounce_ms") == 20)
R.check("description present", d.get("description") == "Button")
R.check("period_ms absent", "period_ms" not in d)
R.check("caller absent", "caller" not in d)

t2 = EventTrigger(type="manual")
d2 = t2.to_dict()
R.check("minimal: only type",
        set(d2.keys()) == {"type"})


# ======================================================================
# [3] from_dict type conversions
# ======================================================================
section("3. from_dict type conversions")

d = {
    "type": "timer",
    "source": "TIMER_1",
    "period_ms": "1000",
    "auto_reload": "false",
}
t = EventTrigger.from_dict(d)
R.check("period_ms int", t.period_ms == 1000)
R.check("auto_reload False", t.auto_reload is False)
R.check("type preserved", t.type == "timer")

# Empty dict -> defaults
t_empty = EventTrigger.from_dict({})
R.check("empty dict -> manual", t_empty.type == "manual")


# ======================================================================
# [4] XML write: <Trigger> present
# ======================================================================
section("4. XML write (Trigger present)")

sm = StateMachine()
sm.layer_name = "Application"
sm.add_event(Event(
    name="SELECT_ITEM",
    kind=EventKind.SIGNAL,
    trigger="\u5546\u54c1\u9078\u629e\u30dc\u30bf\u30f3",
    trigger_detail=EventTrigger(
        type="edge", source="GPIO_BUTTON_1",
        edge="falling", debounce_ms=20,
        description="\u30dc\u30bf\u30f3\u62bc\u4e0b\u3092\u691c\u51fa",
    ),
))

elem = state_machine_to_element(sm)
events = elem.find("Events")
R.check("<Events> exists", events is not None)

event_elem = events.find("Event")
R.check("<Event> exists", event_elem is not None)
R.check("trigger attribute present",
        event_elem.get("trigger") == "\u5546\u54c1\u9078\u629e\u30dc\u30bf\u30f3")

trigger_elem = event_elem.find("Trigger")
R.check("<Trigger> child present", trigger_elem is not None)
R.check("Trigger type=edge", trigger_elem.get("type") == "edge")
R.check("Trigger source=GPIO_BUTTON_1",
        trigger_elem.get("source") == "GPIO_BUTTON_1")
R.check("Trigger edge=falling",
        trigger_elem.get("edge") == "falling")
R.check("Trigger debounce_ms='20'",
        trigger_elem.get("debounce_ms") == "20")


# ======================================================================
# [5] XML write: <Trigger> absent when trigger_detail is None
# ======================================================================
section("5. XML write (Trigger absent)")

sm = StateMachine()
sm.layer_name = "Application"
sm.add_event(Event(
    name="START",
    kind=EventKind.SIGNAL,
    trigger="simple trigger only",
))

elem = state_machine_to_element(sm)
event_elem = elem.find("Events").find("Event")
R.check("trigger attribute present",
        event_elem.get("trigger") == "simple trigger only")
R.check("<Trigger> child absent",
        event_elem.find("Trigger") is None)


# ======================================================================
# [6] XML read: <Trigger> present -> EventTrigger restored
# ======================================================================
section("6. XML read (Trigger present)")

xml_src = '''<StateMachine layer_name="Application">
  <States>
    <State name="Idle" type="initial" />
    <State name="Active" type="normal" />
  </States>
  <Events>
    <Event name="SELECT_ITEM" kind="signal" trigger="\u5546\u54c1\u9078\u629e">
      <Trigger type="edge" source="GPIO_BUTTON_1"
               edge="falling" debounce_ms="20" />
    </Event>
  </Events>
  <RoleFunctions />
  <Transitions />
</StateMachine>'''

root = ET.fromstring(xml_src)
sm = state_machine_from_element(root)

R.check("event loaded", "SELECT_ITEM" in sm.events)
evt = sm.events["SELECT_ITEM"]
R.check("trigger attribute read", evt.trigger == "\u5546\u54c1\u9078\u629e")
R.check("trigger_detail is EventTrigger",
        isinstance(evt.trigger_detail, EventTrigger))
R.check("trigger_detail.type == 'edge'",
        evt.trigger_detail.type == "edge")
R.check("trigger_detail.source == 'GPIO_BUTTON_1'",
        evt.trigger_detail.source == "GPIO_BUTTON_1")
R.check("trigger_detail.edge == 'falling'",
        evt.trigger_detail.edge == "falling")
R.check("trigger_detail.debounce_ms == 20",
        evt.trigger_detail.debounce_ms == 20)


# ======================================================================
# [7] XML read: no <Trigger> -> trigger_detail is None
# ======================================================================
section("7. XML read (Trigger absent)")

xml_src2 = '''<StateMachine layer_name="Application">
  <States>
    <State name="Idle" type="initial" />
  </States>
  <Events>
    <Event name="START" kind="signal" trigger="legacy" />
  </Events>
  <RoleFunctions />
  <Transitions />
</StateMachine>'''

root2 = ET.fromstring(xml_src2)
sm2 = state_machine_from_element(root2)
evt2 = sm2.events["START"]
R.check("trigger preserved", evt2.trigger == "legacy")
R.check("trigger_detail is None (backward compat)",
        evt2.trigger_detail is None)


# ======================================================================
# [8] Full round-trip (all trigger types)
# ======================================================================
section("8. Full round-trip (all trigger types)")

cases = [
    ("EV_MANUAL",  EventTrigger(type="manual")),
    ("EV_EDGE",    EventTrigger(type="edge", source="GPIO_A",
                                edge="falling", debounce_ms=20)),
    ("EV_POLL",    EventTrigger(type="polling", source="POLL_1",
                                period_ms=100)),
    ("EV_TIMER",   EventTrigger(type="timer", source="TIMER_1",
                                period_ms=1000, auto_reload=False)),
    ("EV_CALL",    EventTrigger(type="call", caller="InitSystem")),
    ("EV_CMP",     EventTrigger(type="comparison", condition="x > 0",
                                poll_period_ms=50)),
]

sm = StateMachine()
sm.layer_name = "Application"
for name, td in cases:
    sm.add_event(Event(name=name, kind=EventKind.SIGNAL, trigger_detail=td))

# Serialize -> deserialize
elem = state_machine_to_element(sm)
xml_str = ET.tostring(elem, encoding="unicode")
root = ET.fromstring(xml_str)
sm2 = state_machine_from_element(root)

for name, td in cases:
    R.check(f"{name}: event loaded", name in sm2.events)
    evt2 = sm2.events.get(name)
    if evt2 is None:
        continue
    td2 = evt2.trigger_detail
    R.check(f"{name}: type preserved",
            td2 is not None and td2.type == td.type)
    R.check(f"{name}: source preserved",
            td2 is not None and td2.source == td.source)
    if td.type == "edge":
        R.check(f"{name}: debounce_ms preserved",
                td2.debounce_ms == td.debounce_ms)
        R.check(f"{name}: edge preserved",
                td2.edge == td.edge)
    if td.type in ("polling", "timer"):
        R.check(f"{name}: period_ms preserved",
                td2.period_ms == td.period_ms)
    if td.type == "timer":
        R.check(f"{name}: auto_reload preserved",
                td2.auto_reload == td.auto_reload)
    if td.type == "call":
        R.check(f"{name}: caller preserved",
                td2.caller == td.caller)
    if td.type == "comparison":
        R.check(f"{name}: condition preserved",
                td2.condition == td.condition)
        R.check(f"{name}: poll_period_ms preserved",
                td2.poll_period_ms == td.poll_period_ms)


# ======================================================================
# Summary
# ======================================================================
print()
print("=" * 70)
print(f"  TOTAL: {R.passed + R.failed}  "
      f"PASSED: {R.passed}  FAILED: {R.failed}")
print("=" * 70)

if R.failures:
    print("\nFailures:")
    for name in R.failures:
        print(f"  - {name}")

sys.exit(0 if R.failed == 0 else 1)