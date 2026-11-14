"""Phase 4: add MwGrill tab."""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
from _cooking_common import (load_or_create, save, add_var, add_rolefn,
                              add_tab)

GR_ROLES = [
    ("StartGrill", "Start grill heater"),
    ("StopGrill", "Stop grill heater"),
    ("SetGrillDuty", "Set grill heater duty"),
    ("CheckGrillOverheat", "Check grill overheat"),
    ("LogGrFault", "Log grill fault"),
    ("ClearGrFault", "Clear grill fault"),
]


def main() -> int:
    root = load_or_create()

    # --- SharedLibraries ---
    rfl = root.find("SharedLibraries/RoleFunctionLibrary")
    for name, desc in GR_ROLES:
        add_rolefn(rfl, name, "MwGrill", desc, desc)

    # --- Add MwGrill tab ---
    tab = add_tab(root, "MwGrill", "GrIdle", "3", "MwGrill",
                  "Grill heater layer")
    sm = tab.find("StateMachine")

    # States
    states = ET.SubElement(sm, "States")
    for sname, stype, sdesc in [
        ("GrIdle", "initial", "Grill idle"),
        ("Grilling", "normal", "Grill heating"),
        ("GrError", "normal", "Grill error"),
    ]:
        ET.SubElement(states, "State", {"name": sname, "type": stype,
            "parent": "", "do": "", "description": sdesc})

    # Events
    events = ET.SubElement(sm, "Events")
    for eid, (ename, params, prio, edesc, dt) in enumerate([
        ("GR_START", "", "0", "Start grill", "direct"),
        ("GR_STOP", "", "0", "Stop grill", "direct"),
        ("GR_OVERHEAT", "err_code", "9", "Grill overheat", "queue"),
        ("GR_CLEAR", "", "0", "Clear fault", "direct"),
    ], 1):
        ET.SubElement(events, "Event", {
            "name": ename, "id": str(eid), "kind": "signal", "params": params,
            "priority": prio, "description": edesc, "delivery_type": dt,
            "source_layer": "middleware",
            "data_type": "uint8_t" if params else "",
            "data_name": params, "title": edesc})

    # RoleFunctions (tab-local copy)
    rfs = ET.SubElement(sm, "RoleFunctions")
    for name, desc in GR_ROLES:
        add_rolefn(rfs, name, "MwGrill", desc, desc)

    # Transitions
    trs = ET.SubElement(sm, "Transitions")
    ET.SubElement(trs, "Transition", {
        "source": "GrIdle", "event": "GR_START", "condition": "", "action": "",
        "target": "Grilling", "transition_type": "external",
        "title": "Start grill", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})
    ET.SubElement(trs, "Transition", {
        "source": "Grilling", "event": "GR_STOP", "condition": "", "action": "",
        "target": "GrIdle", "transition_type": "external",
        "title": "Stop grill", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})

    for src in ["GrIdle", "Grilling"]:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": "GR_OVERHEAT", "condition": "", "action": "",
            "target": "GrError", "transition_type": "external",
            "title": f"Overheat ({src})", "has_else": "false",
            "else_target": "", "early_return": "true", "label": "T1"})

    ET.SubElement(trs, "Transition", {
        "source": "GrError", "event": "GR_CLEAR", "condition": "",
        "action": "", "target": "GrIdle", "transition_type": "external",
        "title": "Clear fault", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})

    save(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())