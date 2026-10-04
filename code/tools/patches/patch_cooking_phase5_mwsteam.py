"""Phase 5: add MwSteam tab (with pulse boiler control)."""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
from _cooking_common import (load_or_create, save, add_var, add_rolefn,
                              add_tab)

ST_VARS = [
    ("steam_target_temp", "uint16_t", "degC", "Target steam temperature"),
]

ST_ROLES = [
    ("StartBoilerHeater", "Start boiler heater"),
    ("StopBoilerHeater", "Stop boiler heater"),
    ("PulsePump", "Pulse boiler pump"),
    ("SetPumpDuty", "Set pump duty cycle"),
    ("ReadBoilerTemp", "Read boiler temperature"),
    ("CalculateSteamPID", "Compute steam PID output"),
    ("CheckSteamOverheat", "Check steam overheat"),
    ("LogStFault", "Log steam fault"),
    ("ClearStFault", "Clear steam fault"),
]


def main() -> int:
    root = load_or_create()

    # --- GlobalDefinitions ---
    sv = root.find("GlobalDefinitions/SystemVariables")
    for name, typ, unit, desc in ST_VARS:
        add_var(sv, name, typ, unit, desc)

    # --- SharedLibraries ---
    rfl = root.find("SharedLibraries/RoleFunctionLibrary")
    for name, desc in ST_ROLES:
        add_rolefn(rfl, name, "MwSteam", desc, desc)

    # --- Add MwSteam tab ---
    tab = add_tab(root, "MwSteam", "StIdle", "3", "MwSteam",
                  "Steam generation layer")
    sm = tab.find("StateMachine")

    # States
    states = ET.SubElement(sm, "States")
    for sname, stype, sdesc in [
        ("StIdle", "initial", "Steam generator idle"),
        ("Steaming", "normal", "Steam generation active"),
        ("StError", "normal", "Steam error"),
    ]:
        ET.SubElement(states, "State", {"name": sname, "type": stype,
            "parent": "", "do": "", "description": sdesc})

    # Events
    events = ET.SubElement(sm, "Events")
    for eid, (ename, params, prio, edesc, dt) in enumerate([
        ("ST_START", "", "0", "Start steam", "direct"),
        ("ST_STOP", "", "0", "Stop steam", "direct"),
        ("ST_BOILER_READY", "", "0", "Boiler at temperature", "direct"),
        ("ST_PUMP_TICK", "", "0", "Pump pulse tick", "queue"),
        ("ST_OVERHEAT", "err_code", "9", "Boiler overheat", "queue"),
        ("ST_CLEAR", "", "0", "Clear fault", "direct"),
    ], 1):
        ET.SubElement(events, "Event", {
            "name": ename, "id": str(eid), "kind": "signal", "params": params,
            "priority": prio, "description": edesc, "delivery_type": dt,
            "source_layer": "middleware",
            "data_type": "uint8_t" if params else "",
            "data_name": params, "title": edesc})

    # RoleFunctions (tab-local copy)
    rfs = ET.SubElement(sm, "RoleFunctions")
    for name, desc in ST_ROLES:
        add_rolefn(rfs, name, "MwSteam", desc, desc)

    # Transitions
    trs = ET.SubElement(sm, "Transitions")
    ET.SubElement(trs, "Transition", {
        "source": "StIdle", "event": "ST_START", "condition": "", "action": "",
        "target": "Steaming", "transition_type": "external",
        "title": "Start steam", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})
    ET.SubElement(trs, "Transition", {
        "source": "Steaming", "event": "ST_STOP", "condition": "", "action": "",
        "target": "StIdle", "transition_type": "external",
        "title": "Stop steam", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})
    ET.SubElement(trs, "Transition", {
        "source": "Steaming", "event": "ST_PUMP_TICK", "condition": "",
        "action": "", "target": "Steaming", "transition_type": "external",
        "title": "Pulse pump", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})

    for src in ["StIdle", "Steaming"]:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": "ST_OVERHEAT", "condition": "", "action": "",
            "target": "StError", "transition_type": "external",
            "title": f"Overheat ({src})", "has_else": "false",
            "else_target": "", "early_return": "true", "label": "T1"})

    ET.SubElement(trs, "Transition", {
        "source": "StError", "event": "ST_CLEAR", "condition": "",
        "action": "", "target": "StIdle", "transition_type": "external",
        "title": "Clear fault", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})

    save(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())