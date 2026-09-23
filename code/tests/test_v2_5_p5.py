#!/usr/bin/env python3
"""StaTable R-6 (Namespace all-tabs wiring) test suite.

Verifies that layer_names_provider flows through all 4 hops:

    MainWindow._get_all_layer_names
        → StateMachineTab
            → MatrixTableWidget
                → ActionEditorDialog
                    → TransitionsTab / ActionsTab

Run:
  python tests/test_v2_5_p5.py
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
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

    def summary(self):
        total = self.passed + self.failed
        print()
        print("=" * 70)
        print(f"  TOTAL: {total}  PASSED: {self.passed}  FAILED: {self.failed}")
        print("=" * 70)
        if self.errors:
            print("\nFailures:")
            for name, msg in self.errors:
                print(f"  - {name}")
                if msg:
                    print(f"      {msg}")
        return self.failed == 0


R = TestResult()


def check(name, cond, msg=""):
    if cond:
        R.ok(name)
    else:
        R.fail(name, msg)
    return cond


# ======================================================================
# Fixtures
# ======================================================================
def make_sm(layer_name="Application"):
    from statable.state_machine import StateMachine
    from statable.model import State, Event
    sm = StateMachine()
    sm.layer_name = layer_name
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    return sm


# ======================================================================
# [1] ActionEditorDialog accepts layer_names_provider
# ======================================================================
def test_action_editor_accepts_lnp():
    print("\n[1] ActionEditorDialog accepts layer_names_provider")

    from statable_gui.transition_editor_direct.dialog import (
        ActionEditorDialog)
    from statable_gui.transition_editor_direct.draft import ActionDraft

    draft = ActionDraft(source="Idle", event="START", layer_name="Application")

    def provider():
        return ["Application", "Driver", "Middleware"]

    dlg = ActionEditorDialog(
        draft,
        states=["Idle", "Active"],
        state_machine=make_sm(),
        layer_names_provider=provider,
    )
    check("dialog stores layer_names_provider",
          dlg.layer_names_provider is provider)

    check("TransitionsTab received layer_names_provider",
          getattr(dlg.transitions_tab, "layer_names_provider", None) is provider)
    check("ActionsTab received layer_names_provider",
          getattr(dlg.actions_tab, "layer_names_provider", None) is provider)


# ======================================================================
# [2] ActionEditorDialog handles None provider (backward compat)
# ======================================================================
def test_action_editor_none_lnp():
    print("\n[2] ActionEditorDialog handles None provider")

    from statable_gui.transition_editor_direct.dialog import (
        ActionEditorDialog)
    from statable_gui.transition_editor_direct.draft import ActionDraft

    draft = ActionDraft(source="Idle", event="START", layer_name="Application")
    dlg = ActionEditorDialog(
        draft,
        states=["Idle"],
        state_machine=make_sm(),
    )
    check("dialog stores None", dlg.layer_names_provider is None)
    check("TransitionsTab.lnp is None",
          getattr(dlg.transitions_tab, "layer_names_provider", "X") is None)
    check("ActionsTab.lnp is None",
          getattr(dlg.actions_tab, "layer_names_provider", "X") is None)


# ======================================================================
# [3] MatrixTableWidget accepts layer_names_provider
# ======================================================================
def test_matrix_table_accepts_lnp():
    print("\n[3] MatrixTableWidget accepts layer_names_provider")

    from statable_gui.matrix_table import MatrixTableWidget

    def provider():
        return ["Application", "Driver"]

    widget = MatrixTableWidget(
        make_sm(),
        layer_names_provider=provider,
    )
    check("MatrixTableWidget stores layer_names_provider",
          widget.layer_names_provider is provider)


# ======================================================================
# [4] MatrixTableWidget passes it to ActionEditorDialog
# ======================================================================
def test_matrix_table_forwards_to_dialog():
    print("\n[4] MatrixTableWidget forwards to ActionEditorDialog")

    from statable_gui.matrix_table import MatrixTableWidget
    from statable_gui.transition_editor_direct import dialog as dlg_mod
    import statable_gui.matrix_table as mt_mod

    captured = {}

    class CapturedDialog:
        def __init__(self, draft, **kwargs):
            captured.update(kwargs)
            captured["draft"] = draft

        def exec(self):
            return 0  # rejected

    original_dlg = dlg_mod.ActionEditorDialog
    original_mt = mt_mod.ActionEditorDialog

    dlg_mod.ActionEditorDialog = CapturedDialog
    mt_mod.ActionEditorDialog = CapturedDialog
    try:
        def provider():
            return ["Application", "Driver"]

        widget = MatrixTableWidget(make_sm(), layer_names_provider=provider)
        widget.open_transition_dialog(0, 0)
        check("ActionEditorDialog received layer_names_provider",
              captured.get("layer_names_provider") is provider)
    finally:
        dlg_mod.ActionEditorDialog = original_dlg
        mt_mod.ActionEditorDialog = original_mt


# ======================================================================
# [5] StateMachineTab forwards to MatrixTableWidget
# ======================================================================
def test_state_machine_tab_forwards():
    print("\n[5] StateMachineTab forwards layer_names_provider")

    from statable_gui.widgets import StateMachineTab

    def provider():
        return ["Application", "Driver", "Middleware"]

    tab = StateMachineTab(
        make_sm(),
        layer_names_provider=provider,
    )
    check("StateMachineTab stores provider",
          tab.layer_names_provider is provider)
    check("MatrixTableWidget received provider",
          tab.table.layer_names_provider is provider)
    check("SettingsPanel received provider",
          tab.settings.layer_names_provider is provider)


# ======================================================================
# [6] End-to-end namespace choices (SettingsPanel)
# ======================================================================
def test_end_to_end_namespace_choices():
    print("\n[6] End-to-end: namespace choices include all layers")

    from statable_gui.widgets import StateMachineTab

    def provider():
        return ["Application", "Driver", "Middleware"]

    tab = StateMachineTab(
        make_sm("Application"),
        layer_names_provider=provider,
    )
    choices = tab.settings._get_namespace_choices()
    check("Application in choices", "Application" in choices, f"got {choices}")
    check("Driver in choices", "Driver" in choices, f"got {choices}")
    check("Middleware in choices", "Middleware" in choices, f"got {choices}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable R-6 (Namespace all-tabs wiring)")
    print("=" * 70)

    # QApplication is required before creating any QWidget / QDialog.
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    test_action_editor_accepts_lnp()
    test_action_editor_none_lnp()
    test_matrix_table_accepts_lnp()
    test_matrix_table_forwards_to_dialog()
    test_state_machine_tab_forwards()
    test_end_to_end_namespace_choices()

    ok = R.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()