#!/usr/bin/env python3
"""
P1 (Data layer) test suite for StaTable v2.2.

Verifies:
  1. State.entry / exit: List[str]
  2. Transition.early_return / label
  3. ActionStep / TransitionRelation classes
  4. StateMachine.cell_actions / cell_relations accessors
  5. XML round-trip (new format)
  6. Backward compatibility (old XML format)
  7. Sample data migration

Run:
  python tests/test_v2_2_p1.py
  pytest tests/test_v2_2_p1.py -v
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ======================================================================
# Simple test harness (works without pytest)
# ======================================================================
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


RESULT = TestResult()


def check(name, condition, msg=""):
    if condition:
        RESULT.ok(name)
    else:
        RESULT.fail(name, msg)
    return condition


# ======================================================================
# 1. Data model tests
# ======================================================================
def test_state_entry_exit_is_list():
    print("\n[1] State.entry / exit type")
    from statable.model import State

    s1 = State(name="Idle")
    check("default entry is list",
          isinstance(s1.entry, list), f"got {type(s1.entry)}")
    check("default exit is list",
          isinstance(s1.exit, list), f"got {type(s1.exit)}")
    check("default entry is empty", s1.entry == [])
    check("default exit is empty", s1.exit == [])

    s2 = State(name="Active", entry=["A", "B"], exit=["C"])
    check("entry stored as list", s2.entry == ["A", "B"])
    check("exit stored as list", s2.exit == ["C"])


def test_transition_early_return_and_label():
    print("\n[2] Transition.early_return / label")
    from statable.model import Transition

    t1 = Transition(source="A", event="E")
    check("default early_return is False",
          t1.early_return is False)
    check("default label is empty",
          t1.label == "")

    t2 = Transition(source="A", event="E",
                    early_return=True, label="T1")
    check("early_return stored", t2.early_return is True)
    check("label stored", t2.label == "T1")


def test_action_step():
    print("\n[3] ActionStep")
    from statable.model import ActionStep

    a1 = ActionStep()
    check("default role_function is empty",
          a1.role_function == "")
    check("default trigger is 'always'",
          a1.trigger == "always")

    a2 = ActionStep(role_function="Driver.PreCheck",
                    trigger="after_transitions")
    check("role_function stored",
          a2.role_function == "Driver.PreCheck")
    check("trigger stored",
          a2.trigger == "after_transitions")
    check("title auto-filled",
          a2.title == "Driver.PreCheck")


def test_transition_relation():
    print("\n[4] TransitionRelation")
    from statable.model import TransitionRelation

    r1 = TransitionRelation()
    check("default kind is 'sequential'",
          r1.kind == "sequential")
    check("default members empty", r1.members == [])
    check("default shared_condition empty",
          r1.shared_condition == "")

    r2 = TransitionRelation(
        kind="group",
        members=["T1", "T2"],
        shared_condition="cond_A",
    )
    check("kind stored", r2.kind == "group")
    check("members stored", r2.members == ["T1", "T2"])
    check("shared_condition stored",
          r2.shared_condition == "cond_A")


# ======================================================================
# 2. StateMachine cell_actions / cell_relations
# ======================================================================
def test_statemachine_cell_accessors():
    print("\n[5] StateMachine cell accessors")
    from statable.state_machine import StateMachine
    from statable.model import (
        State, Event, ActionStep, TransitionRelation,
    )

    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))

    # Initial state: empty
    check("initial cell_actions is empty dict",
          sm.cell_actions == {})
    check("initial cell_relations is empty dict",
          sm.cell_relations == {})

    # get on empty cell
    check("get_actions_for_cell returns []",
          sm.get_actions_for_cell("Idle", "START") == [])
    check("get_relations_for_cell returns []",
          sm.get_relations_for_cell("Idle", "START") == [])

    # set actions
    actions = [
        ActionStep(role_function="Driver.PreCheck", trigger="always"),
        ActionStep(role_function="Driver.Cleanup", trigger="after_transitions"),
    ]
    sm.set_actions_for_cell("Idle", "START", actions)
    got = sm.get_actions_for_cell("Idle", "START")
    check("actions stored and retrieved",
          len(got) == 2 and got[0].role_function == "Driver.PreCheck")

    # set relations
    rels = [
        TransitionRelation(kind="sequential", members=["T1", "T2"]),
        TransitionRelation(kind="group", members=["T1"],
                           shared_condition="cond_A"),
    ]
    sm.set_relations_for_cell("Idle", "START", rels)
    got_r = sm.get_relations_for_cell("Idle", "START")
    check("relations stored and retrieved",
          len(got_r) == 2 and got_r[1].kind == "group")

    # get_cell_keys
    keys = sm.get_cell_keys()
    check("get_cell_keys returns one key",
          keys == [("Idle", "START")])

    # clearing via set_* with []
    sm.set_actions_for_cell("Idle", "START", [])
    check("clearing actions removes key",
          sm.get_actions_for_cell("Idle", "START") == [])

    # remove_cell_metadata
    sm.set_relations_for_cell("Idle", "START", rels)
    sm.remove_cell_metadata("Idle", "START")
    check("remove_cell_metadata clears both",
          sm.get_actions_for_cell("Idle", "START") == []
          and sm.get_relations_for_cell("Idle", "START") == [])


def test_statemachine_remove_event_cleans_cells():
    print("\n[6] StateMachine.remove_event cleans cell metadata")
    from statable.state_machine import StateMachine
    from statable.model import (
        State, Event, ActionStep, TransitionRelation,
    )

    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_event(Event(name="START"))
    sm.add_event(Event(name="STOP"))

    sm.set_actions_for_cell("Idle", "START",
                             [ActionStep(role_function="X")])
    sm.set_actions_for_cell("Idle", "STOP",
                             [ActionStep(role_function="Y")])
    sm.set_relations_for_cell("Idle", "START",
                               [TransitionRelation(kind="sequential")])

    sm.remove_event("START")

    check("START cell_actions removed",
          sm.get_actions_for_cell("Idle", "START") == [])
    check("START cell_relations removed",
          sm.get_relations_for_cell("Idle", "START") == [])
    check("STOP cell_actions preserved",
          len(sm.get_actions_for_cell("Idle", "STOP")) == 1)


# ======================================================================
# 3. XML round-trip (new format)
# ======================================================================
def test_xml_roundtrip_new_format():
    print("\n[7] XML round-trip (new format)")
    from statable.state_machine import StateMachine
    from statable.xml_io import (
        state_machine_to_element, state_machine_from_element,
    )
    from statable.model import (
        State, Event, Transition, ActionStep, TransitionRelation,
    )

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.layer_priority = 3
    sm.add_state(State(name="Idle", entry=["EntryA", "EntryB"],
                       exit=["ExitA"]))
    sm.add_state(State(name="Active"))
    sm.set_initial("Idle")
    sm.add_event(Event(name="START"))

    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="cond_A", target="Active",
        has_else=True, else_target="Idle",
        early_return=True, label="T1",
        pre_actions=["Driver.Init"],
        else_actions=["Driver.Fallback"],
    ))
    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="cond_B", target="Idle",
        has_else=False,
        early_return=False, label="T2",
    ))

    sm.set_actions_for_cell("Idle", "START", [
        ActionStep(role_function="Driver.PreCheck", trigger="always"),
        ActionStep(role_function="Driver.Cleanup",
                   trigger="after_transitions"),
    ])
    sm.set_relations_for_cell("Idle", "START", [
        TransitionRelation(kind="sequential", members=["T1", "T2"]),
        TransitionRelation(kind="group", members=["T1"],
                           shared_condition="cond_common"),
    ])

    # Serialize + deserialize
    elem = state_machine_to_element(sm)
    sm2 = state_machine_from_element(elem)

    # Verify states
    idle = sm2.states.get("Idle")
    check("state entry round-trip",
          idle is not None and idle.entry == ["EntryA", "EntryB"],
          f"got {idle.entry if idle else 'None'}")
    check("state exit round-trip",
          idle is not None and idle.exit == ["ExitA"])

    # Verify transitions
    check("2 transitions loaded",
          len(sm2.transitions) == 2,
          f"got {len(sm2.transitions)}")

    t1 = next((t for t in sm2.transitions if t.label == "T1"), None)
    check("T1 found by label", t1 is not None)
    if t1:
        check("T1 early_return round-trip",
              t1.early_return is True)
        check("T1 else_target round-trip",
              t1.else_target == "Idle")
        check("T1 has_else round-trip",
              t1.has_else is True)
        check("T1 pre_actions round-trip",
              t1.pre_actions == ["Driver.Init"])
        check("T1 else_actions round-trip",
              t1.else_actions == ["Driver.Fallback"])

    t2 = next((t for t in sm2.transitions if t.label == "T2"), None)
    check("T2 found by label", t2 is not None)
    if t2:
        check("T2 early_return round-trip",
              t2.early_return is False)
        check("T2 has_else round-trip",
              t2.has_else is False)

    # Verify cell actions
    actions = sm2.get_actions_for_cell("Idle", "START")
    check("2 cell actions loaded",
          len(actions) == 2, f"got {len(actions)}")
    if len(actions) == 2:
        check("action[0] role_function",
              actions[0].role_function == "Driver.PreCheck")
        check("action[0] trigger",
              actions[0].trigger == "always")
        check("action[1] trigger",
              actions[1].trigger == "after_transitions")

    # Verify cell relations
    rels = sm2.get_relations_for_cell("Idle", "START")
    check("2 cell relations loaded",
          len(rels) == 2, f"got {len(rels)}")
    if len(rels) == 2:
        check("relation[0] kind",
              rels[0].kind == "sequential")
        check("relation[0] members",
              rels[0].members == ["T1", "T2"])
        check("relation[1] shared_condition",
              rels[1].shared_condition == "cond_common")


# ======================================================================
# 4. Backward compatibility (old XML)
# ======================================================================
def test_backward_compat_old_state_format():
    print("\n[8] Backward compat: old State entry/exit (str)")
    from statable.xml_io import state_machine_from_element

    old_xml = """<?xml version="1.0"?>
<StateMachine initial="Idle" layer_name="Driver">
  <States>
    <State name="Idle" type="normal" entry="Idle_entry" exit="Idle_exit" do="" description=""/>
    <State name="Active" type="normal" entry="" exit="" do="Active_do" description=""/>
  </States>
  <Events>
    <Event name="START" kind="signal" params="" priority="0" description=""
           delivery_type="direct" source_layer="driver" data_type="" data_name="" title=""/>
  </Events>
  <RoleFunctions/>
  <Transitions/>
</StateMachine>"""

    elem = ET.fromstring(old_xml)
    sm = state_machine_from_element(elem)

    idle = sm.states.get("Idle")
    check("old entry migrated to list",
          idle is not None and idle.entry == ["Idle_entry"],
          f"got {idle.entry if idle else 'None'}")
    check("old exit migrated to list",
          idle is not None and idle.exit == ["Idle_exit"])

    active = sm.states.get("Active")
    check("old empty entry -> []",
          active is not None and active.entry == [])


def test_backward_compat_no_early_return():
    print("\n[9] Backward compat: Transition without early_return")
    from statable.xml_io import state_machine_from_element

    old_xml = """<?xml version="1.0"?>
<StateMachine initial="Idle">
  <States>
    <State name="Idle" type="normal"/>
    <State name="Active" type="normal"/>
  </States>
  <Events>
    <Event name="START" kind="signal" params="" priority="0" description=""
           delivery_type="direct" source_layer="driver" data_type="" data_name="" title=""/>
  </Events>
  <RoleFunctions/>
  <Transitions>
    <Transition source="Idle" event="START" condition=""
                action="" target="Active" transition_type="external"
                title="Test" has_else="true" else_target="Idle"/>
  </Transitions>
</StateMachine>"""

    elem = ET.fromstring(old_xml)
    sm = state_machine_from_element(elem)

    t = sm.transitions[0] if sm.transitions else None
    check("transition loaded", t is not None)
    if t:
        check("early_return defaults to False",
              t.early_return is False)
        check("label defaults to empty",
              t.label == "")


def test_backward_compat_no_cells():
    print("\n[10] Backward compat: no <Cells> element")
    from statable.xml_io import state_machine_from_element

    old_xml = """<?xml version="1.0"?>
<StateMachine initial="Idle">
  <States>
    <State name="Idle" type="normal"/>
  </States>
  <Events/>
  <RoleFunctions/>
  <Transitions/>
</StateMachine>"""

    elem = ET.fromstring(old_xml)
    sm = state_machine_from_element(elem)

    check("no cells -> empty cell_actions",
          sm.cell_actions == {})
    check("no cells -> empty cell_relations",
          sm.cell_relations == {})
    check("get_cell_keys empty",
          sm.get_cell_keys() == [])


# ======================================================================
# 5. Full project round-trip (file I/O)
# ======================================================================
def test_full_project_roundtrip():
    print("\n[11] Full project save/load (temp file)")
    from statable.state_machine import StateMachine
    from statable.global_defs import GlobalDefinitions
    from statable.xml_io import project_to_xml, project_from_xml
    from statable.model import (
        State, Event, Transition, ActionStep, TransitionRelation,
    )

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.layer_priority = 2
    sm.add_state(State(name="Idle", entry=["E1"], exit=["X1"]))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.set_initial("Idle")

    sm.add_transition(Transition(
        source="Idle", event="START",
        condition="cA", target="Active",
        early_return=True, label="T1",
    ))

    sm.set_actions_for_cell("Idle", "START",
        [ActionStep(role_function="Driver.Pre", trigger="always")])
    sm.set_relations_for_cell("Idle", "START",
        [TransitionRelation(kind="group", members=["T1"],
                            shared_condition="cX")])

    gd = GlobalDefinitions()

    with tempfile.NamedTemporaryFile(
            mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
        tmp_path = f.name

    try:
        project_to_xml([("Driver", sm)], gd, tmp_path,
                       project_settings={"project_name": "TestProj"})

        check("XML file created", os.path.exists(tmp_path))

        # File content sanity check
        with open(tmp_path, encoding='utf-8') as f:
            content = f.read()
        check("XML has <Entry>", "<Entry>" in content)
        check("XML has early_return attr",
              'early_return="true"' in content)
        check("XML has label attr", 'label="T1"' in content)
        check("XML has <Cells>", "<Cells>" in content)

        # Load
        tabs, gd2, rl, cl, ll, ps = project_from_xml(tmp_path)

        check("one tab loaded", len(tabs) == 1)
        name, sm2 = tabs[0]
        check("tab name preserved", name == "Driver")
        check("layer_name preserved",
              sm2.layer_name == "Driver")
        check("layer_priority preserved",
              sm2.layer_priority == 2)

        t = sm2.transitions[0] if sm2.transitions else None
        check("transition loaded", t is not None)
        if t:
            check("early_return preserved",
                  t.early_return is True)
            check("label preserved", t.label == "T1")

        actions = sm2.get_actions_for_cell("Idle", "START")
        check("cell actions preserved",
              len(actions) == 1
              and actions[0].role_function == "Driver.Pre")

        rels = sm2.get_relations_for_cell("Idle", "START")
        check("cell relations preserved",
              len(rels) == 1
              and rels[0].shared_condition == "cX")

        check("project_settings preserved",
              ps.get('project_name') == "TestProj")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ======================================================================
# 6. Sample data
# ======================================================================
def test_sample_data_loads():
    print("\n[12] Sample data loads without error")
    from statable.sample_data import (
        create_sample_state_machine, create_sample_global_defs,
    )

    try:
        sm = create_sample_state_machine()
        check("sample state machine created",
              sm is not None and len(sm.states) > 0)
        check("sample states have list entry",
              all(isinstance(s.entry, list) for s in sm.states.values()))
        check("sample states have list exit",
              all(isinstance(s.exit, list) for s in sm.states.values()))
    except Exception as e:
        check("sample state machine loads", False, f"{type(e).__name__}: {e}")

    try:
        gd = create_sample_global_defs()
        check("sample global defs created",
              gd is not None and len(gd.variables) > 0)
    except Exception as e:
        check("sample global defs loads", False, f"{type(e).__name__}: {e}")


# ======================================================================
# 7. Simulate realistic P4 workflow
# ======================================================================
def test_realistic_cell_workflow():
    print("\n[13] Realistic cell workflow (Idle+START with 2 transitions)")
    from statable.state_machine import StateMachine
    from statable.model import (
        State, Event, Transition, ActionStep, TransitionRelation,
    )

    sm = StateMachine()
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_state(State(name="Error"))
    sm.add_event(Event(name="START"))

    # T1 (Commit): cond_A -> Active
    t1 = Transition(source="Idle", event="START",
                    condition="cond_A", target="Active",
                    has_else=False, early_return=True, label="T1")
    # T2 (Commit with else): cond_B -> Active / else -> Error
    t2 = Transition(source="Idle", event="START",
                    condition="cond_B", target="Active",
                    has_else=True, else_target="Error",
                    early_return=True, label="T2")

    sm.add_transition(t1)
    sm.add_transition(t2)

    sm.set_actions_for_cell("Idle", "START", [
        ActionStep(role_function="Driver.PreCheck", trigger="always"),
        ActionStep(role_function="Driver.Log", trigger="after_transitions"),
    ])
    sm.set_relations_for_cell("Idle", "START", [
        TransitionRelation(kind="sequential", members=["T1", "T2"]),
    ])

    cell = sm.get_transitions_for_cell("Idle", "START")
    check("2 transitions in cell", len(cell) == 2)
    check("T1 order first", cell[0].label == "T1")
    check("T2 else_target set", cell[1].else_target == "Error")

    actions = sm.get_actions_for_cell("Idle", "START")
    check("2 actions in cell", len(actions) == 2)

    rels = sm.get_relations_for_cell("Idle", "START")
    check("1 relation in cell", len(rels) == 1)


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable v2.2 P1 (Data layer) test suite")
    print("=" * 70)

    test_state_entry_exit_is_list()
    test_transition_early_return_and_label()
    test_action_step()
    test_transition_relation()

    test_statemachine_cell_accessors()
    test_statemachine_remove_event_cleans_cells()

    test_xml_roundtrip_new_format()
    test_backward_compat_old_state_format()
    test_backward_compat_no_early_return()
    test_backward_compat_no_cells()

    test_full_project_roundtrip()
    test_sample_data_loads()
    test_realistic_cell_workflow()

    ok = RESULT.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()