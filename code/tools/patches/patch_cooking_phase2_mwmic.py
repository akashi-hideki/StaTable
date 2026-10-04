"""Phase 2: add MwMicrowave tab."""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
from _cooking_common import (load_or_create, save, add_var, add_rolefn,
                              add_tab)

MW_VARS = [
    ("mw_target_power", "uint16_t", "W", "Target microwave power"),
]

MW_ROLES = [
    ("StartMagnetron", "Start magnetron with soft-start"),
    ("StopMagnetron", "Stop magnetron"),
    ("SetMwPower", "Set microwave power level"),
    ("CheckAnodeCurrent", "Monitor anode current"),
    ("LogMwFault", "Log microwave fault"),
    ("ClearMwFault", "Clear microwave fault"),
]


def main() -> int:
    root = load_or_create()

    # --- GlobalDefinitions ---
    sv = root.find("GlobalDefinitions/SystemVariables")
    for name, typ, unit, desc in MW_VARS:
        add_var(sv, name, typ, unit, desc)

    # --- SharedLibraries ---
    rfl = root.find("SharedLibraries/RoleFunctionLibrary")
    for name, desc in MW_ROLES:
        add_rolefn(rfl, name, "MwMicrowave", desc, desc)

    # --- Add MwMicrowave tab ---
    tab = add_tab(root, "MwMicrowave", "MwIdle", "3", "MwMicrowave",
                  "Microwave heating layer")
    sm = tab.find("StateMachine")

    # States
    states = ET.SubElement(sm, "States")
    for sname, stype, sdesc in [
        ("MwIdle", "initial", "Microwave idle"),
        ("Heating", "normal", "Magnetron heating"),
        ("MwError", "normal", "Microwave error"),
    ]:
        ET.SubElement(states, "State", {"name": sname, "type": stype,
            "parent": "", "do": "", "description": sdesc})

    # Events
    events = ET.SubElement(sm, "Events")
    for eid, (ename, params, prio, edesc, dt) in enumerate([
        ("MW_START", "", "0", "Start microwave", "direct"),
        ("MW_STOP", "", "0", "Stop microwave", "direct"),
        ("MW_ANODE_OK", "", "0", "Anode current OK", "direct"),
        ("MW_ANODE_FAULT", "err_code", "9", "Anode current fault", "queue"),
        ("MW_OVERHEAT", "err_code", "9", "Overheat detected", "queue"),
        ("MW_CLEAR", "", "0", "Clear fault", "direct"),
    ], 1):
        ET.SubElement(events, "Event", {
            "name": ename, "id": str(eid), "kind": "signal", "params": params,
            "priority": prio, "description": edesc, "delivery_type": dt,
            "source_layer": "middleware",
            "data_type": "uint8_t" if params else "",
            "data_name": params, "title": edesc})

    # RoleFunctions (tab-local copy)
    rfs = ET.SubElement(sm, "RoleFunctions")
    for name, desc in MW_ROLES:
        add_rolefn(rfs, name, "MwMicrowave", desc, desc)

    # Transitions
    trs = ET.SubElement(sm, "Transitions")
    rules = [
        ("MwIdle", "MW_START", "Heating", "Start heating"),
        ("Heating", "MW_STOP", "MwIdle", "Stop heating"),
    ]
    for src, ev, tgt, title in rules:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": ev, "condition": "", "action": "",
            "target": tgt, "transition_type": "external", "title": title,
            "has_else": "false", "else_target": "",
            "early_return": "true", "label": "T1"})

    # Fault from any state
    for src in ["MwIdle", "Heating"]:
        for ev, title in [("MW_ANODE_FAULT", "Anode fault"),
                          ("MW_OVERHEAT", "Overheat")]:
            ET.SubElement(trs, "Transition", {
                "source": src, "event": ev, "condition": "", "action": "",
                "target": "MwError", "transition_type": "external",
                "title": f"{title} ({src})", "has_else": "false",
                "else_target": "", "early_return": "true", "label": "T1"})

    ET.SubElement(trs, "Transition", {
        "source": "MwError", "event": "MW_CLEAR", "condition": "",
        "action": "", "target": "MwIdle", "transition_type": "external",
        "title": "Clear fault", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})

    save(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())