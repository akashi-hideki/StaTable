#!/usr/bin/env python3
"""StaTable R-7 + R-8 test suite.

R-7: RoleFunctionDialog "+ New Literal" button
R-8: ConditionBuilderDialog "+ New Template" button + tree category

Run:
  python tests/test_v2_5_p6.py
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
def make_literal_library():
    from statable_gui.libcntrl.literal_library import (
        LiteralLibrary, LiteralDefinition)
    lib = LiteralLibrary()
    lib.add(LiteralDefinition(
        name="EXISTING_LIT", value="1", literal_type="int"))
    return lib


def make_condition_library():
    from statable_gui.libcntrl.condition_library import (
        ConditionLibrary, ConditionTemplate)
    lib = ConditionLibrary()
    lib.add(ConditionTemplate(
        name="EXISTING_TMPL", condition="x != 0"))
    return lib


def make_global_defs():
    from statable.global_defs import GlobalDefinitions
    return GlobalDefinitions()


def make_state_machine():
    from statable.state_machine import StateMachine
    from statable.model import State, Event
    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_event(Event(name="START"))
    return sm


# ======================================================================
# R-7: RoleFunctionDialog
# ======================================================================
def test_r7_dialog_accepts_literal_library():
    print("\n[R-7][1] RoleFunctionDialog accepts literal_library")

    from statable_gui.role_function_dialog import RoleFunctionDialog

    lib = make_literal_library()
    dlg = RoleFunctionDialog(
        literals=["EXISTING_LIT"],
        literal_library=lib,
    )
    check("literal_library stored", dlg._literal_library is lib)
    check("+ New Literal button exists",
          hasattr(dlg, "new_literal_btn") and dlg.new_literal_btn is not None)
    check("button label is '+ New Literal'",
          dlg.new_literal_btn.text() == "+ New Literal")


def test_r7_dialog_backward_compat():
    print("\n[R-7][2] RoleFunctionDialog backward compat (no library)")

    from statable_gui.role_function_dialog import RoleFunctionDialog

    dlg = RoleFunctionDialog(literals=["A"])
    check("literal_library is None", dlg._literal_library is None)
    check("+ New Literal button not created",
          not hasattr(dlg, "new_literal_btn"))


def test_r7_dialog_new_literal_updates_list():
    print("\n[R-7][3] RoleFunctionDialog new literal updates list + library")

    from statable_gui.role_function_dialog import RoleFunctionDialog

    lib = make_literal_library()
    dlg = RoleFunctionDialog(
        literals=["EXISTING_LIT"],
        literal_library=lib,
    )
    initial_count = dlg.literal_list.count()

    # Manually add to library + list (simulating NewLiteralDialog OK)
    from statable_gui.libcntrl.literal_library import LiteralDefinition
    new_lit = LiteralDefinition(
        name="NEW_LIT", value="42", literal_type="int")
    lib.add(new_lit)

    from PySide6.QtWidgets import QListWidgetItem
    from PySide6.QtCore import Qt
    item = QListWidgetItem(new_lit.name)
    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
    item.setCheckState(Qt.Checked)
    dlg.literal_list.addItem(item)

    check("list count increased", dlg.literal_list.count() == initial_count + 1)
    check("library has NEW_LIT",
          lib.get("NEW_LIT") is not None)
    result = dlg.get_role_function()
    check("get_role_function includes NEW_LIT",
          "NEW_LIT" in result.used_literals)


# ======================================================================
# R-8: ConditionBuilderDialog
# ======================================================================
def test_r8_dialog_accepts_condition_library():
    print("\n[R-8][1] ConditionBuilderDialog accepts condition_library")

    from statable_gui.condition_builder_dialog import ConditionBuilderDialog

    lib = make_condition_library()
    dlg = ConditionBuilderDialog(
        global_defs=make_global_defs(),
        state_machine=make_state_machine(),
        condition_library=lib,
    )
    check("condition_library stored", dlg.condition_library is lib)
    check("+ New Template button exists",
          hasattr(dlg, "new_template_btn") and dlg.new_template_btn is not None)
    check("button label is '+ New Template'",
          dlg.new_template_btn.text() == "+ New Template")


def test_r8_dialog_backward_compat():
    print("\n[R-8][2] ConditionBuilderDialog backward compat (no library)")

    from statable_gui.condition_builder_dialog import ConditionBuilderDialog

    dlg = ConditionBuilderDialog(
        global_defs=make_global_defs(),
        state_machine=make_state_machine(),
    )
    check("condition_library is None", dlg.condition_library is None)
    check("+ New Template button not created",
          not hasattr(dlg, "new_template_btn"))


def test_r8_tree_shows_templates():
    print("\n[R-8][3] ConditionBuilderDialog tree shows templates")

    from statable_gui.condition_builder_dialog import ConditionBuilderDialog

    lib = make_condition_library()
    dlg = ConditionBuilderDialog(
        global_defs=make_global_defs(),
        state_machine=make_state_machine(),
        condition_library=lib,
    )
    # Find the "Condition templates" category in the tree
    tree = dlg.symbol_tree
    found_category = False
    found_tmpl = False
    for i in range(tree.topLevelItemCount()):
        top = tree.topLevelItem(i)
        if top.text(0) == "Condition templates":
            found_category = True
            for j in range(top.childCount()):
                child = top.child(j)
                if child.text(0) == "EXISTING_TMPL":
                    found_tmpl = True
                    break
    check("tree has 'Condition templates' category", found_category)
    check("tree contains EXISTING_TMPL", found_tmpl)


def test_r8_new_template_appears_in_tree():
    print("\n[R-8][4] New template appears in tree")

    from statable_gui.condition_builder_dialog import ConditionBuilderDialog
    from statable_gui.libcntrl.condition_library import ConditionTemplate

    lib = make_condition_library()
    dlg = ConditionBuilderDialog(
        global_defs=make_global_defs(),
        state_machine=make_state_machine(),
        condition_library=lib,
    )

    # Add a new template and refresh
    lib.add(ConditionTemplate(name="NEW_TMPL", condition="y == 1"))
    dlg._populate_tree()

    tree = dlg.symbol_tree
    found = False
    for i in range(tree.topLevelItemCount()):
        top = tree.topLevelItem(i)
        if top.text(0) == "Condition templates":
            for j in range(top.childCount()):
                if top.child(j).text(0) == "NEW_TMPL":
                    found = True
                    break
    check("NEW_TMPL appears in tree after refresh", found)


def test_r8_template_inserts_condition():
    print("\n[R-8][5] Template insertion inserts condition text")

    from statable_gui.condition_builder_dialog import ConditionBuilderDialog
    from statable_gui.libcntrl.condition_library import ConditionTemplate

    lib = make_condition_library()
    dlg = ConditionBuilderDialog(
        global_defs=make_global_defs(),
        state_machine=make_state_machine(),
        condition_library=lib,
    )

    # Simulate insertion: find template child, call _insert_symbol
    tree = dlg.symbol_tree
    for i in range(tree.topLevelItemCount()):
        top = tree.topLevelItem(i)
        if top.text(0) == "Condition templates":
            for j in range(top.childCount()):
                child = top.child(j)
                if child.text(0) == "EXISTING_TMPL":
                    dlg._insert_symbol(child, 0)
                    break
    text = dlg.condition_edit.toPlainText()
    check("condition editor contains 'x != 0'", "x != 0" in text, f"got: {text!r}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable R-7 + R-8 (dialog inline library creation)")
    print("=" * 70)

    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    test_r7_dialog_accepts_literal_library()
    test_r7_dialog_backward_compat()
    test_r7_dialog_new_literal_updates_list()
    test_r8_dialog_accepts_condition_library()
    test_r8_dialog_backward_compat()
    test_r8_tree_shows_templates()
    test_r8_new_template_appears_in_tree()
    test_r8_template_inserts_condition()

    ok = R.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()