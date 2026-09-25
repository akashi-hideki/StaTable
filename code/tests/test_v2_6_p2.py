# tests/test_v2_6_p2.py
"""StaTable v2.6 / C-51 Step 3 Phase 2 (GUI Trigger section) test suite."""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_THIS_DIR)
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from PySide6.QtWidgets import QApplication, QGroupBox

from statable.model import Event, EventKind, EventTrigger
from statable.global_defs import (
    GlobalDefinitions, InterruptHandlerDef, TimerBaseDef,
)
from statable.state_machine import StateMachine
from statable.model import RoleFunction

from statable_gui.event_definition_dialog import (
    EventEditDialog, EventDefinitionDialog,
)


_app = QApplication.instance() or QApplication(sys.argv)


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
# [1] EventEditDialog accepts state_machine kwarg
# ======================================================================
section("1. EventEditDialog state_machine kwarg")

sm = StateMachine()
sm.layer_name = "Application"

dlg = EventEditDialog(None, event=None, global_defs=GlobalDefinitions(),
                      state_machine=sm)
R.check("state_machine stored", dlg.state_machine is sm)

dlg2 = EventEditDialog(None, event=None, global_defs=GlobalDefinitions())
R.check("state_machine default None", dlg2.state_machine is None)


# ======================================================================
# [2] Trigger section exists
# ======================================================================
section("2. Trigger section exists")

gd = GlobalDefinitions()
dlg = EventEditDialog(None, event=None, global_defs=gd, state_machine=sm)
R.check("trig_group exists", hasattr(dlg, "trig_group"))
R.check("trig_group is QGroupBox", isinstance(dlg.trig_group, QGroupBox))
R.check("trig_group is checkable", dlg.trig_group.isCheckable())
R.check("trig_group unchecked by default (no trigger_detail)",
        not dlg.trig_group.isChecked())


# ======================================================================
# [3] Type combo has 6 items
# ======================================================================
section("3. Type combo items")

expected_types = {"manual", "edge", "polling", "timer",
                  "call", "comparison"}
actual_types = {dlg.trig_type_combo.itemData(i)
                for i in range(dlg.trig_type_combo.count())}
R.check("6 types present", actual_types == expected_types)


# ======================================================================
# [4] Preset trigger_detail loads correctly
# ======================================================================
section("4. Preset trigger_detail loads")

gd = GlobalDefinitions()
gd.interrupts.append(InterruptHandlerDef(name="GPIO_B1"))
gd.interrupts.append(InterruptHandlerDef(name="GPIO_B2"))

evt = Event(
    name="SEL", kind=EventKind.SIGNAL,
    trigger_detail=EventTrigger(
        type="edge", source="GPIO_B1",
        edge="falling", debounce_ms=20,
        description="button press"),
)
dlg = EventEditDialog(None, event=evt, global_defs=gd, state_machine=sm)
R.check("groupbox checked when trigger_detail preset",
        dlg.trig_group.isChecked())
R.check("type combo == edge",
        dlg.trig_type_combo.currentData() == "edge")
R.check("edge combo == falling",
        dlg.trig_edge_combo.currentData() == "falling")
R.check("debounce == 20",
        dlg.trig_debounce_spin.value() == 20)
R.check("desc loaded",
        dlg.trig_desc_edit.text() == "button press")


# ======================================================================
# [5] Source candidates populated from interrupts (edge)
# ======================================================================
section("5. Source candidates: edge")

source_items = [dlg.trig_source_combo.itemText(i)
                for i in range(dlg.trig_source_combo.count())]
R.check("GPIO_B1 in candidates", "GPIO_B1" in source_items)
R.check("GPIO_B2 in candidates", "GPIO_B2" in source_items)


# ======================================================================
# [6] Source candidates: timer / polling
# ======================================================================
section("6. Source candidates: timer")

gd2 = GlobalDefinitions()
gd2.timer_base = TimerBaseDef(variable_name="g_tick")
gd2.extra_timers.append(TimerBaseDef(variable_name="g_tick_100ms"))

dlg2 = EventEditDialog(None, event=None, global_defs=gd2, state_machine=sm)
dlg2.trig_group.setChecked(True)
# Switch to timer
idx = dlg2.trig_type_combo.findData("timer")
dlg2.trig_type_combo.setCurrentIndex(idx)

src_items = [dlg2.trig_source_combo.itemText(i)
             for i in range(dlg2.trig_source_combo.count())]
R.check("g_tick in candidates", "g_tick" in src_items)
R.check("g_tick_100ms in candidates", "g_tick_100ms" in src_items)


# ======================================================================
# [7] Source candidates: call (role functions)
# ======================================================================
section("7. Source candidates: call")

sm2 = StateMachine()
sm2.layer_name = "Application"
sm2.add_role_function(RoleFunction(name="Init", namespace="App"))
sm2.add_role_function(RoleFunction(name="Boot", namespace=""))

dlg3 = EventEditDialog(None, event=None, global_defs=GlobalDefinitions(),
                       state_machine=sm2)
dlg3.trig_group.setChecked(True)
idx = dlg3.trig_type_combo.findData("call")
dlg3.trig_type_combo.setCurrentIndex(idx)

src_items = [dlg3.trig_source_combo.itemText(i)
             for i in range(dlg3.trig_source_combo.count())]
R.check("App.Init in candidates", "App.Init" in src_items)
R.check("Boot in candidates", "Boot" in src_items)


# ======================================================================
# [8] Visibility changes with Type
# ======================================================================
section("8. Type-driven field visibility")

dlg4 = EventEditDialog(None, event=None, global_defs=GlobalDefinitions(),
                       state_machine=sm)
dlg4.trig_group.setChecked(True)

# manual: no dynamic rows
idx = dlg4.trig_type_combo.findData("manual")
dlg4.trig_type_combo.setCurrentIndex(idx)
R.check("manual: edge hidden", not dlg4.trig_edge_combo.isVisible()
        or not dlg4.trig_edge_row[0] or not dlg4.trig_edge_row[0].isVisible())
R.check("manual: caller hidden",
        dlg4.trig_caller_row[0] is None
        or not dlg4.trig_caller_row[0].isVisible())

# edge: edge row visible
idx = dlg4.trig_type_combo.findData("edge")
dlg4.trig_type_combo.setCurrentIndex(idx)
R.check("edge: edge label visible",
        dlg4.trig_edge_row[0] is not None
        and dlg4.trig_edge_row[0].isVisible())

# comparison: condition row visible
idx = dlg4.trig_type_combo.findData("comparison")
dlg4.trig_type_combo.setCurrentIndex(idx)
R.check("comparison: condition label visible",
        dlg4.trig_condition_row[0] is not None
        and dlg4.trig_condition_row[0].isVisible())


# ======================================================================
# [9] get_event() returns trigger_detail when checked
# ======================================================================
section("9. get_event() with trigger_detail")

gd5 = GlobalDefinitions()
gd5.interrupts.append(InterruptHandlerDef(name="GPIO_X"))

dlg5 = EventEditDialog(None, event=None, global_defs=gd5, state_machine=sm)
dlg5.name_edit.setText("EV1")
dlg5.trig_group.setChecked(True)
dlg5.trig_type_combo.setCurrentIndex(
    dlg5.trig_type_combo.findData("edge"))
dlg5.trig_source_combo.setCurrentText("GPIO_X")
dlg5.trig_edge_combo.setCurrentIndex(
    dlg5.trig_edge_combo.findData("falling"))
dlg5.trig_debounce_spin.setValue(15)

result = dlg5.get_event()
R.check("trigger_detail returned",
        result.trigger_detail is not None)
R.check("type == edge",
        result.trigger_detail.type == "edge")
R.check("source == GPIO_X",
        result.trigger_detail.source == "GPIO_X")
R.check("edge == falling",
        result.trigger_detail.edge == "falling")
R.check("debounce_ms == 15",
        result.trigger_detail.debounce_ms == 15)


# ======================================================================
# [10] get_event() returns None when groupbox unchecked
# ======================================================================
section("10. get_event() without trigger_detail")

dlg6 = EventEditDialog(None, event=None, global_defs=GlobalDefinitions(),
                       state_machine=sm)
dlg6.name_edit.setText("EV2")
# groupbox unchecked by default
result = dlg6.get_event()
R.check("trigger_detail is None",
        result.trigger_detail is None)


# ======================================================================
# [11] Preset trigger_detail → get_event round-trip
# ======================================================================
section("11. Full round-trip through dialog")

evt = Event(
    name="EV3", kind=EventKind.SIGNAL,
    trigger_detail=EventTrigger(
        type="timer", source="g_tick",
        period_ms=500, auto_reload=False,
        description="tick 500ms one-shot"),
)
dlg7 = EventEditDialog(None, event=evt, global_defs=GlobalDefinitions(),
                       state_machine=sm)
result = dlg7.get_event()
R.check("type preserved", result.trigger_detail.type == "timer")
R.check("source preserved", result.trigger_detail.source == "g_tick")
R.check("period_ms preserved", result.trigger_detail.period_ms == 500)
R.check("auto_reload preserved", result.trigger_detail.auto_reload is False)
R.check("description preserved",
        result.trigger_detail.description == "tick 500ms one-shot")


# ======================================================================
# [12] kind=change disables trigger section
# ======================================================================
section("12. kind=change disables trigger section")

dlg8 = EventEditDialog(None, event=None, global_defs=GlobalDefinitions(),
                       state_machine=sm)
idx = dlg8.kind_combo.findData(EventKind.CHANGE)
dlg8.kind_combo.setCurrentIndex(idx)
R.check("trigger section disabled for kind=change",
        not dlg8.trig_group.isEnabled())

idx2 = dlg8.kind_combo.findData(EventKind.SIGNAL)
dlg8.kind_combo.setCurrentIndex(idx2)
R.check("trigger section enabled for kind=signal",
        dlg8.trig_group.isEnabled())


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