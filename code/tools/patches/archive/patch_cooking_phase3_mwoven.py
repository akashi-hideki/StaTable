"""Phase 3: add MwOven tab (with convection)."""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
from _cooking_common import (load_or_create, save, add_var, add_rolefn,
                              add_tab)

OV_VARS = [
    ("oven_target_temp", "uint16_t", "degC", "Target oven temperature"),
    ("oven_current_temp", "uint16_t", "degC", "Current oven temperature"),
]

OV_ROLES = [
    ("StartOvenPid", "Start oven PID control"),
    ("StopOvenPid", "Stop oven PID control"),
    ("SetTopHeaterDuty", "Set top heater duty"),
    ("SetBottomHeaterDuty", "Set bottom heater duty"),
    ("SetBackHeaterDuty", "Set back heater duty"),
    ("SetConvectionFan", "Set convection fan duty"),
    ("ReadThermistors", "Read all thermistors"),
    ("CheckOvenOverheat", "Check oven overheat"),
    ("LogOvFault", "Log oven fault"),
    ("ClearOvFault", "Clear oven fault"),
]


def main() -> int:
    root = load_or_create()

    # --- GlobalDefinitions ---
    sv = root.find("GlobalDefinitions/SystemVariables")
    for name, typ, unit, desc in OV_VARS:
        add_var(sv, name, typ, unit, desc)

    # --- SharedLibraries ---
    rfl = root.find("SharedLibraries/RoleFunctionLibrary")
    for name, desc in OV_ROLES:
        add_rolefn(rfl, name, "MwOven", desc, desc)

    # --- Add MwOven tab ---
    tab = add_tab(root, "MwOven", "OvIdle", "3", "MwOven",
                  "Oven and grill heater layer")
    sm = tab.find("StateMachine")

    # States
    states = ET.SubElement(sm, "States")
    for sname, stype, sdesc in [
        ("OvIdle", "initial", "Oven idle"),
        ("PidHeating", "normal", "PID heating with convection"),
        ("OvError", "normal", "Oven error"),
    ]:
        ET.SubElement(states, "State", {"name": sname, "type": stype,
            "parent": "", "do": "", "description": sdesc})

    # Events
    events = ET.SubElement(sm, "Events")
    for eid, (ename, params, prio, edesc, dt) in enumerate([
        ("OV_START", "", "0", "Start oven", "direct"),
        ("OV_STOP", "", "0", "Stop oven", "direct"),
        ("OV_TEMP_REACHED", "", "0", "Target temperature reached", "direct"),
        ("OV_THERM_TICK", "", "0", "Thermistor update tick", "queue"),
        ("OV_OVERHEAT", "err_code", "9", "Oven overheat", "queue"),
        ("OV_CLEAR", "", "0", "Clear fault", "direct"),
    ], 1):
        ET.SubElement(events, "Event", {
            "name": ename, "id": str(eid), "kind": "signal", "params": params,
            "priority": prio, "description": edesc, "delivery_type": dt,
            "source_layer": "middleware",
            "data_type": "uint8_t" if params else "",
            "data_name": params, "title": edesc})

    # RoleFunctions (tab-local copy)
    rfs = ET.SubElement(sm, "RoleFunctions")
    for name, desc in OV_ROLES:
        add_rolefn(rfs, name, "MwOven", desc, desc)

    # Transitions
    trs = ET.SubElement(sm, "Transitions")
    rules = [
        ("OvIdle", "OV_START", "PidHeating", "Start PID heating"),
        ("PidHeating", "OV_STOP", "OvIdle", "Stop heating"),
        ("PidHeating", "OV_TEMP_REACHED", "PidHeating", "Maintain temperature"),
    ]
    for src, ev, tgt, title in rules:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": ev, "condition": "", "action": "",
            "target": tgt, "transition_type": "external", "title": title,
            "has_else": "false", "else_target": "",
            "early_return": "true", "label": "T1"})

    # Fault from any state
    for src in ["OvIdle", "PidHeating"]:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": "OV_OVERHEAT", "condition": "",
            "action": "", "target": "OvError", "transition_type": "external",
            "title": f"Overheat ({src})", "has_else": "false",
            "else_target": "", "early_return": "true", "label": "T1"})

    ET.SubElement(trs, "Transition", {
        "source": "OvError", "event": "OV_CLEAR", "condition": "",
        "action": "", "target": "OvIdle", "transition_type": "external",
        "title": "Clear fault", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})

    save(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())