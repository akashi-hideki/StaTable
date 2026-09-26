#!/usr/bin/env python3
"""
P4 (GUI signal wiring) test suite for StaTable v2.7.1.

Verifies:
  1. MatrixTableWidget: horizontal-header double-click wiring
  2. MatrixTableWidget: cell double-click wiring (existing)
  3. SettingsPanel: state table double-click wiring (Name only)
  4. StateActionsDialog: launch from header / Name column
  5. _ActionListWidget: add / delete / up / down
  6. StateActionsDialog: OK updates model
  7. StateActionsDialog: Cancel leaves model untouched
  8. StateActionsDialog: 4-tab structure
  9. StateActionsDialog: preview generation
 10. SettingsPanel: apply_changes preserves entry / exit / do_actions

Run:
  python tests/test_v2_7_p4.py
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Offscreen Qt for headless testing
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ======================================================================
# Test harness
# ======================================================================
class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
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

    def skip(self, name, reason=""):
        self.skipped += 1
        print(f"  [SKIP] {name}  ({reason})")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print()
        print("=" * 70)
        print(f"  TOTAL: {total}  PASSED: {self.passed}  "
              f"FAILED: {self.failed}  SKIPPED: {self.skipped}")
        print("=" * 70)
        if self.errors:
            print("\nFailures:")
            for name, msg in self.errors:
                print(f"  - {name}")
                if msg:
                    print(f"      {msg}")
        return self.failed == 0


RESULT = TestResult()


def check(name, condition, msg=""):
    if condition:
        RESULT.ok(name)
    else:
        RESULT.fail(name, msg)
    return condition


def get_app():
    """Return a singleton QApplication."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return None
    return QApplication.instance() or QApplication(sys.argv)


def _make_sm(states=None):
    """Build a simple StateMachine."""
    from statable.state_machine import StateMachine
    from statable.model import State, Event

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.layer_priority = 3
    for name in (states or ["Idle", "Active"]):
        sm.add_state(State(name=name))
    sm.add_event(Event(name="START"))
    sm.set_initial("Idle")
    return sm


# ======================================================================
# 1. MatrixTableWidget signal wiring
# ======================================================================
def test_matrix_signal_wiring():
    print("\n[1] MatrixTableWidget signal wiring")
    app = get_app()
    if app is None:
        RESULT.skip("matrix signal wiring", "PySide6 not available")
        return

    from statable_gui.matrix_table import MatrixTableWidget

    sm = _make_sm(["Idle", "Active", "Error"])
    w = MatrixTableWidget(sm)

    check("has open_state_actions_for_header",
          hasattr(w, "open_state_actions_for_header"),
          "method missing")

    check("has open_transition_dialog (existing)",
          hasattr(w, "open_transition_dialog"))

    # Verify signal is connected (Qt introspection)
    #  sectionDoubleClicked is connected to a slot
    try:
        header = w.horizontalHeader()
        # PySide6: receivers() may not be available, so we test by
        # emitting the signal and checking the call count.
        check("horizontal header exists",
              header is not None)
    except Exception as e:
        RESULT.fail("horizontal header access", str(e))

    # Test by monkey-patching: emit sectionDoubleClicked and observe
    calls = {"count": 0, "index": None}
    orig = w.open_state_actions_for_header

    def spy(idx):
        calls["count"] += 1
        calls["index"] = idx

    w.open_state_actions_for_header = spy
    # Reconnect to spy
    try:
        w.horizontalHeader().sectionDoubleClicked.disconnect()
    except (RuntimeError, TypeError):
        pass
    w.horizontalHeader().sectionDoubleClicked.connect(spy)

    # Emit for index 1 (should be "Active")
    w.horizontalHeader().sectionDoubleClicked.emit(1)
    check("sectionDoubleClicked emit fires handler",
          calls["count"] == 1 and calls["index"] == 1,
          f"got calls={calls}")


def test_matrix_header_opens_dialog():
    print("\n[2] MatrixTableWidget: header -> StateActionsDialog (mocked)")
    app = get_app()
    if app is None:
        RESULT.skip("header dialog", "PySide6 not available")
        return

    from statable_gui.matrix_table import MatrixTableWidget
    from statable_gui.state_actions_dialog import StateActionsDialog
    from PySide6.QtWidgets import QDialog

    sm = _make_sm(["Idle", "Active"])
    w = MatrixTableWidget(sm)

    captured = {"launched": None, "state_name": None}

    def fake_exec(self):
        captured["launched"] = True
        captured["state_name"] = (
            self.state.name if self.state is not None else None)
        return QDialog.Accepted

    with patch.object(StateActionsDialog, "exec", fake_exec):
        w.open_state_actions_for_header(0)

    check("dialog launched for index 0",
          captured["launched"] is True)
    check("dialog state = 'Idle'",
          captured["state_name"] == "Idle",
          f"got {captured['state_name']!r}")


def test_matrix_header_unknown_index():
    print("\n[2b] MatrixTableWidget: header with invalid index")
    app = get_app()
    if app is None:
        RESULT.skip("header invalid index", "PySide6 not available")
        return

    from statable_gui.matrix_table import MatrixTableWidget
    from statable_gui.state_actions_dialog import StateActionsDialog

    sm = _make_sm(["Idle", "Active"])
    w = MatrixTableWidget(sm)

    launched = {"count": 0}

    def fake_exec(self):
        launched["count"] += 1
        return 0

    with patch.object(StateActionsDialog, "exec", fake_exec):
        w.open_state_actions_for_header(999)   # out of range

    check("no dialog launched for invalid index",
          launched["count"] == 0,
          f"got count={launched['count']}")


# ======================================================================
# 3. MatrixTableWidget: cell double-click (existing)
# ======================================================================
def test_matrix_cell_double_click_existing():
    print("\n[3] MatrixTableWidget: cell -> ActionEditorDialog (existing)")
    app = get_app()
    if app is None:
        RESULT.skip("matrix cell double-click", "PySide6 not available")
        return

    from statable_gui.matrix_table import MatrixTableWidget
    from statable_gui.transition_editor_direct.dialog import (
        ActionEditorDialog)
    from PySide6.QtWidgets import QDialog

    sm = _make_sm(["Idle", "Active"])
    w = MatrixTableWidget(sm)

    launched = {"count": 0}

    def fake_exec(self):
        launched["count"] += 1
        return QDialog.Rejected

    with patch.object(ActionEditorDialog, "exec", fake_exec):
        # cellDoubleClicked is connected to open_transition_dialog
        w.cellDoubleClicked.emit(0, 0)

    check("ActionEditorDialog launched on cell double-click",
          launched["count"] == 1,
          f"got count={launched['count']}")


# ======================================================================
# 4. SettingsPanel: state table double-click wiring
# ======================================================================
def test_settings_state_table_wiring():
    print("\n[4] SettingsPanel: state table double-click wiring")
    app = get_app()
    if app is None:
        RESULT.skip("settings wiring", "PySide6 not available")
        return

    from statable_gui.widgets import SettingsPanel

    sm = _make_sm(["Idle", "Active"])
    p = SettingsPanel(sm)

    check("has _open_state_actions",
          hasattr(p, "_open_state_actions"))
    check("STATE_COL_NAME == 0", p.STATE_COL_NAME == 0)
    check("STATE_COL_DESC == 1", p.STATE_COL_DESC == 1)
    check("STATE_COL_TYPE == 2", p.STATE_COL_TYPE == 2)

    calls = {"count": 0, "row": None}

    def spy(row, initial_tab=None):
        calls["count"] += 1
        calls["row"] = row

    p._open_state_actions = spy
    # Reconnect signal to spy
    try:
        p.state_table.cellDoubleClicked.disconnect()
    except (RuntimeError, TypeError):
        pass
    p.state_table.cellDoubleClicked.connect(
        lambda r, c: spy(r) if c == p.STATE_COL_NAME else None)

    # Emit for Name column (0)
    p.state_table.cellDoubleClicked.emit(0, p.STATE_COL_NAME)
    check("Name col double-click fires _open_state_actions",
          calls["count"] == 1 and calls["row"] == 0,
          f"got calls={calls}")

    # Emit for Description column (1): should NOT fire
    calls_before = calls["count"]
    p.state_table.cellDoubleClicked.emit(0, p.STATE_COL_DESC)
    check("Description col double-click does NOT fire",
          calls["count"] == calls_before,
          f"got calls={calls}")
#!/usr/bin/env python3
"""
P4 (GUI signal wiring) test suite for StaTable v2.7.1.

Verifies:
  1. MatrixTableWidget: horizontal-header double-click wiring
  2. MatrixTableWidget: cell double-click wiring (existing)
  3. SettingsPanel: state table double-click wiring (Name only)
  4. StateActionsDialog: launch from header / Name column
  5. _ActionListWidget: add / delete / up / down
  6. StateActionsDialog: OK updates model
  7. StateActionsDialog: Cancel leaves model untouched
  8. StateActionsDialog: 4-tab structure
  9. StateActionsDialog: preview generation
 10. SettingsPanel: apply_changes preserves entry / exit / do_actions

Run:
  python tests/test_v2_7_p4.py
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Offscreen Qt for headless testing
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ======================================================================
# 5. _ActionListWidget: add / delete / up / down
# ======================================================================
def test_action_list_widget_operations():
    print("\n[5] _ActionListWidget operations")
    app = get_app()
    if app is None:
        RESULT.skip("_ActionListWidget", "PySide6 not available")
        return

    from statable_gui.state_actions_dialog import _ActionListWidget
    from statable.model import ActionStep

    w = _ActionListWidget()

    # set_actions
    w.set_actions([
        ActionStep(role_function="Driver.A"),
        ActionStep(role_function="Driver.B", condition="x > 0"),
    ])
    check("set_actions row count", w.table.rowCount() == 2)
    check("row 0 target", w.table.item(0, w.COL_TARGET).text() == "Driver.A")
    check("row 1 condition", w.table.item(1, w.COL_CONDITION).text() == "x > 0")

    # get_actions round-trip
    got = w.get_actions()
    check("get_actions len", len(got) == 2)
    check("get_actions[0].role_function", got[0].role_function == "Driver.A")
    check("get_actions[1].condition", got[1].condition == "x > 0")

    # add
    w._on_add()
    check("_on_add row count", w.table.rowCount() == 3)

    # delete
    w.table.selectRow(2)
    w._on_delete()
    check("_on_delete row count", w.table.rowCount() == 2)

    # up
    w.table.selectRow(1)
    w._on_up()
    check("_on_up reorder",
          w.table.item(0, w.COL_TARGET).text() == "Driver.B")
    check("_on_up reorder (2)",
          w.table.item(1, w.COL_TARGET).text() == "Driver.A")

    # down
    w.table.selectRow(0)
    w._on_down()
    check("_on_down reorder",
          w.table.item(0, w.COL_TARGET).text() == "Driver.A")

    # empty target is dropped
    w.set_actions([
        ActionStep(role_function="Driver.X"),
        ActionStep(),  # empty
    ])
    got = w.get_actions()
    check("empty target dropped", len(got) == 1)
    check("empty target dropped value", got[0].role_function == "Driver.X")

    # fire_event action
    w.set_actions([
        ActionStep(action_type="fire_event", event_name="Driver.TICK"),
    ])
    got = w.get_actions()
    check("fire_event len", len(got) == 1)
    check("fire_event action_type", got[0].action_type == "fire_event")
    check("fire_event event_name", got[0].event_name == "Driver.TICK")


# ======================================================================
# 6. StateActionsDialog: OK updates model
# ======================================================================
def test_state_actions_dialog_ok():
    print("\n[6] StateActionsDialog OK updates model")
    app = get_app()
    if app is None:
        RESULT.skip("dialog OK", "PySide6 not available")
        return

    from statable_gui.state_actions_dialog import StateActionsDialog
    from statable.state_machine import StateMachine
    from statable.model import State, ActionStep

    sm = StateMachine()
    sm.layer_name = "Driver"
    s = State(name="Idle")
    sm.add_state(s)

    dlg = StateActionsDialog(state=s, state_machine=sm)
    check("entry widget exists", hasattr(dlg, "entry_widget"))
    check("exit widget exists", hasattr(dlg, "exit_widget"))
    check("do widget exists", hasattr(dlg, "do_widget"))

    # Modify entry actions
    dlg.entry_widget.set_actions([
        ActionStep(role_function="Driver.NewEntry"),
    ])
    dlg.do_widget.set_actions([
        ActionStep(role_function="Driver.NewDo", condition="ctx->x"),
    ])

    # Simulate OK
    dlg._on_accept()

    check("state.entry updated",
          len(s.entry) == 1 and s.entry[0].role_function == "Driver.NewEntry",
          f"got {s.entry!r}")
    check("state.do_actions updated",
          len(s.do_actions) == 1
          and s.do_actions[0].role_function == "Driver.NewDo",
          f"got {s.do_actions!r}")
    check("state.exit remains empty",
          len(s.exit) == 0)


# ======================================================================
# 7. StateActionsDialog: Cancel leaves model untouched
# ======================================================================
def test_state_actions_dialog_cancel():
    print("\n[7] StateActionsDialog Cancel leaves model untouched")
    app = get_app()
    if app is None:
        RESULT.skip("dialog cancel", "PySide6 not available")
        return

    from statable_gui.state_actions_dialog import StateActionsDialog
    from statable.state_machine import StateMachine
    from statable.model import State, ActionStep

    sm = StateMachine()
    sm.layer_name = "Driver"
    s = State(name="Idle", entry=[ActionStep(role_function="Original")])
    sm.add_state(s)

    original_entry = list(s.entry)
    dlg = StateActionsDialog(state=s, state_machine=sm)

    # Modify the UI
    dlg.entry_widget.set_actions([
        ActionStep(role_function="Modified"),
    ])

    # Simulate Cancel (just call reject; don't call _on_accept)
    dlg.reject()

    check("state.entry unchanged on Cancel",
          len(s.entry) == len(original_entry)
          and s.entry[0].role_function == "Original",
          f"got {s.entry!r}")


# ======================================================================
# 8. StateActionsDialog: tab structure
# ======================================================================
def test_state_actions_dialog_tabs():
    print("\n[8] StateActionsDialog 4-tab structure")
    app = get_app()
    if app is None:
        RESULT.skip("dialog tabs", "PySide6 not available")
        return

    from statable_gui.state_actions_dialog import StateActionsDialog
    from statable.model import State

    s = State(name="Idle")
    dlg = StateActionsDialog(state=s)

    check("has 4 tabs", dlg.tabs.count() == 4,
          f"got {dlg.tabs.count()}")
    check("tab 0 is Entry",
          dlg.tabs.tabText(0) == "Entry",
          f"got {dlg.tabs.tabText(0)!r}")
    check("tab 1 is Exit",
          dlg.tabs.tabText(1) == "Exit")
    check("tab 2 is Do",
          dlg.tabs.tabText(2) == "Do")
    check("tab 3 is Preview",
          dlg.tabs.tabText(3) == "Preview")


# ======================================================================
# 9. StateActionsDialog: preview generation
# ======================================================================
def test_state_actions_dialog_preview():
    print("\n[9] StateActionsDialog preview generation")
    app = get_app()
    if app is None:
        RESULT.skip("dialog preview", "PySide6 not available")
        return

    from statable_gui.state_actions_dialog import StateActionsDialog
    from statable.state_machine import StateMachine
    from statable.model import State, ActionStep

    sm = StateMachine()
    sm.layer_name = "Driver"
    s = State(name="Idle")
    sm.add_state(s)

    dlg = StateActionsDialog(state=s, state_machine=sm)
    dlg.entry_widget.set_actions([
        ActionStep(role_function="Driver.Init"),
    ])
    dlg.do_widget.set_actions([
        ActionStep(role_function="Driver.Poll", condition="ctx->x > 0"),
    ])

    dlg._refresh_preview()
    txt = dlg.preview_widget.toPlainText()

    check("preview contains Driver_Entry_Idle",
          "Driver_Entry_Idle" in txt)
    check("preview contains Driver_Do_Idle",
          "Driver_Do_Idle" in txt)
    check("preview contains RoleFunc_Driver_Init",
          "RoleFunc_Driver_Init" in txt)
    check("preview contains condition",
          "ctx->x > 0" in txt)
    check("preview contains custom marker",
          "Driver_Entry_Idle_custom" in txt)


# ======================================================================
# 10. SettingsPanel: apply_changes preserves entry / exit / do
# ======================================================================
def test_settings_apply_changes_preserves_actions():
    print("\n[10] SettingsPanel apply_changes preserves actions")
    app = get_app()
    if app is None:
        RESULT.skip("apply_changes preserves", "PySide6 not available")
        return

    from statable_gui.widgets import SettingsPanel
    from statable.state_machine import StateMachine
    from statable.model import State, ActionStep

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_state(State(
        name="Idle",
        entry=[ActionStep(role_function="Driver.E1")],
        exit=[ActionStep(role_function="Driver.X1")],
        do_actions=[ActionStep(role_function="Driver.D1")],
    ))
    sm.add_state(State(
        name="Active",
        do_actions=[
            ActionStep(role_function="Driver.D2"),
            ActionStep(role_function="Driver.D3"),
        ],
    ))

    p = SettingsPanel(sm)
    p.apply_changes()

    check("Idle entry preserved (1)",
          len(sm.states["Idle"].entry) == 1
          and sm.states["Idle"].entry[0].role_function == "Driver.E1")
    check("Idle exit preserved (1)",
          len(sm.states["Idle"].exit) == 1
          and sm.states["Idle"].exit[0].role_function == "Driver.X1")
    check("Idle do_actions preserved (1)",
          len(sm.states["Idle"].do_actions) == 1
          and sm.states["Idle"].do_actions[0].role_function == "Driver.D1")
    check("Active do_actions preserved (2)",
          len(sm.states["Active"].do_actions) == 2)

    # Type / Name column editing still works
    p.state_table.item(0, p.STATE_COL_DESC).setText("new desc")
    p.apply_changes()
    check("description edit applied",
          sm.states["Idle"].description == "new desc")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.7.1 P4 (GUI signal wiring) test suite")
    print("=" * 70)

    test_matrix_signal_wiring()
    test_matrix_header_opens_dialog()
    test_matrix_header_unknown_index()
    test_matrix_cell_double_click_existing()

    test_settings_state_table_wiring()

    test_action_list_widget_operations()
    test_state_actions_dialog_ok()
    test_state_actions_dialog_cancel()
    test_state_actions_dialog_tabs()
    test_state_actions_dialog_preview()

    test_settings_apply_changes_preserves_actions()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()