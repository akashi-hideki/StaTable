# tools/gui_smoke_v2_8.py
"""
Headless smoke test for ValidationDialog (v2.8.0).

Instantiates ValidationDialog with offscreen Qt, feeds a canned AI
reply, parses it, and asserts the change_tree contents. Message boxes
are monkeypatched to avoid blocking.

[v2 fix]
  - Section [4]: the low-confidence warning expectation was wrong.
    C-002 is rejected at the reference-check stage *before* the
    warning collector runs, so no warning is emitted for it. The
    expectation is now 0 warnings.

Run:
    cd code
    python tools\\gui_smoke_v2_8.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

CODE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE))

from PySide6.QtWidgets import QApplication, QMessageBox, QTreeWidgetItem
from PySide6.QtCore import Qt

# Suppress all QMessageBox popups
QMessageBox.information = staticmethod(lambda *a, **k: None)
QMessageBox.warning = staticmethod(lambda *a, **k: None)
QMessageBox.critical = staticmethod(lambda *a, **k: None)

from codegen.validate.validation_dialog import ValidationDialog

from statable.state_machine import StateMachine
from statable.model import (
    State, Event, Transition, StateType, EventKind, RoleFunction,
)
from statable.global_defs import GlobalDefinitions


SAMPLE_REPLY = """I diagnosed the design.

<response>
{
  "version": "1.0",
  "summary": "Add recovery.",
  "changes": [
    {
      "id": "C-001",
      "action": "add_transition",
      "params": {"source": "Idle", "event": "START", "target": "Active"},
      "reason": "Connect Idle to Active.",
      "evidence": ["STATE_NO_TRANSITION:Idle"],
      "priority": "high",
      "confidence": 0.95
    },
    {
      "id": "C-002",
      "action": "add_transition",
      "params": {"source": "Ghost", "event": "START", "target": "Active"},
      "reason": "Invalid: Ghost does not exist.",
      "evidence": ["TEST"],
      "priority": "low",
      "confidence": 0.3
    }
  ]
}
</response>
"""


_total = 0
_passed = 0
_failed = 0


def check(label, cond):
    global _total, _passed, _failed
    _total += 1
    if cond:
        _passed += 1
        print(f"  [PASS] {label}")
    else:
        _failed += 1
        print(f"  [FAIL] {label}")


def main() -> int:
    app = QApplication.instance() or QApplication([])

    sm = StateMachine()
    sm.layer_name = "Application"
    sm.layer_priority = 5
    sm.add_state(State(name="Idle", type=StateType.NORMAL))
    sm.add_state(State(name="Active", type=StateType.NORMAL))
    sm.add_event(Event(name="START", kind=EventKind.SIGNAL))
    sm.set_initial("Idle")

    gd = GlobalDefinitions()

    print("=" * 70)
    print("  GUI smoke test — ValidationDialog (v2.8.0)")
    print("=" * 70)

    print()
    print("[1] Instantiate ValidationDialog")
    dlg = ValidationDialog(sm, gd)
    check("dialog created", dlg is not None)
    check("has response_validator",
          hasattr(dlg, "response_validator"))
    check("has validation_outcome",
          hasattr(dlg, "validation_outcome"))

    print()
    print("[2] Tabs")
    check("tab_widget exists", hasattr(dlg, "tab_widget"))
    check("4 tabs present", dlg.tab_widget.count() == 4)

    print()
    print("[3] Feed sample reply")
    dlg.response_edit.setPlainText(SAMPLE_REPLY)
    dlg._parse_response()

    print()
    print("[4] validation_outcome")
    outcome = dlg.validation_outcome
    check("outcome is not None", outcome is not None)
    if outcome:
        check("2 parsed", outcome.total == 2)
        check("1 valid", len(outcome.valid_requests) == 1)
        check("1 invalid", len(outcome.invalid_requests) == 1)
        # C-002 is rejected at the reference-check stage *before*
        # the warning collector runs, so no warning is emitted.
        check("0 warnings (only invalid was low-conf)",
              len(outcome.warnings) == 0)
        if outcome.valid_requests:
            check("valid id C-001",
                  outcome.valid_requests[0].id == "C-001")
        if outcome.invalid_requests:
            check("invalid id C-002",
                  outcome.invalid_requests[0][0].id == "C-002")
            check("invalid reason mentions Ghost",
                  "Ghost" in outcome.invalid_requests[0][1])

    print()
    print("[5] change_tree contents")
    tree = dlg.change_tree
    check("7 columns", tree.columnCount() == 7)
    check("2 rows (1 valid + 1 excluded)", tree.topLevelItemCount() == 2)

    if tree.topLevelItemCount() >= 1:
        row0 = tree.topLevelItem(0)
        check("row0 Action = add_transition",
              row0.text(1) == "add_transition")
        check("row0 Priority = high", row0.text(4) == "high")
        check("row0 Confidence = 0.95", row0.text(5) == "0.95")
        check("row0 Status = OK", row0.text(6) == "OK")
        check("row0 checkable & checked",
              bool(row0.flags() & Qt.ItemIsUserCheckable)
              and row0.checkState(0) == Qt.Checked)

    if tree.topLevelItemCount() >= 2:
        row1 = tree.topLevelItem(1)
        check("row1 Action = add_transition",
              row1.text(1) == "add_transition")
        check("row1 Priority = low", row1.text(4) == "low")
        check("row1 Confidence = 0.30", row1.text(5) == "0.30")
        check("row1 Status starts with EXCLUDED",
              row1.text(6).startswith("EXCLUDED:"))
        check("row1 not checkable",
              not bool(row1.flags() & Qt.ItemIsUserCheckable))

    print()
    print("[6] Apply valid changes")
    before = len(sm.transitions)
    dlg._apply_changes()
    after = len(sm.transitions)
    check("transition added", after == before + 1)
    check("transition is Idle->Active via START",
          any(t.source == "Idle" and t.event == "START"
              and t.target == "Active" for t in sm.transitions))

    print()
    print("=" * 70)
    print(f"  TOTAL: {_total}  PASSED: {_passed}  FAILED: {_failed}")
    print("=" * 70)
    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())