#!/usr/bin/env python3
"""
P4-B (Overview tab: reachability / coverage analysis) test suite for StaTable v2.2.

Verifies:
  1. CoverageAnalyzer.analyze_cell      (cell-internal analysis)
  2. CoverageAnalyzer.analyze_state_graph (state graph analysis)
  3. OverviewTab API
  4. ActionEditorDialog 5-tab structure
  5. Full integration: XML -> SM -> analyze -> report

Run:
  python tests/test_v2_2_p4b.py
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


def qapp():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return None
    return QApplication.instance() or QApplication(sys.argv)


# ======================================================================
# Helpers
# ======================================================================
def make_sm(transitions, states=None, events=None, layer="Driver"):
    from statable.state_machine import StateMachine
    from statable.model import State, Event

    sm = StateMachine()
    sm.layer_name = layer

    all_states = set(states or [])
    all_events = set(events or [])
    for t in transitions:
        all_states.add(t.source)
        if t.target:
            all_states.add(t.target)
        if t.else_target:
            all_states.add(t.else_target)
        all_events.add(t.event)

    for s in sorted(all_states):
        sm.add_state(State(name=s))
    for e in sorted(all_events):
        sm.add_event(Event(name=e))
    for t in transitions:
        sm.add_transition(t)
    return sm


# ======================================================================
# 1. CoverageAnalyzer.analyze_cell
# ======================================================================
def test_analyze_cell_basic():
    print("\n[1] CoverageAnalyzer.analyze_cell (basic)")
    try:
        from statable_gui.transition_editor_direct.coverage_analyzer import (
            CoverageAnalyzer,
        )
        from statable.model import Transition
    except ImportError as e:
        RESULT.fail("import CoverageAnalyzer", str(e))
        return

    t1 = Transition(source="Idle", event="START", condition="cond_A",
                    target="Active", early_return=True, label="T1")
    t2 = Transition(source="Idle", event="START", condition="cond_B",
                    target="Error", early_return=False, label="T2")
    sm = make_sm([t1, t2])

    analyzer = CoverageAnalyzer()
    report = analyzer.analyze_cell(sm, "Idle", "START")

    check("report has transitions_count",
          hasattr(report, "transitions_count")
          and report.transitions_count == 2,
          f"got {getattr(report, 'transitions_count', None)}")
    check("report has unreachable_labels",
          hasattr(report, "unreachable_labels"))
    check("report has duplicate_targets",
          hasattr(report, "duplicate_targets"))
    check("report has overlap_pairs",
          hasattr(report, "overlap_pairs"))
    check("no duplicate targets (Active vs Error)",
          report.duplicate_targets == [],
          f"got {report.duplicate_targets}")


def test_analyze_cell_unreachable():
    print("\n[1b] analyze_cell: unreachable after Commit")
    from statable_gui.transition_editor_direct.coverage_analyzer import (
        CoverageAnalyzer,
    )
    from statable.model import Transition

    # All Commit -> T2 unreachable
    t1 = Transition(source="Idle", event="START", condition="",
                    target="Active", has_else=True, else_target="Error",
                    early_return=True, label="T1")
    t2 = Transition(source="Idle", event="START", condition="cond_B",
                    target="Idle", early_return=True, label="T2")
    sm = make_sm([t1, t2])

    analyzer = CoverageAnalyzer()
    report = analyzer.analyze_cell(sm, "Idle", "START")

    check("T2 flagged as unreachable",
          "T2" in report.unreachable_labels,
          f"got {report.unreachable_labels}")


def test_analyze_cell_duplicate_target():
    print("\n[1c] analyze_cell: duplicate targets")
    from statable_gui.transition_editor_direct.coverage_analyzer import (
        CoverageAnalyzer,
    )
    from statable.model import Transition

    t1 = Transition(source="Idle", event="START", condition="cond_A",
                    target="Active", early_return=True, label="T1")
    t2 = Transition(source="Idle", event="START", condition="cond_B",
                    target="Active", early_return=True, label="T2")
    sm = make_sm([t1, t2])

    analyzer = CoverageAnalyzer()
    report = analyzer.analyze_cell(sm, "Idle", "START")

    check("duplicate target 'Active' detected",
          "Active" in report.duplicate_targets,
          f"got {report.duplicate_targets}")
    if "Active" in report.duplicate_targets:
        labels = report.duplicate_targets["Active"]
        check("Active targeted by T1 and T2",
              set(labels) == {"T1", "T2"},
              f"got {labels}")


# ======================================================================
# 2. CoverageAnalyzer.analyze_state_graph
# ======================================================================
def test_analyze_state_graph_basic():
    print("\n[2] CoverageAnalyzer.analyze_state_graph (basic)")
    from statable_gui.transition_editor_direct.coverage_analyzer import (
        CoverageAnalyzer,
    )
    from statable.model import Transition

    t1 = Transition(source="Idle", event="START", condition="",
                    target="Active", early_return=True, label="T1")
    t2 = Transition(source="Active", event="STOP", condition="",
                    target="Idle", early_return=True, label="T2")
    sm = make_sm([t1, t2], states=["Idle", "Active"])
    sm.set_initial("Idle")

    analyzer = CoverageAnalyzer()
    report = analyzer.analyze_state_graph(sm)

    check("report has unreachable_states",
          hasattr(report, "unreachable_states"))
    check("report has terminal_states",
          hasattr(report, "terminal_states"))
    check("report has self_loops",
          hasattr(report, "self_loops"))
    check("all states reachable",
          report.unreachable_states == [],
          f"got {report.unreachable_states}")
    check("no terminal states",
          report.terminal_states == [],
          f"got {report.terminal_states}")


def test_analyze_state_graph_unreachable():
    print("\n[2b] analyze_state_graph: unreachable state")
    from statable_gui.transition_editor_direct.coverage_analyzer import (
        CoverageAnalyzer,
    )
    from statable.model import Transition

    t1 = Transition(source="Idle", event="START", condition="",
                    target="Active", early_return=True, label="T1")
    sm = make_sm([t1], states=["Idle", "Active", "Orphan"])
    sm.set_initial("Idle")

    analyzer = CoverageAnalyzer()
    report = analyzer.analyze_state_graph(sm)

    check("'Orphan' flagged as unreachable",
          "Orphan" in report.unreachable_states,
          f"got {report.unreachable_states}")


def test_analyze_state_graph_terminal():
    print("\n[2c] analyze_state_graph: terminal state")
    from statable_gui.transition_editor_direct.coverage_analyzer import (
        CoverageAnalyzer,
    )
    from statable.model import Transition

    t1 = Transition(source="Idle", event="START", condition="",
                    target="Active", early_return=True, label="T1")
    sm = make_sm([t1], states=["Idle", "Active"])
    sm.set_initial("Idle")

    analyzer = CoverageAnalyzer()
    report = analyzer.analyze_state_graph(sm)

    check("'Active' flagged as terminal",
          "Active" in report.terminal_states,
          f"got {report.terminal_states}")


def test_analyze_state_graph_self_loop():
    print("\n[2d] analyze_state_graph: self loop")
    from statable_gui.transition_editor_direct.coverage_analyzer import (
        CoverageAnalyzer,
    )
    from statable.model import Transition

    t1 = Transition(source="Idle", event="TICK", condition="",
                    target="Idle", early_return=False, label="T1")
    sm = make_sm([t1], states=["Idle"])
    sm.set_initial("Idle")

    analyzer = CoverageAnalyzer()
    report = analyzer.analyze_state_graph(sm)

    check("self-loop detected",
          len(report.self_loops) == 1,
          f"got {report.self_loops}")
    if report.self_loops:
        check("self-loop tuple",
              report.self_loops[0] == ("Idle", "TICK"),
              f"got {report.self_loops[0]}")


# ======================================================================
# 3. OverviewTab
# ======================================================================
def test_overview_tab():
    print("\n[3] OverviewTab")
    app = qapp()
    if app is None:
        RESULT.skip("OverviewTab", "PySide6 not available")
        return

    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.overview_tab import (
            OverviewTab,
        )
    except ImportError as e:
        RESULT.fail("import OverviewTab", str(e))
        return

    draft = ActionDraft(source="Idle", event="START")
    tab = OverviewTab(draft)

    check("has refresh()", hasattr(tab, "refresh"))
    check("has get_summary_text()",
          hasattr(tab, "get_summary_text"))

    text = tab.get_summary_text()
    check("summary is str", isinstance(text, str))
def test_dialog_five_tabs():
    print("\n[4] ActionEditorDialog: 5 tabs")
    app = qapp()
    if app is None:
        RESULT.skip("ActionEditorDialog 5 tabs", "PySide6")
        return

    try:
        from statable_gui.transition_editor_direct.draft import ActionDraft
        from statable_gui.transition_editor_direct.dialog import (
            ActionEditorDialog,
        )
    except ImportError as e:
        RESULT.fail("import", str(e))
        return

    draft = ActionDraft(source="Idle", event="START", layer_name="Driver")
    dlg = ActionEditorDialog(
        draft,
        role_functions=["Driver.PreCheck"],
        states=["Idle", "Active"],
    )

    names = dlg.get_tab_names()
    check("has 5 tabs", len(names) == 5, f"got {names}")
    check("tab 0 is Transitions", names[0] == "Transitions", f"{names}")
    check("tab 1 is Pre / Post Actions",
          names[1] == "Pre / Post Actions", f"{names}")
    check("tab 2 is Relations", names[2] == "Relations", f"{names}")
    check("tab 3 is Overview", names[3] == "Overview", f"{names}")
    check("tab 4 is Preview", names[4] == "Preview", f"{names}")


# ======================================================================
# 5. Full integration
# ======================================================================
def test_full_integration():
    print("\n[5] Full integration: SM -> analyze -> report")
    from statable_gui.transition_editor_direct.coverage_analyzer import (
        CoverageAnalyzer,
    )
    from statable.model import Transition

    # Realistic scenario: Idle --START--> Active, Active --STOP--> Idle
    # + Idle --START--> Error (with else)
    t1 = Transition(source="Idle", event="START", condition="cond_A",
                    target="Active", has_else=False,
                    early_return=True, label="T1")
    t2 = Transition(source="Idle", event="START", condition="cond_B",
                    target="Error", has_else=True, else_target="Idle",
                    early_return=True, label="T2")
    t3 = Transition(source="Active", event="STOP", condition="",
                    target="Idle", early_return=True, label="T3")

    sm = make_sm([t1, t2, t3], states=["Idle", "Active", "Error"])
    sm.set_initial("Idle")

    analyzer = CoverageAnalyzer()

    cell_report = analyzer.analyze_cell(sm, "Idle", "START")
    check("cell: 2 transitions", cell_report.transitions_count == 2)
    check("cell: no duplicate targets", cell_report.duplicate_targets == [])

    graph_report = analyzer.analyze_state_graph(sm)
    check("graph: all reachable",
          graph_report.unreachable_states == [],
          f"got {graph_report.unreachable_states}")
    check("graph: 'Error' is terminal",
          "Error" in graph_report.terminal_states,
          f"got {graph_report.terminal_states}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2 P4-B (Overview) test suite")
    print("=" * 70)

    test_analyze_cell_basic()
    test_analyze_cell_unreachable()
    test_analyze_cell_duplicate_target()

    test_analyze_state_graph_basic()
    test_analyze_state_graph_unreachable()
    test_analyze_state_graph_terminal()
    test_analyze_state_graph_self_loop()

    test_overview_tab()
    test_dialog_five_tabs()
    test_full_integration()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()