#!/usr/bin/env python3
"""
P3 (Display layer) test suite for StaTable v2.2.

Verifies:
  1. mermaid_gen: multiple transitions per cell -> multiple edges
  2. mermaid_gen: else_target rendered as a separate edge
  3. mermaid_gen: entry/exit does not appear (metadata only)
  4. mermaid_gen: backward compat (single transition)
  5. matrix_table: _truncate_text helper
  6. matrix_table: _build_transition_tooltip includes early_return
  7. matrix_table: _event_header_label (Q / D prefixes)
  8. matrix_table: cell label shows multiple targets
  9. matrix_table: cell label marks Commit / Tentative
 10. SettingsPanel: entry / exit as list (Qt offscreen)
 11. TransitionListDialog: Mode column (Qt offscreen)
 12. Full round: XML -> SM -> matrix label / mermaid

Run:
  python tests/test_v2_2_p3.py
  pytest tests/test_v2_2_p3.py -v
"""

import os
import sys
from pathlib import Path

# Offscreen Qt for headless testing (must be set BEFORE importing PySide6)
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


def check_contains(name, haystack, needle, msg=""):
    if needle in haystack:
        RESULT.ok(name)
        return True
    else:
        RESULT.fail(name, msg or f"expected to contain: {needle!r}\n"
                                f"--- got ---\n{haystack}\n-----------")
        return False


def check_not_contains(name, haystack, needle):
    if needle not in haystack:
        RESULT.ok(name)
        return True
    else:
        RESULT.fail(name, f"should NOT contain: {needle!r}\n"
                          f"--- got ---\n{haystack}\n-----------")


# ======================================================================
# Fixtures
# ======================================================================
def make_sm_with_transitions(transitions, layer_name="Driver",
                              entry_exit=None):
    """Build a StateMachine with the given transitions."""
    from statable.state_machine import StateMachine
    from statable.model import State, Event

    sm = StateMachine()
    sm.layer_name = layer_name

    states = set()
    events = set()
    for t in transitions:
        states.add(t.source)
        if t.target:
            states.add(t.target)
        if t.else_target:
            states.add(t.else_target)
        events.add(t.event)

    for s in sorted(states):
        entry = []
        exit_ = []
        if entry_exit and s in entry_exit:
            entry = entry_exit[s].get("entry", [])
            exit_ = entry_exit[s].get("exit", [])
        sm.add_state(State(name=s, entry=entry, exit=exit_))

    for e in sorted(events):
        if e:
            sm.add_event(Event(name=e))
    # Always add a completion event (empty name)
    sm.add_event(Event(name=""))

    for t in transitions:
        sm.add_transition(t)

    return sm


# ======================================================================
# 1. mermaid_gen: multiple targets
# ======================================================================
def test_mermaid_multiple_targets():
    print("\n[1] mermaid_gen: multiple transitions -> multiple edges")
    from statable.model import Transition
    from statable.mermaid_gen import generate_mermaid

    t1 = Transition(source="Idle", event="START", condition="cond_A",
                    target="Active", early_return=True, label="T1")
    t2 = Transition(source="Idle", event="START", condition="cond_B",
                    target="Error", early_return=True, label="T2")

    sm = make_sm_with_transitions([t1, t2])
    code = generate_mermaid(sm)

    check_contains("edge Idle->Active", code, "Idle --> Active")
    check_contains("edge Idle->Error", code, "Idle --> Error")
    check_contains("label has cond_A", code, "cond_A")
    check_contains("label has cond_B", code, "cond_B")


def test_mermaid_else_target():
    print("\n[2] mermaid_gen: else_target rendered")
    from statable.model import Transition
    from statable.mermaid_gen import generate_mermaid

    t = Transition(source="Idle", event="START", condition="cond_A",
                   target="Active", has_else=True, else_target="Error",
                   early_return=True, label="T1")
    sm = make_sm_with_transitions([t])
    code = generate_mermaid(sm)

    check_contains("then edge Idle->Active", code, "Idle --> Active")
    # else edge should appear (implementation-specific; may use "else" label)
    check("else edge present (Idle->Error)",
          "Idle --> Error" in code,
          f"--- got ---\n{code}\n-----------")


def test_mermaid_no_entry_exit():
    print("\n[3] mermaid_gen: entry/exit NOT shown")
    from statable.model import Transition
    from statable.mermaid_gen import generate_mermaid

    t = Transition(source="Idle", event="START", condition="cond_A",
                   target="Active", early_return=True, label="T1")
    sm = make_sm_with_transitions(
        [t],
        entry_exit={
            "Idle": {"exit": ["Driver.IdleExit"]},
            "Active": {"entry": ["Driver.ActiveEntry"]},
        },
    )
    code = generate_mermaid(sm)

    check_not_contains("no exit fn in mermaid", code, "IdleExit")
    check_not_contains("no entry fn in mermaid", code, "ActiveEntry")


def test_mermaid_backward_compat():
    print("\n[4] mermaid_gen: backward compat (single transition)")
    from statable.model import Transition
    from statable.mermaid_gen import generate_mermaid

    t = Transition(source="Idle", event="START", condition="cond_A",
                   target="Active")
    sm = make_sm_with_transitions([t])
    code = generate_mermaid(sm)

    check_contains("edge Idle->Active", code, "Idle --> Active")
    check_contains("has START label", code, "START")
    check_contains("has stateDiagram header", code, "stateDiagram-v2")


# ======================================================================
# 5. matrix_table helpers
# ======================================================================
def test_truncate_text():
    print("\n[5] matrix_table._truncate_text")
    from statable_gui.matrix_table import _truncate_text

    check("short text unchanged",
          _truncate_text("abc", 10) == "abc")
    check("exact limit unchanged",
          _truncate_text("abcdefghij", 10) == "abcdefghij")
    long = _truncate_text("abcdefghijklmnop", 10)
    check("long text truncated", long.endswith("..."))
    check("truncated length <= max + 3",
          len(long) <= 13, f"got {len(long)}")


def test_build_transition_tooltip():
    print("\n[6] matrix_table._build_transition_tooltip")
    from statable.model import Transition
    from statable_gui.matrix_table import _build_transition_tooltip

    t = Transition(source="Idle", event="START", condition="cond_A",
                   target="Active", early_return=True, label="T1",
                   title="TestTitle")
    tip = _build_transition_tooltip(t)

    check_contains("has title", tip, "TestTitle")
    check_contains("has target", tip, "Active")
    check_contains("has event", tip, "START")
    check_contains("has condition", tip, "cond_A")
    # v2.2: mode (Commit/Tentative) should be visible
    check("has Commit marker",
          "Commit" in tip or "commit" in tip,
          f"--- got ---\n{tip}\n-----------")

    t2 = Transition(source="Idle", event="START", condition="cond_B",
                    target="Active", early_return=False)
    tip2 = _build_transition_tooltip(t2)
    check("has Tentative marker",
          "Tentative" in tip2 or "tentative" in tip2,
          f"--- got ---\n{tip2}\n-----------")


def test_event_header_label():
    print("\n[7] matrix_table._event_header_label")
    from statable.model import EventDeliveryType
    from statable_gui.matrix_table import _event_header_label

    check("DIRECT no prefix",
          _event_header_label("START", EventDeliveryType.DIRECT) == "START")
    check("QUEUE has [Q]",
          _event_header_label("START", EventDeliveryType.QUEUE) == "[Q] START")
    check("DOUBLE has [D]",
          _event_header_label("START", EventDeliveryType.DOUBLE) == "[D] START")


# ======================================================================
# 8. matrix_table cell label
# ======================================================================
def test_matrix_cell_label_single():
    print("\n[8] matrix_table._generate_cell_label (single)")
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        RESULT.skip("matrix label (single)", "PySide6 not available")
        return

    app = QApplication.instance() or QApplication(sys.argv)

    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition
    from statable_gui.matrix_table import MatrixTableWidget

    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        early_return=True, label="T1",
    ))

    w = MatrixTableWidget(sm)
    t = sm.transitions[0]
    label = w._generate_cell_label(t, "START")

    check("label not empty", bool(label), f"got {label!r}")
    check_contains("label has Active", label, "Active")
    check("label has Commit/Tentative marker",
          "Commit" in label or "Tentative" in label
          or "[C]" in label or "[T]" in label,
          f"got {label!r}")


def test_matrix_cell_label_multiple():
    print("\n[8b] matrix_table cell with multiple transitions")
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        RESULT.skip("matrix label (multiple)", "PySide6 not available")
        return

    app = QApplication.instance() or QApplication(sys.argv)

    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition
    from statable_gui.matrix_table import MatrixTableWidget

    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_state(State(name="Error"))
    sm.add_event(Event(name="START"))
    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        early_return=True, label="T1",
    ))
    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="cond_B", target="Error",
        early_return=False, label="T2",
    ))

    w = MatrixTableWidget(sm)
    items = w._find_transitions("Idle", "START")
    check("2 transitions found", len(items) == 2,
          f"got {len(items)}")


# ======================================================================
# 9. SettingsPanel entry/exit list
# ======================================================================
def test_settings_panel_entry_exit_list():
    print("\n[9] SettingsPanel: entry/exit as list")
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        RESULT.skip("SettingsPanel entry/exit", "PySide6 not available")
        return

    app = QApplication.instance() or QApplication(sys.argv)

    from statable.state_machine import StateMachine
    from statable.model import State
    from statable_gui.widgets import SettingsPanel
    from statable_gui.global_defs import GlobalDefinitions

    sm = StateMachine()
    sm.add_state(State(name="Idle",
                       entry=["Idle_Entry"],
                       exit=["Idle_Exit"]))
    sm.add_state(State(name="Active",
                       entry=["Active_Entry1", "Active_Entry2"]))

    panel = SettingsPanel(sm, global_defs=GlobalDefinitions())

    # The entry column (index 2) should display the joined list
    # e.g. "Idle_Entry" for single, "Active_Entry1; Active_Entry2" for multiple
    entry_cell_idle = panel.state_table.item(0, 2).text() if panel.state_table.item(0, 2) else ""
    exit_cell_idle = panel.state_table.item(0, 3).text() if panel.state_table.item(0, 3) else ""

    check("Idle entry displays single item",
          "Idle_Entry" in entry_cell_idle,
          f"got {entry_cell_idle!r}")
    check("Idle exit displays single item",
          "Idle_Exit" in exit_cell_idle,
          f"got {exit_cell_idle!r}")

    entry_cell_active = panel.state_table.item(1, 2).text() if panel.state_table.item(1, 2) else ""
    check("Active entry displays multiple items",
          "Active_Entry1" in entry_cell_active
          and "Active_Entry2" in entry_cell_active,
          f"got {entry_cell_active!r}")


# ======================================================================
# 10. TransitionListDialog Mode column
# ======================================================================
def test_transition_list_dialog_mode():
    print("\n[10] TransitionListDialog: Mode column")
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        RESULT.skip("TransitionListDialog Mode", "PySide6 not available")
        return

    app = QApplication.instance() or QApplication(sys.argv)

    from statable.state_machine import StateMachine
    from statable.model import State, Event, Transition
    from statable_gui.dialogs import TransitionListDialog
    from statable_gui.global_defs import GlobalDefinitions

    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))

    t1 = Transition(source="Idle", event="START", condition="cond_A",
                    target="Active", early_return=True, label="T1")
    t2 = Transition(source="Idle", event="START", condition="cond_B",
                    target="Active", early_return=False, label="T2")

    dlg = TransitionListDialog(
        state_names=["Idle", "Active"],
        event_name="START",
        existing_transitions=[t1, t2],
        global_defs=GlobalDefinitions(),
        state_machine=sm,
    )

    # Header should include a "Mode" column (or the equivalent)
    headers = [dlg.table.horizontalHeaderItem(i).text()
               for i in range(dlg.table.columnCount())]
    check("Mode column exists",
          any("Mode" in h for h in headers),
          f"headers={headers}")

    # Existing rows should preserve early_return
    row0 = dlg._row_to_transition(0)
    check("row0 early_return preserved",
          row0 is not None and row0.early_return is True,
          f"got {row0.early_return if row0 else None}")
    row1 = dlg._row_to_transition(1)
    check("row1 early_return preserved",
          row1 is not None and row1.early_return is False)


# ======================================================================
# 11. Full integration: XML -> SM -> display
# ======================================================================
def test_full_display_pipeline():
    print("\n[11] Full pipeline (XML -> SM -> mermaid)")
    import tempfile
    from statable.state_machine import StateMachine
    from statable.global_defs import GlobalDefinitions
    from statable.xml_io import project_to_xml, project_from_xml
    from statable.model import (
        State, Event, Transition, ActionStep, TransitionRelation,
    )
    from statable.mermaid_gen import generate_mermaid

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_state(State(name="Idle", exit=["Driver.IdleExit"]))
    sm.add_state(State(name="Active", entry=["Driver.ActiveEntry"]))
    sm.add_state(State(name="Error"))
    sm.add_event(Event(name="START"))
    sm.add_event(Event(name=""))
    sm.set_initial("Idle")

    sm.add_transition(Transition(
        source="Idle", event="START", condition="cond_A", target="Active",
        has_else=False, early_return=True, label="T1",
    ))
    sm.add_transition(Transition(
        source="Idle", event="START", condition="cond_B", target="Error",
        has_else=True, else_target="Idle", early_return=True, label="T2",
    ))

    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
        tmp = f.name

    try:
        gd = GlobalDefinitions()
        project_to_xml([("Driver", sm)], gd, tmp)

        tabs, gd2, _, _, _, _ = project_from_xml(tmp)
        sm2 = tabs[0][1]

        check("2 transitions loaded", len(sm2.transitions) == 2)

        mermaid = generate_mermaid(sm2)
        check_contains("edge Idle->Active", mermaid, "Idle --> Active")
        check_contains("edge Idle->Error", mermaid, "Idle --> Error")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2 P3 (Display layer) test suite")
    print("=" * 70)

    test_mermaid_multiple_targets()
    test_mermaid_else_target()
    test_mermaid_no_entry_exit()
    test_mermaid_backward_compat()

    test_truncate_text()
    test_build_transition_tooltip()
    test_event_header_label()

    test_matrix_cell_label_single()
    test_matrix_cell_label_multiple()

    test_settings_panel_entry_exit_list()
    test_transition_list_dialog_mode()

    test_full_display_pipeline()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()