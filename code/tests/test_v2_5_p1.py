# tests/test_v2_5_p1.py
"""StaTable v2.5 P1 (ActionEditorDialog role-function management) test suite.

Covers:
  - New buttons on _ActionGroup / TransitionsTab
  - _find_rf_by_display() qualified-vs-bare name resolution
  - _get_namespace_choices() candidate ordering and dedup
  - _dialog_kwargs() structure
  - _on_new / _on_edit / _on_delete role function
    (with RoleFunctionDialog mocked)

Regression focus:
  StateMachine.role_functions is keyed by *bare* name (rf.name), but
  the UI displays *qualified* names. The edit / delete handlers must
  resolve qualified -> bare before touching the dict; otherwise they
  silently fail with "not registered".
"""

import os
import sys
import logging

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CODE_DIR = os.path.dirname(_THIS_DIR)
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import (
    QApplication, QDialog, QPushButton, QMessageBox,
)

from statable.model import RoleFunction, ActionStep
from statable.state_machine import StateMachine

from statable_gui.libcntrl.role_function_library import RoleFunctionLibrary
from statable_gui.libcntrl.literal_library import LiteralLibrary

from statable_gui.transition_editor_direct.draft import ActionDraft
from statable_gui.transition_editor_direct.actions_tab import (
    ActionsTab, _ActionGroup, _qualified_name,
    TRIGGER_PRE, TRIGGER_POST,
)
from statable_gui.transition_editor_direct.transitions_tab import TransitionsTab


# Quiet the new debug logging (v2.5) during tests
logging.getLogger("transition_editor_direct.actions_tab").setLevel(
    logging.WARNING)
logging.getLogger("transition_editor_direct.transitions_tab").setLevel(
    logging.WARNING)


# ======================================================================
# Test harness
# ======================================================================
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


def find_button(widget, text):
    for btn in widget.findChildren(QPushButton):
        if text in btn.text():
            return btn
    return None


# ======================================================================
# Fixtures
# ======================================================================
def make_sm(layer_name="Application", roles=None):
    """Build a StateMachine.

    NOTE: StateMachine.__init__() does NOT accept `layer_name` as a
    keyword argument. Set it as an attribute after construction.
    """
    sm = StateMachine()
    sm.layer_name = layer_name
    for rf in (roles or []):
        sm.add_role_function(rf)
    return sm


def make_draft():
    return ActionDraft(source="Idle", event="START",
                       layer_name="Application")


def make_actions_tab(sm, role_functions=None, role_function_library=None,
                     literal_library=None, layer_names_provider=None):
    return ActionsTab(
        make_draft(),
        role_functions=role_functions,
        global_defs=None,
        state_machine=sm,
        role_function_library=role_function_library,
        literal_library=literal_library,
        layer_names_provider=layer_names_provider,
    )


def make_transitions_tab(sm, role_functions=None,
                         role_function_library=None,
                         literal_library=None,
                         layer_names_provider=None):
    return TransitionsTab(
        make_draft(),
        states=[],
        global_defs=None,
        state_machine=sm,
        role_function_library=role_function_library,
        literal_library=literal_library,
        layer_names_provider=layer_names_provider,
    )


# ======================================================================
# [1] Module import / _qualified_name helper
# ======================================================================
section("1. Module import & _qualified_name helper")

R.check("ActionsTab imported", ActionsTab is not None)
R.check("TransitionsTab imported", TransitionsTab is not None)
R.check("_ActionGroup imported", _ActionGroup is not None)

rf_qn = RoleFunction(name="Init", namespace="Driver")
R.check("_qualified_name(namespace+name)",
        _qualified_name(rf_qn) == "Driver.Init")

rf_bare = RoleFunction(name="Init", namespace="")
R.check("_qualified_name(bare)",
        _qualified_name(rf_bare) == "Init")


# ======================================================================
# [2] _ActionGroup: new kwargs + buttons
# ======================================================================
section("2. _ActionGroup constructor & buttons")

sm = make_sm()
group = _ActionGroup(
    "Pre", TRIGGER_PRE, [],
    role_function_library=RoleFunctionLibrary(),
    literal_library=LiteralLibrary(),
    layer_names_provider=None,
    global_defs=None,
    state_machine=sm,
)

R.check("role_function_library stored",
        group.role_function_library is not None)
R.check("literal_library stored", group.literal_library is not None)
R.check("state_machine stored", group.state_machine is sm)
R.check("layer_names_provider default None",
        group.layer_names_provider is None)

R.check("+ New Role Function button exists",
        find_button(group, "New Role Function") is not None)
R.check("Edit Role Function button exists",
        find_button(group, "Edit Role Function") is not None)
R.check("Delete Role Function button exists",
        find_button(group, "Delete Role Function") is not None)

R.check("new_role_btn attribute exists",
        hasattr(group, "new_role_btn"))
R.check("edit_role_btn attribute exists",
        hasattr(group, "edit_role_btn"))
R.check("delete_role_btn attribute exists",
        hasattr(group, "delete_role_btn"))


# ======================================================================
# [3] ActionsTab: new kwargs forwarded
# ======================================================================
section("3. ActionsTab new kwargs")

sm = make_sm()
rfl = RoleFunctionLibrary()
litl = LiteralLibrary()
lnp = lambda: ["Driver", "Middleware", "Application"]

tab = make_actions_tab(
    sm, role_functions=["Driver.Init"],
    role_function_library=rfl, literal_library=litl,
    layer_names_provider=lnp,
)

R.check("ActionsTab.role_function_library forwarded",
        tab.role_function_library is rfl)
R.check("ActionsTab.literal_library forwarded",
        tab.literal_library is litl)
R.check("ActionsTab.layer_names_provider forwarded",
        tab.layer_names_provider is lnp)
R.check("ActionsTab.state_machine forwarded", tab.state_machine is sm)

R.check("pre_group.role_function_library forwarded",
        tab.pre_group.role_function_library is rfl)
R.check("post_group.role_function_library forwarded",
        tab.post_group.role_function_library is rfl)
R.check("pre_group.state_machine forwarded",
        tab.pre_group.state_machine is sm)
R.check("post_group.state_machine forwarded",
        tab.post_group.state_machine is sm)

R.check("pre_group has new_role_btn",
        find_button(tab.pre_group, "New Role Function") is not None)
R.check("post_group has new_role_btn",
        find_button(tab.post_group, "New Role Function") is not None)


# ======================================================================
# [4] TransitionsTab: new kwargs + button
# ======================================================================
section("4. TransitionsTab new kwargs")

sm = make_sm()
rfl = RoleFunctionLibrary()
litl = LiteralLibrary()
lnp = lambda: ["Application"]

ttab = make_transitions_tab(
    sm, role_functions=["App.Init"],
    role_function_library=rfl, literal_library=litl,
    layer_names_provider=lnp,
)

R.check("TransitionsTab.role_function_library forwarded",
        ttab.role_function_library is rfl)
R.check("TransitionsTab.literal_library forwarded",
        ttab.literal_library is litl)
R.check("TransitionsTab.layer_names_provider forwarded",
        ttab.layer_names_provider is lnp)
R.check("TransitionsTab.state_machine forwarded",
        ttab.state_machine is sm)
R.check("+ New Role Function button exists on TransitionsTab",
        find_button(ttab, "New Role Function") is not None)


# ======================================================================
# [5] _find_rf_by_display: qualified / bare / miss
# ======================================================================
section("5. _find_rf_by_display")

sm = make_sm(layer_name="Application", roles=[
    RoleFunction(name="Init", namespace="App"),
    RoleFunction(name="Boot", namespace=""),
])
group = _ActionGroup(
    "Pre", TRIGGER_PRE, [],
    state_machine=sm,
)

rf1 = group._find_rf_by_display("App.Init")
R.check("resolve qualified name 'App.Init'", rf1 is not None)
R.check("resolved rf.name == 'Init'", rf1 is not None and rf1.name == "Init")

rf2 = group._find_rf_by_display("Init")
R.check("resolve bare name 'Init' via fallback",
        rf2 is not None and rf2.name == "Init")

rf3 = group._find_rf_by_display("Boot")
R.check("resolve bare name 'Boot'",
        rf3 is not None and rf3.name == "Boot")

rf_none = group._find_rf_by_display("Nonexistent.Func")
R.check("unknown name -> None", rf_none is None)

rf_empty = group._find_rf_by_display("")
R.check("empty name -> None", rf_empty is None)

group_no_sm = _ActionGroup("Pre", TRIGGER_PRE, [], state_machine=None)
R.check("no state_machine -> None",
        group_no_sm._find_rf_by_display("App.Init") is None)


# ======================================================================
# [6] _get_namespace_choices: order & dedup
# ======================================================================
section("6. _get_namespace_choices")

sm = make_sm(layer_name="Application", roles=[
    RoleFunction(name="Init", namespace="App"),
])
lnp = lambda: ["Driver", "Middleware", "Application"]

group = _ActionGroup(
    "Pre", TRIGGER_PRE, [],
    layer_names_provider=lnp,
    state_machine=sm,
)

choices = group._get_namespace_choices()
R.check("includes layer_names_provider entries",
        "Driver" in choices and "Middleware" in choices)
R.check("includes current layer_name",
        "Application" in choices)
R.check("includes role_functions namespace 'App'",
        "App" in choices)
R.check("no duplicates",
        len(choices) == len(set(choices)))

# Without provider, still includes sm.layer_name and namespaces
group_no_lnp = _ActionGroup(
    "Pre", TRIGGER_PRE, [],
    state_machine=sm,
)
choices2 = group_no_lnp._get_namespace_choices()
R.check("no provider -> still has sm.layer_name",
        "Application" in choices2)
R.check("no provider -> still has role namespace",
        "App" in choices2)

# With role_function_library
rfl = RoleFunctionLibrary()
rfl.add(RoleFunction(name="Ext", namespace="External"))
group_rfl = _ActionGroup(
    "Pre", TRIGGER_PRE, [],
    state_machine=sm,
    role_function_library=rfl,
)
choices3 = group_rfl._get_namespace_choices()
R.check("role_function_library namespace included",
        "External" in choices3)


# ======================================================================
# [7] _dialog_kwargs structure
# ======================================================================
section("7. _dialog_kwargs")

sm = make_sm(layer_name="Application", roles=[
    RoleFunction(name="Init", namespace="App"),
])
rfl = RoleFunctionLibrary()
rfl.add(RoleFunction(name="Ext", namespace="External"))
litl = LiteralLibrary()

group = _ActionGroup(
    "Pre", TRIGGER_PRE, [],
    state_machine=sm,
    role_function_library=rfl,
    literal_library=litl,
)

kwargs = group._dialog_kwargs()
R.check("kwargs has 'global_vars'", "global_vars" in kwargs)
R.check("kwargs has 'events'", "events" in kwargs)
R.check("kwargs has 'literals'", "literals" in kwargs)
R.check("kwargs has 'namespace_choices'", "namespace_choices" in kwargs)
R.check("namespace_choices is non-empty list",
        isinstance(kwargs["namespace_choices"], list)
        and len(kwargs["namespace_choices"]) > 0)


# ======================================================================
# [8] _on_new_role_function (mocked dialog)
# ======================================================================
section("8. _on_new_role_function")

sm = make_sm(layer_name="Application")
tab = make_actions_tab(sm, role_function_library=RoleFunctionLibrary(),
                       literal_library=LiteralLibrary())
group = tab.pre_group

new_rf = RoleFunction(name="TestFunc", namespace="App", title="Test")

signal_fired = [False]
group.changed.connect(lambda: signal_fired.__setitem__(0, True))

with patch(
    "statable_gui.transition_editor_direct.actions_tab."
    "RoleFunctionDialog"
) as mock_dlg:
    inst = MagicMock()
    inst.exec.return_value = QDialog.Accepted
    inst.get_role_function.return_value = new_rf
    mock_dlg.return_value = inst

    group._on_new_role_function()

R.check("rf registered in state_machine",
        "TestFunc" in sm.role_functions)
R.check("state_machine rf has namespace 'App'",
        sm.role_functions["TestFunc"].namespace == "App")
R.check("row appended to table",
        group.table.rowCount() == 1)
R.check("row text is qualified 'App.TestFunc'",
        group.table.item(0, 0).text() == "App.TestFunc")
R.check("changed signal emitted", signal_fired[0])
R.check("local role_functions list updated",
        "App.TestFunc" in group.role_functions)


# ======================================================================
# [9] _on_new_role_function: duplicate name warning
# ======================================================================
section("9. _on_new_role_function (duplicate)")

sm = make_sm(layer_name="Application", roles=[
    RoleFunction(name="TestFunc", namespace="App"),
])
tab = make_actions_tab(sm)
group = tab.pre_group

dup_rf = RoleFunction(name="TestFunc", namespace="App")

with patch(
    "statable_gui.transition_editor_direct.actions_tab.RoleFunctionDialog"
) as mock_dlg, patch(
    "statable_gui.transition_editor_direct.actions_tab.QMessageBox"
) as mock_mb:
    inst = MagicMock()
    inst.exec.return_value = QDialog.Accepted
    inst.get_role_function.return_value = dup_rf
    mock_dlg.return_value = inst

    group._on_new_role_function()

R.check("duplicate: warning shown", mock_mb.warning.called)
R.check("duplicate: no row added",
        group.table.rowCount() == 0)
R.check("duplicate: only 1 rf in sm",
        len(sm.role_functions) == 1)


# ======================================================================
# [10] _on_edit_role_function: REGRESSION (bare-name resolution)
# ======================================================================
section("10. _on_edit_role_function (regression)")

# This is the exact scenario that failed before the fix:
# UI displays "App.Init", but sm.role_functions is keyed by "Init".
sm = make_sm(layer_name="Application", roles=[
    RoleFunction(name="Init", namespace="App", title="Init"),
])
tab = make_actions_tab(sm)
group = tab.pre_group
group._append_row("App.Init")
group.table.setCurrentCell(0, 0)

updated_rf = RoleFunction(name="Init", namespace="NewApp",
                          title="Init (renamed ns)")

with patch(
    "statable_gui.transition_editor_direct.actions_tab.RoleFunctionDialog"
) as mock_dlg:
    inst = MagicMock()
    inst.exec.return_value = QDialog.Accepted
    inst.get_role_function.return_value = updated_rf
    mock_dlg.return_value = inst

    group._on_edit_role_function()

R.check("edit: rf namespace updated to 'NewApp'",
        sm.role_functions["Init"].namespace == "NewApp")
R.check("edit: row text updated to 'NewApp.Init'",
        group.table.item(0, 0).text() == "NewApp.Init")
R.check("edit: local role_functions synced",
        "NewApp.Init" in group.role_functions)
R.check("edit: old name removed from list",
        "App.Init" not in group.role_functions)


# ======================================================================
# [11] _on_edit_role_function: rename (name change)
# ======================================================================
section("11. _on_edit_role_function (rename)")

sm = make_sm(layer_name="Application", roles=[
    RoleFunction(name="OldName", namespace="App"),
])
tab = make_actions_tab(sm)
group = tab.pre_group
group._append_row("App.OldName")
group.table.setCurrentCell(0, 0)

renamed = RoleFunction(name="NewName", namespace="App")

with patch(
    "statable_gui.transition_editor_direct.actions_tab.RoleFunctionDialog"
) as mock_dlg:
    inst = MagicMock()
    inst.exec.return_value = QDialog.Accepted
    inst.get_role_function.return_value = renamed
    mock_dlg.return_value = inst

    group._on_edit_role_function()

R.check("rename: old key removed",
        "OldName" not in sm.role_functions)
R.check("rename: new key added",
        "NewName" in sm.role_functions)
R.check("rename: row text now 'App.NewName'",
        group.table.item(0, 0).text() == "App.NewName")


# ======================================================================
# [12] _on_edit_role_function: not registered -> info dialog
# ======================================================================
section("12. _on_edit_role_function (not registered)")

sm = make_sm(layer_name="Application")
tab = make_actions_tab(sm)
group = tab.pre_group
group._append_row("Ghost.Func")
group.table.setCurrentCell(0, 0)

with patch(
    "statable_gui.transition_editor_direct.actions_tab.RoleFunctionDialog"
) as mock_dlg, patch(
    "statable_gui.transition_editor_direct.actions_tab.QMessageBox"
) as mock_mb:
    group._on_edit_role_function()

R.check("not registered: no dialog opened",
        not mock_dlg.called)
R.check("not registered: info dialog shown",
        mock_mb.information.called)


# ======================================================================
# [13] _on_delete_role_function (mocked confirm)
# ======================================================================
section("13. _on_delete_role_function")

sm = make_sm(layer_name="Application", roles=[
    RoleFunction(name="Init", namespace="App"),
])
tab = make_actions_tab(sm)
group = tab.pre_group
group._append_row("App.Init")
group.table.setCurrentCell(0, 0)

signal_fired = [False]
group.changed.connect(lambda: signal_fired.__setitem__(0, True))

with patch(
    "statable_gui.transition_editor_direct.actions_tab.QMessageBox"
) as mock_mb:
    mock_mb.Yes = QMessageBox.Yes
    mock_mb.No = QMessageBox.No
    mock_mb.question.return_value = QMessageBox.Yes

    group._on_delete_role_function()

R.check("delete: rf removed from state_machine",
        "Init" not in sm.role_functions)
R.check("delete: row removed",
        group.table.rowCount() == 0)
R.check("delete: local role_functions cleared",
        "App.Init" not in group.role_functions)
R.check("delete: changed signal emitted", signal_fired[0])


# ======================================================================
# [14] _on_delete_role_function: user cancels
# ======================================================================
section("14. _on_delete_role_function (cancel)")

sm = make_sm(layer_name="Application", roles=[
    RoleFunction(name="Init", namespace="App"),
])
tab = make_actions_tab(sm)
group = tab.pre_group
group._append_row("App.Init")
group.table.setCurrentCell(0, 0)

with patch(
    "statable_gui.transition_editor_direct.actions_tab.QMessageBox"
) as mock_mb:
    mock_mb.Yes = QMessageBox.Yes
    mock_mb.No = QMessageBox.No
    mock_mb.question.return_value = QMessageBox.No

    group._on_delete_role_function()

R.check("cancel: rf still in state_machine",
        "Init" in sm.role_functions)
R.check("cancel: row still present",
        group.table.rowCount() == 1)


# ======================================================================
# [15] TransitionsTab._on_new_role_function (mocked dialog)
# ======================================================================
section("15. TransitionsTab._on_new_role_function")

sm = make_sm(layer_name="Application")
ttab = make_transitions_tab(
    sm,
    role_function_library=RoleFunctionLibrary(),
    literal_library=LiteralLibrary(),
)

new_rf = RoleFunction(name="CondFunc", namespace="App")

with patch(
    "statable_gui.transition_editor_direct.transitions_tab."
    "RoleFunctionDialog"
) as mock_dlg:
    inst = MagicMock()
    inst.exec.return_value = QDialog.Accepted
    inst.get_role_function.return_value = new_rf
    mock_dlg.return_value = inst

    ttab._on_new_role_function()

R.check("TransitionsTab: rf registered",
        "CondFunc" in sm.role_functions)
R.check("TransitionsTab: local role_functions updated",
        "App.CondFunc" in ttab.role_functions)


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