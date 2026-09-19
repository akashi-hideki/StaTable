#!/usr/bin/env python3
"""
P4-A (Editor UI: Transitions / Actions / Relations tabs) test suite for StaTable v2.2.

Verifies:
  1. ActionDraft.cell_actions / cell_relations  (draft.py extension)
  2. transition_to_flow_item / flow_item_to_transition  (early_return / label)
  3. TransitionsTab  API  (+ Target / Else target / Has else ComboBox)
  4. ActionsTab      API  (Pre / Post groups)
  5. RelationsTab    API  (explicit add; dialog disabled in offscreen mode)
  6. ActionEditorDialog 5-tab structure
  7. CodeWidget (Preview) cell_actions rendering

Run:
  python tests/test_v2_2_p4a.py
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ======================================================================
# Harness
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


def check_contains(name, haystack, needle, msg=""):
    if needle in haystack:
        RESULT.ok(name)
        return True
    else:
        RESULT.fail(name, msg or f"expected to contain: {needle!r}")
        return False


def qapp():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return None
    return QApplication.instance() or QApplication(sys.argv)


# ======================================================================
# 1. draft.py extensions
# ======================================================================
def test_draft_cell_fields():
    print("\n[1] ActionDraft.cell_actions / cell_relations")
    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
    except ImportError as e:
        RESULT.fail("import ActionDraft", str(e))
        return

    d = ActionDraft(source="Idle", event="START")
    check("cell_actions exists", hasattr(d, "cell_actions"),
          f"attrs={list(vars(d).keys())}")
    check("cell_relations exists", hasattr(d, "cell_relations"))
    check("cell_actions default empty",
          getattr(d, "cell_actions", None) == [])
    check("cell_relations default empty",
          getattr(d, "cell_relations", None) == [])


def test_draft_to_dict_roundtrip():
    print("\n[2] ActionDraft round-trip (to_dict / from_dict)")
    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable.model import ActionStep, TransitionRelation
    except ImportError as e:
        RESULT.fail("import", str(e))
        return

    d = ActionDraft(source="Idle", event="START")
    d.cell_actions = [
        ActionStep(role_function="Driver.PreCheck",
                   trigger="before_transitions"),
    ]
    d.cell_relations = [
        TransitionRelation(kind="group", members=["T1", "T2"],
                           shared_condition="cond_common"),
    ]
    data = d.to_dict()

    check("to_dict has cell_actions", "cell_actions" in data)
    check("to_dict has cell_relations", "cell_relations" in data)

    d2 = ActionDraft.from_dict(data)
    check("cell_actions round-trip",
          len(d2.cell_actions) == 1
          and d2.cell_actions[0].role_function == "Driver.PreCheck")
    check("cell_relations round-trip",
          len(d2.cell_relations) == 1
          and d2.cell_relations[0].shared_condition == "cond_common")


# ======================================================================
# 3. FlowItem param extension
# ======================================================================
def test_transition_to_flow_item_with_early_return():
    print("\n[3] transition_to_flow_item: early_return / label")
    try:
        from statable_gui.transition_editor_direct.draft import (
            transition_to_flow_item, flow_item_to_transition,
        )
        from statable.model import Transition
    except ImportError as e:
        RESULT.fail("import", str(e))
        return

    t = Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    )
    fi = transition_to_flow_item(t)

    check("FlowItem params has early_return",
          fi.params.get("early_return") is True,
          f"params={fi.params}")
    check("FlowItem params has label",
          fi.params.get("label") == "T1",
          f"params={fi.params}")

    t2 = flow_item_to_transition(fi, "Idle", "START")
    check("early_return round-trip", t2.early_return is True)
    check("label round-trip", t2.label == "T1")


# ======================================================================
# 4. TransitionsTab
# ======================================================================
def test_transitions_tab():
    print("\n[4] TransitionsTab")
    app = qapp()
    if app is None:
        RESULT.skip("TransitionsTab", "PySide6 not available")
        return

    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.transitions_tab import (
            TransitionsTab,
        )
        from statable.model import Transition
    except ImportError as e:
        RESULT.fail("import TransitionsTab", str(e))
        return

    draft = ActionDraft(source="Idle", event="START")
    tab = TransitionsTab(draft, states=["Idle", "Active", "Error"])

    check("initial row count 0", tab.row_count() == 0)

    row = tab.add_transition()
    check("add_transition returns 0", row == 0)
    check("row count 1", tab.row_count() == 1)

    t = Transition(source="Idle", event="START", condition="cond_A",
                   target="Active", early_return=True, label="T2")
    row = tab.add_transition(t)
    check("add_transition with explicit returns 1", row == 1)
    check("row count 2", tab.row_count() == 2)

    new_row = tab.move_up(1)
    check("move_up returns 0", new_row == 0)
    transitions = tab.get_transitions()
    check("move_up reorder",
          transitions[0].label == "T2" and transitions[1].label != "T2",
          f"got {[t.label for t in transitions]}")

    new_row = tab.move_down(0)
    check("move_down returns 1", new_row == 1)

    tab.delete_transition(0)
    check("delete row count 1", tab.row_count() == 1)

    t3 = Transition(source="Idle", event="START", condition="cond_C",
                    target="Error", early_return=False, label="T3")
    tab.set_transitions([t3])
    check("set_transitions row count 1", tab.row_count() == 1)
    got = tab.get_transitions()
    check("set/get round-trip",
          len(got) == 1 and got[0].label == "T3")


def test_transitions_tab_early_return_preserved():
    print("\n[4b] TransitionsTab: early_return preserved")
    app = qapp()
    if app is None:
        RESULT.skip("TransitionsTab early_return", "PySide6")
        return

    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.transitions_tab import (
            TransitionsTab,
        )
        from statable.model import Transition
    except ImportError as e:
        RESULT.fail("import", str(e))
        return

    draft = ActionDraft(source="Idle", event="START")
    tab = TransitionsTab(draft, states=["Idle", "Active"])

    t1 = Transition(source="Idle", event="START", condition="c1",
                    target="Active", early_return=True, label="T1")
    t2 = Transition(source="Idle", event="START", condition="c2",
                    target="Active", early_return=False, label="T2")
    tab.set_transitions([t1, t2])

    got = tab.get_transitions()
    check("T1 early_return=True preserved", got[0].early_return is True)
    check("T2 early_return=False preserved", got[1].early_return is False)
    check("T1 label preserved", got[0].label == "T1")
    check("T2 label preserved", got[1].label == "T2")


def test_transitions_tab_target_combo():
    print("\n[4c] TransitionsTab: Target / Else target / Has else as ComboBox")
    app = qapp()
    if app is None:
        RESULT.skip("TransitionsTab combo", "PySide6")
        return

    try:
        from PySide6.QtWidgets import QComboBox
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.transitions_tab import (
            TransitionsTab,
            COL_TARGET, COL_HAS_ELSE, COL_ELSE_TARGET, COL_MODE,
            NONE_LABEL,
        )
        from statable.model import Transition
    except ImportError as e:
        RESULT.fail("import combo test", str(e))
        return

    draft = ActionDraft(source="Idle", event="START")
    tab = TransitionsTab(draft, states=["Idle", "Active", "Error"])

    t = Transition(source="Idle", event="START",
                   condition="cA", target="Active",
                   has_else=True, else_target="Error",
                   early_return=True, label="T1")
    tab.add_transition(t)

    for col, name in (
        (COL_TARGET, "Target"),
        (COL_HAS_ELSE, "Has else"),
        (COL_ELSE_TARGET, "Else target"),
        (COL_MODE, "Mode"),
    ):
        w = tab.table.cellWidget(0, col)
        check(f"{name} is QComboBox",
              isinstance(w, QComboBox),
              f"got {type(w).__name__}")

    target_w = tab.table.cellWidget(0, COL_TARGET)
    items = [target_w.itemText(i) for i in range(target_w.count())]
    check("Target has (none)", NONE_LABEL in items, f"got {items}")
    check("Target has Active", "Active" in items, f"got {items}")
    check("Target has Error", "Error" in items, f"got {items}")
    check("Target currentText is Active",
          target_w.currentText() == "Active",
          f"got {target_w.currentText()}")

    et_w = tab.table.cellWidget(0, COL_ELSE_TARGET)
    check("Else target currentText is Error",
          et_w.currentText() == "Error",
          f"got {et_w.currentText()}")

    he_w = tab.table.cellWidget(0, COL_HAS_ELSE)
    check("Has else currentText is Yes",
          he_w.currentText() == "Yes",
          f"got {he_w.currentText()}")

    got = tab.get_transitions()
    check("get: target preserved", got[0].target == "Active")
    check("get: else_target preserved", got[0].else_target == "Error")
    check("get: has_else preserved", got[0].has_else is True)

    target_w.setCurrentText(NONE_LABEL)
    got = tab.get_transitions()
    check("get: (none) -> empty target", got[0].target == "")


def test_transitions_tab_has_else_link():
    print("\n[4d] TransitionsTab: has_else <-> else_target link")
    app = qapp()
    if app is None:
        RESULT.skip("has_else link", "PySide6")
        return

    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.transitions_tab import (
            TransitionsTab, COL_HAS_ELSE, COL_ELSE_TARGET,
        )
        from statable.model import Transition
    except ImportError as e:
        RESULT.fail("import", str(e))
        return

    draft = ActionDraft(source="Idle", event="START")
    tab = TransitionsTab(draft, states=["Idle", "Active"])

    t = Transition(source="Idle", event="START",
                   condition="cA", target="Active",
                   has_else=True, else_target="Idle",
                   early_return=True, label="T1")
    tab.add_transition(t)

    et_w = tab.table.cellWidget(0, COL_ELSE_TARGET)
    he_w = tab.table.cellWidget(0, COL_HAS_ELSE)

    check("else_target enabled when has_else=Yes",
          et_w.isEnabled() is True)

    he_w.setCurrentText("No")
    check("else_target disabled when has_else=No",
          et_w.isEnabled() is False)

    he_w.setCurrentText("Yes")
    check("else_target re-enabled",
          et_w.isEnabled() is True)


# ======================================================================
# 5. ActionsTab
# ======================================================================
def test_actions_tab():
    print("\n[5] ActionsTab (Pre / Post groups)")
    app = qapp()
    if app is None:
        RESULT.skip("ActionsTab", "PySide6")
        return

    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.actions_tab import (
            ActionsTab, TRIGGER_PRE, TRIGGER_POST,
        )
        from statable.model import ActionStep
    except ImportError as e:
        RESULT.fail("import ActionsTab", str(e))
        return

    draft = ActionDraft(source="Idle", event="START")
    tab = ActionsTab(draft, role_functions=["Driver.PreCheck", "Driver.Log"])

    check("initial row count 0", tab.row_count() == 0)

    tab.add_action(ActionStep(role_function="Driver.PreCheck",
                              trigger=TRIGGER_PRE))
    check("row count 1 after add_action(Pre)", tab.row_count() == 1)

    tab.add_action(ActionStep(role_function="Driver.Cleanup",
                              trigger=TRIGGER_POST))
    check("row count 2 after add_action(Post)", tab.row_count() == 2)

    got = tab.get_actions()
    check("2 actions returned", len(got) == 2,
          f"got {len(got)}")
    check("action[0] is Pre (before_transitions)",
          got[0].trigger == TRIGGER_PRE,
          f"got {got[0].trigger}")
    check("action[1] is Post (after_transitions)",
          got[1].trigger == TRIGGER_POST,
          f"got {got[1].trigger}")
    check("action[0] role_function preserved",
          got[0].role_function == "Driver.PreCheck",
          f"got {got[0].role_function}")
    check("action[1] role_function preserved",
          got[1].role_function == "Driver.Cleanup",
          f"got {got[1].role_function}")

    tab.delete_action(0)
    check("row count 1 after delete Pre", tab.row_count() == 1)
    got = tab.get_actions()
    check("remaining action is Post",
          len(got) == 1 and got[0].trigger == TRIGGER_POST,
          f"got {[(a.trigger, a.role_function) for a in got]}")

    tab.set_actions([
        ActionStep(role_function="A", trigger="before_transitions"),
        ActionStep(role_function="B", trigger="before_transitions"),
        ActionStep(role_function="C", trigger="after_transitions"),
    ])
    got = tab.get_actions()
    check("3 actions round-trip", len(got) == 3)
    check("two Pre actions first",
          got[0].trigger == TRIGGER_PRE
          and got[1].trigger == TRIGGER_PRE,
          f"got {[a.trigger for a in got]}")
    check("one Post action last",
          got[2].trigger == TRIGGER_POST,
          f"got {[a.trigger for a in got]}")
    check("Pre actions preserve order",
          got[0].role_function == "A" and got[1].role_function == "B",
          f"got {[a.role_function for a in got]}")
    check("Post action role_function",
          got[2].role_function == "C",
          f"got {got[2].role_function}")


# ======================================================================
# 6. RelationsTab
# ======================================================================
def test_relations_tab():
    print("\n[6] RelationsTab")
    app = qapp()
    if app is None:
        RESULT.skip("RelationsTab", "PySide6")
        return

    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.relations_tab import (
            RelationsTab,
        )
        from statable.model import TransitionRelation
    except ImportError as e:
        RESULT.fail("import RelationsTab", str(e))
        return

    draft = ActionDraft(source="Idle", event="START")
    tab = RelationsTab(draft)

    check("initial row count 0", tab.row_count() == 0)

    r1 = TransitionRelation(kind="sequential", members=["T1", "T2"])
    row = tab.add_relation(r1)
    check("add_relation(explicit) returns 0", row == 0)
    check("row count 1 after add_relation(explicit)",
          tab.row_count() == 1)

    r2 = TransitionRelation(kind="group", members=["T1", "T2"],
                            shared_condition="cond_common")
    tab.add_relation(r2)
    check("row count 2", tab.row_count() == 2)

    got = tab.get_relations()
    check("get_relations preserves kind",
          got[1].kind == "group")
    check("get_relations preserves members",
          got[1].members == ["T1", "T2"])
    check("get_relations preserves shared_condition",
          got[1].shared_condition == "cond_common")

    tab.delete_relation(0)
    check("delete row count 1", tab.row_count() == 1)

    tab.set_relations([
        TransitionRelation(kind="sequential", members=["T1", "T2"]),
        TransitionRelation(kind="exclusive", members=["T3"]),
    ])
    got = tab.get_relations()
    check("set/get round-trip",
          len(got) == 2
          and got[0].kind == "sequential"
          and got[1].kind == "exclusive")

    # NOTE: add_relation(None) opens a modal QMessageBox and would hang
    # in offscreen mode; we intentionally do not call it here.


# ======================================================================
# 7. ActionEditorDialog 5-tab structure
# ======================================================================
def test_dialog_tabs():
    print("\n[7] ActionEditorDialog: 5-tab structure")
    app = qapp()
    if app is None:
        RESULT.skip("ActionEditorDialog tabs", "PySide6")
        return

    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.dialog import (
            ActionEditorDialog,
        )
    except ImportError as e:
        RESULT.fail("import ActionEditorDialog", str(e))
        return

    draft = ActionDraft(source="Idle", event="START",
                        layer_name="Driver")
    dlg = ActionEditorDialog(
        draft,
        role_functions=["Driver.PreCheck", "Driver.Log"],
        states=["Idle", "Active"],
    )

    names = dlg.get_tab_names()
    check("has 5 tabs", len(names) == 5, f"got {names}")
    check("tab 0 is Transitions", names[0] == "Transitions", f"got {names}")
    check("tab 1 is Pre / Post Actions",
          names[1] == "Pre / Post Actions", f"got {names}")
    check("tab 2 is Relations", names[2] == "Relations", f"got {names}")
    check("tab 3 is Overview", names[3] == "Overview", f"got {names}")
    check("tab 4 is Preview", names[4] == "Preview", f"got {names}")


# ======================================================================
# 8. CodeWidget (Preview) cell_actions
# ======================================================================
def test_code_widget_cell_actions():
    print("\n[8] CodeWidget: cell_actions in preview")
    app = qapp()
    if app is None:
        RESULT.skip("CodeWidget cell_actions", "PySide6")
        return

    try:
        from statable_gui.transition_editor_direct.draft import (
            ActionDraft, FlowItem,
        )
        from statable_gui.transition_editor_direct.code_widget import CodeWidget
        from statable.model import ActionStep
    except ImportError as e:
        RESULT.fail("import CodeWidget", str(e))
        return

    draft = ActionDraft(source="Idle", event="START",
                        layer_name="Driver")
    draft.cell_actions = [
        ActionStep(role_function="Driver.PreCheck",
                   trigger="before_transitions"),
        ActionStep(role_function="Driver.Cleanup",
                   trigger="after_transitions"),
    ]
    fi = FlowItem(
        item_type="transition",
        name="START",
        edited_text="START",
        params={
            "event": "START",
            "condition": "cond_A",
            "target": "Active",
            "has_else": False,
            "early_return": True,
            "label": "T1",
            "pre_actions": [],
            "else_actions": [],
            "else_target": "",
        },
    )
    draft.flow_items.append(fi)

    widget = CodeWidget(draft)
    code = widget.toPlainText()

    check_contains("has PreCheck", code, "PreCheck")
    check_contains("has Cleanup", code, "Cleanup")
    check_contains("has cond_A", code, "cond_A")


# ======================================================================
# 9. Full integration
# ======================================================================
def test_draft_roundtrip_via_dialog():
    print("\n[9] Full: draft -> TransitionsTab -> get_transitions")
    app = qapp()
    if app is None:
        RESULT.skip("Full roundtrip", "PySide6")
        return

    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.transitions_tab import (
            TransitionsTab,
        )
        from statable.model import Transition
    except ImportError as e:
        RESULT.fail("import", str(e))
        return

    draft = ActionDraft(source="Idle", event="START")
    tab = TransitionsTab(draft, states=["Idle", "Active", "Error"])

    tab.set_transitions([
        Transition(source="Idle", event="START", condition="cA",
                   target="Active", has_else=False,
                   early_return=True, label="T1"),
        Transition(source="Idle", event="START", condition="cB",
                   target="Error", has_else=True, else_target="Idle",
                   early_return=True, label="T2"),
    ])

    transitions = tab.get_transitions()
    check("2 transitions", len(transitions) == 2)
    check("T1 has_else False", transitions[0].has_else is False)
    check("T2 has_else True", transitions[1].has_else is True)
    check("T2 else_target", transitions[1].else_target == "Idle")
    check("Both early_return True",
          transitions[0].early_return is True
          and transitions[1].early_return is True)


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2 P4-A (Editor UI) test suite")
    print("=" * 70)

    test_draft_cell_fields()
    test_draft_to_dict_roundtrip()
    test_transition_to_flow_item_with_early_return()
    test_transitions_tab()
    test_transitions_tab_early_return_preserved()
    test_transitions_tab_target_combo()
    test_transitions_tab_has_else_link()
    test_actions_tab()
    test_relations_tab()
    test_dialog_tabs()
    test_code_widget_cell_actions()
    test_draft_roundtrip_via_dialog()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()