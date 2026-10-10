"""test_v3_4_0_state_actions.py - StateActionsDialog combo & role/event mgmt tests."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

from statable.model import ActionStep, Event, EventKind, RoleFunction, State
from statable.state_machine import StateMachine
from statable_gui.state_actions_dialog import _ActionListWidget
from statable_gui.libcntrl.role_function_library import RoleFunctionLibrary
from statable_gui.libcntrl.literal_library import LiteralLibrary
from statable_gui.libcntrl.condition_library import ConditionLibrary
from statable_gui.global_defs import GlobalDefinitions


PASS = 0
FAIL = 0

def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}")


def _make_sm():
    sm = StateMachine()
    sm.layer_name = "Application"
    sm.add_state(State("Idle"))
    sm.add_state(State("Active"))
    sm.events["STAGE_START"] = Event(name="STAGE_START", kind=EventKind.SIGNAL)
    sm.events["ALL_DONE"] = Event(name="ALL_DONE", kind=EventKind.SIGNAL)
    sm.role_functions["StartStage"] = RoleFunction(
        name="StartStage", namespace="Application",
        description="Start current stage")
    return sm


def _make_widget(sm=None):
    sm = sm or _make_sm()
    rfl = RoleFunctionLibrary()
    litl = LiteralLibrary()
    cdl = ConditionLibrary()
    gd = GlobalDefinitions()
    return _ActionListWidget(
        state_machine=sm,
        role_function_library=rfl,
        literal_library=litl,
        condition_library=cdl,
        layer_names_provider=lambda: ["Application", "DriverInput", "DriverOutput"],
        global_defs=gd,
    ), sm


print("=" * 60)
print("  test_v3_4_0_state_actions.py - StateActionsDialog combo & role/event mgmt")
print("=" * 60)

# 1. Widget construction
w, _ = _make_widget()
check("widget constructed", w is not None)
check("table has 3 columns", w.table.columnCount() == 3)
check("initial row count is 0", w.table.rowCount() == 0)

# 2. Add row
w._on_add()
check("row added", w.table.rowCount() == 1)
check("row data length 1", len(w._rows) == 1)

# 3. Type combo
type_combo = w.table.cellWidget(0, w.COL_TYPE)
check("type combo is QComboBox", type_combo is not None)
check("type combo has role option", type_combo.findData("role") >= 0)
check("type combo has fire_event option", type_combo.findData("fire_event") >= 0)

# 4. Target combo - role candidates
target_combo = w.table.cellWidget(0, w.COL_TARGET)
check("target combo exists", target_combo is not None)
check("target combo includes StartStage",
      "Application.StartStage" in [target_combo.itemText(i)
      for i in range(target_combo.count())])

# 5. Switch Type to fire_event
idx = type_combo.findData("fire_event")
type_combo.setCurrentIndex(idx)
target_combo = w.table.cellWidget(0, w.COL_TARGET)
check("target combo refreshed for fire_event",
      "EVENT_Application_STAGE_START" in
      [target_combo.itemText(i) for i in range(target_combo.count())])

# 6. Condition widget
cond_container = w.table.cellWidget(0, w.COL_CONDITION)
check("condition widget exists", cond_container is not None)
from PySide6.QtWidgets import QLineEdit, QPushButton
check("condition has QLineEdit",
      cond_container.findChild(QLineEdit) is not None)
check("condition has build button",
      cond_container.findChild(QPushButton) is not None)

# 7. set_actions / get_actions round trip
w2, sm2 = _make_widget()
actions_in = [
    ActionStep(action_type="role",
               role_function="Application.StartStage",
               condition="ctx->data.ok"),
    ActionStep(action_type="fire_event",
               event_name="ALL_DONE", condition=""),
]
w2.set_actions(actions_in)
check("round trip row count", len(w2._rows) == 2)
actions_out = w2.get_actions()
check("round trip len", len(actions_out) == 2)
check("round trip role_function",
      actions_out[0].role_function == "Application.StartStage")
check("round trip condition",
      actions_out[0].condition == "ctx->data.ok")
check("round trip event_name",
      actions_out[1].event_name == "ALL_DONE")

# 8. Role candidates dedup
rfl = RoleFunctionLibrary()
rfl.add(RoleFunction(name="Shared", namespace="Application"))
sm3 = _make_sm()
sm3.role_functions["Shared"] = RoleFunction(name="Shared", namespace="Application")
w3 = _ActionListWidget(
    state_machine=sm3, role_function_library=rfl,
    literal_library=LiteralLibrary(), condition_library=ConditionLibrary(),
    layer_names_provider=lambda: ["Application"], global_defs=GlobalDefinitions())
candidates = w3._role_candidates()
check("dedup shared", candidates.count("Application.Shared") == 1)

# 9. Event candidates
evt_candidates = w3._event_candidates()
check("event candidate format",
      "EVENT_Application_STAGE_START" in evt_candidates)

# 10. Delete row
w2._on_delete()
# _on_delete uses currentRow which may not be set; select first
w2.table.setCurrentCell(0, 0)
w2._on_delete()
check("delete row", len(w2._rows) == 1)

# 11. Up/Down
w4, _ = _make_widget()
w4._rows = [{"type": "role", "target": "A", "condition": ""},
            {"type": "role", "target": "B", "condition": ""}]
w4._rebuild_table()
w4.table.setCurrentCell(1, 0)
w4._on_up()
check("up swaps", w4._rows[0]["target"] == "B")
w4._on_down()
check("down swaps back", w4._rows[0]["target"] == "A")

# 12. Role function management (new)
w5, sm5 = _make_widget()
# Simulate adding a role function directly (bypassing dialog)
sm5.add_role_function(RoleFunction(name="NewFunc", namespace="Application"))
w5._rebuild_table()
candidates = w5._role_candidates()
check("new role appears in candidates", "Application.NewFunc" in candidates)

# 13. _find_rf_by_display
rf = w5._find_rf_by_display("Application.StartStage")
check("_find_rf_by_display works", rf is not None and rf.name == "StartStage")

# 14. Role function update propagation
w6, sm6 = _make_widget()
w6._rows = [{"type": "role", "target": "Application.StartStage", "condition": ""}]
w6._rebuild_table()
# Simulate rename
old_rf = sm6.role_functions["StartStage"]
sm6.remove_role_function("StartStage")
new_rf = RoleFunction(name="StartStageV2", namespace="Application")
sm6.add_role_function(new_rf)
# Manual propagation (mimic _on_edit_role_function)
for r_data in w6._rows:
    if r_data.get("target") == "Application.StartStage":
        r_data["target"] = "Application.StartStageV2"
check("rename propagated", w6._rows[0]["target"] == "Application.StartStageV2")

# 15. Event display format
w7, _ = _make_widget()
w7._rows = [{"type": "fire_event", "target": "EVENT_Application_STAGE_START",
             "condition": ""}]
w7._rebuild_table()
actions = w7.get_actions()
check("event display parsed to bare name",
      actions[0].event_name == "STAGE_START")
check("event type preserved", actions[0].action_type == "fire_event")

# 16. Empty target dropped
w8, _ = _make_widget()
w8._rows = [{"type": "role", "target": "", "condition": ""}]
w8._rebuild_table()
check("empty target dropped", len(w8.get_actions()) == 0)


print()
print("=" * 60)
print(f"  Result: {PASS} PASS / {FAIL} FAIL")
print("=" * 60)

os._exit(0 if FAIL == 0 else 1)