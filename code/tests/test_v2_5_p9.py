#!/usr/bin/env python3
"""StaTable C-51 Step 2 test suite: Event.trigger (free-text) field.

Verifies:
  - Event.trigger default is ""
  - XML write: trigger emitted only when non-empty
  - XML read: trigger preserved / missing -> ""
  - Backward compat: pre-C-51 XML round-trips identically
  - GUI: EventEditDialog has trigger_edit
  - GUI: kind=change disables trigger_edit
  - GUI: get_event() returns trigger for signal / call / time
  - GUI: get_event() returns "" for change

Run:
  python tests/test_v2_5_p9.py
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
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
# [1] Event.trigger field exists with default ""
# ======================================================================
def test_event_field():
    print("\n[1] Event.trigger field")

    from statable.model import Event, EventKind

    e = Event(name="X")
    check("default trigger is ''", e.trigger == "", f"got {e.trigger!r}")

    e2 = Event(name="Y", trigger="GPIO edge (ISR), debounce 5ms")
    check("trigger stored", e2.trigger == "GPIO edge (ISR), debounce 5ms")


# ======================================================================
# [2] XML write: trigger emitted when non-empty
# ======================================================================
def test_xml_write_nonempty():
    print("\n[2] XML write (trigger non-empty)")

    from statable.model import Event, EventKind, EventDeliveryType, EventSourceLayer
    from statable.state_machine import StateMachine
    from statable.xml_io import state_machine_to_element

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_event(Event(
        name="COIN_SENSOR", id=1, kind=EventKind.SIGNAL,
        trigger="GPIO edge (ISR), debounce 5ms",
    ))

    elem = state_machine_to_element(sm)
    events = elem.find("Events")
    check("<Events> present", events is not None)

    event_elems = events.findall("Event")
    check("1 event emitted", len(event_elems) == 1)
    if event_elems:
        e = event_elems[0]
        check("trigger attr present",
              e.get("trigger") == "GPIO edge (ISR), debounce 5ms",
              f"got {e.get('trigger')!r}")


# ======================================================================
# [3] XML write: trigger NOT emitted when empty (backward compat)
# ======================================================================
def test_xml_write_empty():
    print("\n[3] XML write (trigger empty -> not emitted)")

    from statable.model import Event, EventKind
    from statable.state_machine import StateMachine
    from statable.xml_io import state_machine_to_element

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_event(Event(name="COIN_SENSOR", id=1, kind=EventKind.SIGNAL))

    elem = state_machine_to_element(sm)
    events = elem.find("Events")
    event_elems = events.findall("Event")
    check("1 event emitted", len(event_elems) == 1)
    if event_elems:
        e = event_elems[0]
        check("trigger attr absent (backward compat)",
              "trigger" not in e.attrib,
              f"attribs: {list(e.attrib.keys())}")


# ======================================================================
# [4] XML read: trigger preserved
# ======================================================================
def test_xml_read_present():
    print("\n[4] XML read (trigger present)")

    from statable.xml_io import state_machine_from_element

    xml_str = """
    <StateMachine initial="Idle" layer_priority="5"
                  layer_description="" layer_name="Driver">
        <States>
            <State name="Idle" type="normal" parent="" do=""
                   description=""/>
        </States>
        <Events>
            <Event name="COIN_SENSOR" id="1" kind="signal"
                   params="" priority="0" description=""
                   delivery_type="direct" source_layer="driver"
                   data_type="" data_name="" title="Coin sensor"
                   trigger="GPIO edge (ISR), debounce 5ms"/>
        </Events>
        <RoleFunctions/>
        <Transitions/>
    </StateMachine>
    """
    elem = ET.fromstring(xml_str)
    sm = state_machine_from_element(elem)
    check("event loaded", "COIN_SENSOR" in sm.events)
    if "COIN_SENSOR" in sm.events:
        check("trigger preserved",
              sm.events["COIN_SENSOR"].trigger
                  == "GPIO edge (ISR), debounce 5ms",
              f"got {sm.events['COIN_SENSOR'].trigger!r}")


# ======================================================================
# [5] XML read: missing trigger -> ""
# ======================================================================
def test_xml_read_missing():
    print("\n[5] XML read (trigger missing -> '')")

    from statable.xml_io import state_machine_from_element

    xml_str = """
    <StateMachine initial="Idle" layer_priority="5"
                  layer_description="" layer_name="Driver">
        <States>
            <State name="Idle" type="normal" parent="" do=""
                   description=""/>
        </States>
        <Events>
            <Event name="COIN_SENSOR" id="1" kind="signal"
                   params="" priority="0" description=""
                   delivery_type="direct" source_layer="driver"
                   data_type="" data_name="" title="Coin sensor"/>
        </Events>
        <RoleFunctions/>
        <Transitions/>
    </StateMachine>
    """
    elem = ET.fromstring(xml_str)
    sm = state_machine_from_element(elem)
    check("event loaded", "COIN_SENSOR" in sm.events)
    if "COIN_SENSOR" in sm.events:
        check("trigger defaults to ''",
              sm.events["COIN_SENSOR"].trigger == "",
              f"got {sm.events['COIN_SENSOR'].trigger!r}")


# ======================================================================
# [6] GUI: EventEditDialog has trigger_edit
# ======================================================================
def test_dialog_widget():
    print("\n[6] EventEditDialog has trigger_edit")

    from statable_gui.event_definition_dialog import EventEditDialog

    dlg = EventEditDialog()
    check("trigger_edit exists", hasattr(dlg, "trigger_edit"))
    check("trigger_edit enabled by default (signal)",
          dlg.trigger_edit.isEnabled())


# ======================================================================
# [7] GUI: kind=change disables trigger_edit
# ======================================================================
def test_dialog_kind_change():
    print("\n[7] EventEditDialog: kind=change disables trigger_edit")

    from statable_gui.event_definition_dialog import EventEditDialog
    from statable.model import EventKind

    dlg = EventEditDialog()
    idx = dlg.kind_combo.findData(EventKind.CHANGE)
    if idx < 0:
        R.fail("CHANGE in kind_combo", "not found")
        return
    dlg.kind_combo.setCurrentIndex(idx)
    check("trigger_edit disabled for change",
          not dlg.trigger_edit.isEnabled())


# ======================================================================
# [8] GUI: get_event() returns trigger for signal
# ======================================================================
def test_dialog_get_event_signal():
    print("\n[8] EventEditDialog.get_event() with trigger (signal)")

    from statable_gui.event_definition_dialog import EventEditDialog
    from statable.model import EventKind

    dlg = EventEditDialog()
    dlg.name_edit.setText("COIN_SENSOR")
    idx = dlg.kind_combo.findData(EventKind.SIGNAL)
    dlg.kind_combo.setCurrentIndex(idx)
    dlg.trigger_edit.setText("GPIO edge (ISR), debounce 5ms")

    ev = dlg.get_event()
    check("trigger stored in Event",
          ev.trigger == "GPIO edge (ISR), debounce 5ms",
          f"got {ev.trigger!r}")


# ======================================================================
# [9] GUI: get_event() returns "" for change
# ======================================================================
def test_dialog_get_event_change():
    print("\n[9] EventEditDialog.get_event() with change -> trigger ''")

    from statable_gui.event_definition_dialog import EventEditDialog
    from statable.model import EventKind

    dlg = EventEditDialog()
    dlg.name_edit.setText("VAR_CHANGED")
    idx = dlg.kind_combo.findData(EventKind.CHANGE)
    dlg.kind_combo.setCurrentIndex(idx)
    # User might still type something, but it should be ignored
    dlg.trigger_edit.setText("should be ignored")

    ev = dlg.get_event()
    check("trigger is '' for change",
          ev.trigger == "",
          f"got {ev.trigger!r}")


# ======================================================================
# [10] Full round-trip with multiple kinds
# ======================================================================
def test_round_trip_full():
    print("\n[10] Full XML round-trip (multiple kinds)")

    from statable.model import (
        Event, EventKind, EventDeliveryType, EventSourceLayer)
    from statable.state_machine import StateMachine
    from statable.xml_io import (
        state_machine_to_element, state_machine_from_element)

    sm = StateMachine()
    sm.layer_name = "Driver"
    sm.add_event(Event(
        name="EV_EDGE", id=1, kind=EventKind.SIGNAL,
        trigger="GPIO edge (ISR), debounce 5ms",
    ))
    sm.add_event(Event(
        name="EV_CALL", id=2, kind=EventKind.CALL,
        trigger="direct call from Application",
    ))
    sm.add_event(Event(
        name="EV_TIME", id=3, kind=EventKind.TIME,
        trigger="periodic timer (10ms)",
    ))

    elem = state_machine_to_element(sm)
    sm2 = state_machine_from_element(elem)

    check("3 events after round-trip", len(sm2.events) == 3)
    for name, trig in (
        ("EV_EDGE", "GPIO edge (ISR), debounce 5ms"),
        ("EV_CALL", "direct call from Application"),
        ("EV_TIME", "periodic timer (10ms)"),
    ):
        e = sm2.events.get(name)
        check(f"{name}: trigger preserved",
              e is not None and e.trigger == trig,
              f"got {getattr(e, 'trigger', None)!r}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable C-51 Step 2 (Event.trigger free-text field)")
    print("=" * 70)

    from PySide6.QtWidgets import QApplication
    _ = QApplication.instance() or QApplication(sys.argv)

    test_event_field()
    test_xml_write_nonempty()
    test_xml_write_empty()
    test_xml_read_present()
    test_xml_read_missing()
    test_dialog_widget()
    test_dialog_kind_change()
    test_dialog_get_event_signal()
    test_dialog_get_event_change()
    test_round_trip_full()

    ok = R.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()