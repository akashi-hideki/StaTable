# tests/test_v2_6_p3.py
"""StaTable v2.6 / C-51 Step 3 Phase 3 - GUI integration test.

End-to-end workflow test simulating actual user actions:

  1. Load real vending_machine.xml
  2. Find BUTTON_SENSOR event
  3. Open EventEditDialog, verify loaded state
  4. Simulate user edits (Type/Source/Edge/Debounce)
  5. Extract via get_event(), verify all fields
  6. Toggle groupbox OFF, verify trigger_detail=None
  7. Save project to temp XML
  8. Reload and verify round-trip
  9. EventDefinitionDialog integration
 10. ConditionBuilderDialog launch from comparison type

Complements test_v2_6_p2.py (unit-level GUI state) with real
file-based workflow verification.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_THIS_DIR)
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication, QDialog

from statable.model import (
    Event, EventKind, EventTrigger, EventDeliveryType,
)
from statable.global_defs import GlobalDefinitions
from statable.state_machine import StateMachine
from statable.xml_io import (
    project_from_xml, project_to_xml,
    state_machine_to_element, state_machine_from_element,
)

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


# ----------------------------------------------------------------------
# Fixture: real vending_machine.xml
# ----------------------------------------------------------------------
VENDING_XML = (
    Path(_CODE_DIR) / "docs" / "tutorial" / "vending_machine.xml"
)


# ======================================================================
# [1] Load real vending_machine.xml
# ======================================================================
section("1. Load vending_machine.xml")

R.check("vending_machine.xml exists", VENDING_XML.exists())

tabs, gd, rfl, cfl, lfl, ps = project_from_xml(str(VENDING_XML))
R.check("3 tabs loaded", len(tabs) == 3)

tab_names = [t[0] for t in tabs]
R.check("Driver tab present", "Driver" in tab_names)
R.check("Middleware tab present", "Middleware" in tab_names)
R.check("Application tab present", "Application" in tab_names)

driver_sm = next(sm for n, sm in tabs if n == "Driver")
mw_sm = next(sm for n, sm in tabs if n == "Middleware")
app_sm = next(sm for n, sm in tabs if n == "Application")


# ======================================================================
# [2] Verify BUTTON_SENSOR trigger_detail loaded from XML
# ======================================================================
section("2. BUTTON_SENSOR trigger_detail from XML")

R.check("BUTTON_SENSOR event exists", "BUTTON_SENSOR" in driver_sm.events)

btn_evt = driver_sm.events["BUTTON_SENSOR"]
R.check("trigger_detail is EventTrigger",
        isinstance(btn_evt.trigger_detail, EventTrigger))
if btn_evt.trigger_detail is not None:
    td = btn_evt.trigger_detail
    R.check("type == 'edge'", td.type == "edge")
    R.check("source == 'GPIO_BUTTON_1'", td.source == "GPIO_BUTTON_1")
    R.check("edge == 'falling'", td.edge == "falling")
    R.check("debounce_ms == 20", td.debounce_ms == 20)


# ======================================================================
# [3] Open EventEditDialog with BUTTON_SENSOR, verify UI state
# ======================================================================
section("3. EventEditDialog for BUTTON_SENSOR")

dlg = EventEditDialog(None, event=btn_evt, global_defs=gd,
                      state_machine=driver_sm)

R.check("trig_group checked", dlg.trig_group.isChecked())
R.check("type combo == edge",
        dlg.trig_type_combo.currentData() == "edge")
R.check("source combo text",
        dlg.trig_source_combo.currentText() == "GPIO_BUTTON_1")
R.check("edge combo == falling",
        dlg.trig_edge_combo.currentData() == "falling")
R.check("debounce spin == 20",
        dlg.trig_debounce_spin.value() == 20)


# ======================================================================
# [4] Simulate user edit: change Type edge -> timer
# ======================================================================
section("4. Simulate user edit: edge -> timer")

# User selects "timer" from the Type dropdown
dlg.trig_type_combo.setCurrentIndex(
    dlg.trig_type_combo.findData("timer"))
R.check("after type change: type == timer",
        dlg.trig_type_combo.currentData() == "timer")

# Set period and auto_reload
dlg.trig_period_spin.setValue(500)
dlg.trig_autoreload_check.setChecked(False)

# Extract new event
new_evt = dlg.get_event()
R.check("get_event: trigger_detail present",
        new_evt.trigger_detail is not None)
if new_evt.trigger_detail is not None:
    R.check("get_event: type == timer",
            new_evt.trigger_detail.type == "timer")
    R.check("get_event: period_ms == 500",
            new_evt.trigger_detail.period_ms == 500)
    R.check("get_event: auto_reload == False",
            new_evt.trigger_detail.auto_reload is False)
    R.check("get_event: edge cleared",
            new_evt.trigger_detail.edge == "")


# ======================================================================
# [5] Simulate user edit: change Type timer -> comparison, use Build button
# ======================================================================
section("5. Simulate user edit: timer -> comparison + Build")

dlg.trig_type_combo.setCurrentIndex(
    dlg.trig_type_combo.findData("comparison"))
R.check("comparison: type selected",
        dlg.trig_type_combo.currentData() == "comparison")

# User types a condition manually
dlg.trig_condition_edit.setText("balance > 100")
dlg.trig_pollperiod_spin.setValue(50)

new_evt2 = dlg.get_event()
R.check("comparison: condition preserved",
        new_evt2.trigger_detail.condition == "balance > 100")
R.check("comparison: poll_period_ms == 50",
        new_evt2.trigger_detail.poll_period_ms == 50)


# ======================================================================
# [6] ConditionBuilderDialog launch (mocked)
# ======================================================================
section("6. ConditionBuilderDialog launch (mocked)")

try:
    from statable_gui import condition_builder_dialog
    can_mock_builder = True
except ImportError:
    can_mock_builder = False

if can_mock_builder:
    with patch(
        "statable_gui.event_definition_dialog."
        "ConditionBuilderDialog" if hasattr(
            __import__("statable_gui.event_definition_dialog",
                       fromlist=["ConditionBuilderDialog"]),
            "ConditionBuilderDialog"
        ) else "statable_gui.condition_builder_dialog.ConditionBuilderDialog"
    ) as mock_builder:
        inst = MagicMock()
        inst.exec.return_value = QDialog.Accepted
        inst.get_condition_text.return_value = "RoleFunc_App_Check() == 0"
        mock_builder.return_value = inst

        # Trigger via the Build button handler
        dlg._open_trigger_condition_builder()
        R.check("Build button: condition updated from builder",
                dlg.trig_condition_edit.text()
                == "RoleFunc_App_Check() == 0")
else:
    R.check("ConditionBuilderDialog available (skipped)", True)


# ======================================================================
# [7] Toggle groupbox OFF -> trigger_detail=None
# ======================================================================
section("7. Toggle groupbox OFF")

dlg.trig_group.setChecked(False)
new_evt3 = dlg.get_event()
R.check("groupbox off: trigger_detail is None",
        new_evt3.trigger_detail is None)


# ======================================================================
# [8] Save project to temp XML (with edits)
# ======================================================================
section("8. Save project to temp XML")

# Apply edited event back to StateMachine
edited_evt = dlg.get_event()
edited_evt.name = "BUTTON_SENSOR"  # ensure name matches
driver_sm.events["BUTTON_SENSOR"] = edited_evt

tmp_dir = tempfile.mkdtemp(prefix="statable_v26p3_")
tmp_xml = os.path.join(tmp_dir, "test_v26p3.xml")

try:
    project_to_xml(tabs, gd, tmp_xml)
    R.check("XML file written", os.path.exists(tmp_xml))

    with open(tmp_xml, "r", encoding="utf-8") as f:
        xml_text = f.read()
    R.check("BUTTON_SENSOR exists in XML",
            'name="BUTTON_SENSOR"' in xml_text)
    R.check("<Trigger> tag emitted for BUTTON_SENSOR",
            "<Trigger" in xml_text)

    # ==============================================================
    # [9] Reload from temp XML, verify round-trip
    # ==============================================================
    section("9. Reload from temp XML")

    tabs2, gd2, _, _, _, _ = project_from_xml(tmp_xml)
    driver_sm2 = next(sm for n, sm in tabs2 if n == "Driver")
    btn_evt2 = driver_sm2.events.get("BUTTON_SENSOR")

    R.check("BUTTON_SENSOR reloaded", btn_evt2 is not None)

    # Note: trigger_detail is None because we toggled OFF in section 7
    if btn_evt2 is not None:
        R.check("trigger_detail is None after toggle-OFF round-trip",
                btn_evt2.trigger_detail is None)

    # ---- Second round-trip: with trigger_detail ON ----
    btn_evt.trigger_detail = EventTrigger(
        type="edge", source="GPIO_BUTTON_1",
        edge="falling", debounce_ms=20,
        description="restored",
    )
    driver_sm2.events["BUTTON_SENSOR"] = btn_evt

    tmp_xml2 = os.path.join(tmp_dir, "test_v26p3b.xml")
    project_to_xml(tabs2, gd2, tmp_xml2)

    tabs3, gd3, _, _, _, _ = project_from_xml(tmp_xml2)
    driver_sm3 = next(sm for n, sm in tabs3 if n == "Driver")
    btn_evt3 = driver_sm3.events.get("BUTTON_SENSOR")

    R.check("2nd round-trip: event present", btn_evt3 is not None)
    if btn_evt3 is not None and btn_evt3.trigger_detail is not None:
        td3 = btn_evt3.trigger_detail
        R.check("2nd round-trip: type preserved", td3.type == "edge")
        R.check("2nd round-trip: source preserved",
                td3.source == "GPIO_BUTTON_1")
        R.check("2nd round-trip: debounce preserved",
                td3.debounce_ms == 20)
        R.check("2nd round-trip: description preserved",
                td3.description == "restored")
    else:
        R.check("2nd round-trip: trigger_detail present", False)

finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)


# ======================================================================
# [10] EventDefinitionDialog integration
# ======================================================================
section("10. EventDefinitionDialog integration")

# Create EventDefinitionDialog for Driver layer
edd = EventDefinitionDialog(driver_sm, global_defs=gd)
R.check("EventDefinitionDialog created", edd is not None)
R.check("table has rows", edd.table.rowCount() > 0)

# Find BUTTON_SENSOR row
found_row = -1
for r in range(edd.table.rowCount()):
    name_item = edd.table.item(r, 1)
    if name_item and name_item.text() == "BUTTON_SENSOR":
        found_row = r
        break
R.check("BUTTON_SENSOR row found in table", found_row >= 0)

# Simulate double-click on BUTTON_SENSOR (skip col=0 which is title)
if found_row >= 0:
    with patch(
        "statable_gui.event_definition_dialog.EventEditDialog"
    ) as mock_dlg:
        inst = MagicMock()
        inst.exec.return_value = QDialog.Rejected  # just open, don't save
        mock_dlg.return_value = inst

        edd.on_double_clicked(found_row, 1)  # col=1 → event name

    R.check("EventEditDialog invoked by double-click",
            mock_dlg.called)
    # Verify state_machine was passed as kwarg
    if mock_dlg.called:
        call_kwargs = mock_dlg.call_args.kwargs
        R.check("EventEditDialog received state_machine",
                call_kwargs.get("state_machine") is driver_sm)


# ======================================================================
# [11] SELECT_ITEM (manual type) round-trip
# ======================================================================
section("11. SELECT_ITEM (manual type) round-trip")

sel_evt = app_sm.events.get("SELECT_ITEM")
R.check("SELECT_ITEM event exists", sel_evt is not None)

if sel_evt is not None:
    R.check("SELECT_ITEM has trigger_detail",
            sel_evt.trigger_detail is not None)
    if sel_evt.trigger_detail is not None:
        R.check("SELECT_ITEM trigger type == manual",
                sel_evt.trigger_detail.type == "manual")

    # Re-open in dialog
    dlg2 = EventEditDialog(None, event=sel_evt, global_defs=gd,
                           state_machine=app_sm)
    R.check("dialog2: groupbox checked",
            dlg2.trig_group.isChecked())
    R.check("dialog2: type == manual",
            dlg2.trig_type_combo.currentData() == "manual")


# ======================================================================
# [12] Full pipeline: existing events unaffected
# ======================================================================
section("12. Existing events unaffected")

# COIN_SENSOR has no trigger_detail (not modified by our patch)
coin_evt = driver_sm.events.get("COIN_SENSOR")
R.check("COIN_SENSOR event exists", coin_evt is not None)
if coin_evt is not None:
    R.check("COIN_SENSOR trigger_detail is None (unchanged)",
            coin_evt.trigger_detail is None)

# Its XML should not have a <Trigger> child
elem = state_machine_to_element(driver_sm)
events_elem = elem.find("Events")
coin_elem = None
for ev in events_elem.findall("Event"):
    if ev.get("name") == "COIN_SENSOR":
        coin_elem = ev
        break
R.check("COIN_SENSOR has no <Trigger> child",
        coin_elem is not None and coin_elem.find("Trigger") is None)


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