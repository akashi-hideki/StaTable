"""StateActionsDialog signal safety test (v3: bulletproof mocks).

Approach:
  Replace the dialog CLASSES imported by state_actions_dialog with
  MagicMock. Any call like RoleFunctionDialog(...) or .exec() inside
  StateActionsDialog's handlers will hit the mock, so no modal dialog
  ever opens. This is guaranteed not to block.

Regression guard for v3.2.2-style bool-injection bugs.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import (
    QApplication, QDialog, QMessageBox, QLineEdit,
)
_app = QApplication.instance() or QApplication(sys.argv)

from statable.model import State
from statable.state_machine import StateMachine

import statable_gui.state_actions_dialog as sa_mod
from statable_gui.state_actions_dialog import StateActionsDialog

PASS = FAIL = 0

def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}")


# --- Setup ---
sm = StateMachine()
sm.layer_name = "Application"
sm.add_state(State("Idle"))

print("=" * 60)
print("  StateActionsDialog signal safety (v3)")
print("=" * 60)

# --- 1. Source-level check ---
src = (Path(__file__).parent.parent /
       "statable_gui" / "state_actions_dialog.py").read_text(encoding="utf-8")
check("no QAction.triggered in source",
      "triggered.connect" not in src)

# --- 2. Mock dialog classes used by state_actions_dialog ---
mock_rfd = MagicMock(name="RoleFunctionDialog")
mock_eed = MagicMock(name="EventEditDialog")
mock_cbd = MagicMock(name="ConditionBuilderDialog")

# .exec() returns Rejected so handlers bail out immediately
mock_rfd.return_value.exec.return_value = QDialog.Rejected
mock_eed.return_value.exec.return_value = QDialog.Rejected
mock_cbd.return_value.exec.return_value = QDialog.Rejected

patches = [
    patch.object(sa_mod, "RoleFunctionDialog", mock_rfd),
    patch.object(sa_mod, "EventEditDialog", mock_eed),
    patch.object(sa_mod, "ConditionBuilderDialog", mock_cbd),
    patch.object(QMessageBox, "information",
                 return_value=QMessageBox.Ok),
    patch.object(QMessageBox, "warning",
                 return_value=QMessageBox.Ok),
    patch.object(QMessageBox, "question",
                 return_value=QMessageBox.No),
    patch.object(QMessageBox, "critical",
                 return_value=QMessageBox.Ok),
]
for p in patches:
    p.start()

try:
    dlg = StateActionsDialog(parent=None,
                             state=sm.states["Idle"],
                             state_machine=sm)
    check("dialog instantiated", dlg is not None)

    # --- 3. All buttons clickable without exception ---
    BTN_ATTRS = ("add_btn", "del_btn", "up_btn", "down_btn",
                 "new_role_btn", "edit_role_btn", "del_role_btn",
                 "new_event_btn", "edit_event_btn", "del_event_btn")

    click_count = 0
    for kind in ("entry", "exit", "do"):
        widget = getattr(dlg, f"{kind}_widget")
        for attr in BTN_ATTRS:
            btn = getattr(widget, attr, None)
            if btn is None:
                check(f"{kind}.{attr} exists", False)
                continue
            try:
                print(f"  [click] {kind}.{attr} ...", end="", flush=True)
                btn.click()
                QApplication.processEvents()
                print(" OK")
                click_count += 1
            except Exception as e:
                print(f" RAISED {type(e).__name__}: {e}")
                check(f"{kind}.{attr} raised {type(e).__name__}", False)

    check(f"all {click_count} button clicks passed (no exception)",
          click_count == 30)

    # --- 4. Type/Target/Condition signal emission ---
    w = dlg.entry_widget
    w._on_add()
    check("row added after button chaos", len(w._rows) >= 1)

    # pick last row (safer)
    last_row = len(w._rows) - 1
    type_combo = w.table.cellWidget(last_row, w.COL_TYPE)
    target_combo = w.table.cellWidget(last_row, w.COL_TARGET)
    cond_container = w.table.cellWidget(last_row, w.COL_CONDITION)
    cond_edit = cond_container.findChild(QLineEdit)

    try:
        type_combo.setCurrentIndex(1)  # fire_event
        QApplication.processEvents()
        check("type_combo switch to fire_event", True)
    except Exception as e:
        check(f"type_combo raised {type(e).__name__}: {e}", False)

    try:
        if target_combo.count() > 0:
            target_combo.setCurrentIndex(0)
        QApplication.processEvents()
        check("target_combo setCurrentIndex", True)
    except Exception as e:
        check(f"target_combo raised {type(e).__name__}: {e}", False)

    try:
        cond_edit.setText("x > 0")
        QApplication.processEvents()
        check("condition_edit setText", True)
    except Exception as e:
        check(f"condition_edit raised {type(e).__name__}: {e}", False)

finally:
    for p in patches:
        p.stop()

print()
print("=" * 60)
print(f"  Result: {PASS} PASS / {FAIL} FAIL")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)