"""Phase 6: add Application tab (final layer)."""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
from _cooking_common import (load_or_create, save, add_var, add_rolefn,
                              add_tab)

APP_VARS = [
    ("stage_elapsed", "uint32_t", "ms", "Elapsed time in current stage"),
    ("stage_duration", "uint32_t", "ms", "Duration of current stage"),
    ("stage_mode", "uint8_t", "", "Current stage heating mode"),
]

APP_ROLES = [
    ("ReceiveSequence", "Receive sequence from panel"),
    ("ParseSequence", "Parse sequence data"),
    ("StartStage", "Start current stage"),
    ("StopStage", "Stop current stage"),
    ("CheckStageDone", "Check if stage complete"),
    ("NextStage", "Advance to next stage"),
    ("ReportStatus", "Report status to panel"),
    ("ReportComplete", "Report completion"),
    ("LogAppError", "Log application error"),
    ("ClearAppError", "Clear application error"),
]


def main() -> int:
    root = load_or_create()

    # --- GlobalDefinitions ---
    sv = root.find("GlobalDefinitions/SystemVariables")
    for name, typ, unit, desc in APP_VARS:
        add_var(sv, name, typ, unit, desc)

    # --- SharedLibraries ---
    rfl = root.find("SharedLibraries/RoleFunctionLibrary")
    for name, desc in APP_ROLES:
        add_rolefn(rfl, name, "Application", desc, desc)

    # --- Add Application tab ---
    tab = add_tab(root, "Application", "Idle", "5", "Application",
                  "Cooking sequence application layer")
    sm = tab.find("StateMachine")

    # States
    states = ET.SubElement(sm, "States")
    for sname, stype, sdesc in [
        ("Idle", "initial", "Waiting for sequence from panel"),
        ("Executing", "normal", "Executing current stage"),
        ("StepTransition", "normal", "Transitioning between stages"),
        ("Completed", "normal", "Sequence complete"),
        ("Error", "final", "Fatal error"),
    ]:
        ET.SubElement(states, "State", {"name": sname, "type": stype,
            "parent": "", "do": "", "description": sdesc})

    # Events  ★ source_layer="middleware" (valid value)
    events = ET.SubElement(sm, "Events")
    for eid, (ename, params, prio, edesc, dt) in enumerate([
        ("SEQ_RECEIVED", "", "0", "Sequence received", "direct"),
        ("STAGE_START", "", "0", "Start current stage", "direct"),
        ("STAGE_DONE", "", "0", "Stage completed", "direct"),
        ("NEXT_STEP", "", "0", "Advance to next step", "direct"),
        ("ALL_DONE", "", "0", "All stages complete", "direct"),
        ("CANCEL", "", "1", "Cancel sequence", "direct"),
        ("APP_FAULT", "err_code", "9", "Application fault", "queue"),
        ("RESET", "", "0", "Reset", "direct"),
    ], 1):
        ET.SubElement(events, "Event", {
            "name": ename, "id": str(eid), "kind": "signal", "params": params,
            "priority": prio, "description": edesc, "delivery_type": dt,
            "source_layer": "middleware",
            "data_type": "uint8_t" if params else "",
            "data_name": params, "title": edesc})

    # RoleFunctions (tab-local copy)
    rfs = ET.SubElement(sm, "RoleFunctions")
    for name, desc in APP_ROLES:
        add_rolefn(rfs, name, "Application", desc, desc)

    # Transitions
    trs = ET.SubElement(sm, "Transitions")
    rules = [
        ("Idle", "SEQ_RECEIVED", "Executing", "Start sequence"),
        ("Executing", "STAGE_DONE", "StepTransition", "Stage completed"),
        ("StepTransition", "NEXT_STEP", "Executing", "Next stage"),
        ("StepTransition", "ALL_DONE", "Completed", "All stages done"),
        ("Completed", "RESET", "Idle", "Reset to idle"),
        ("Executing", "CANCEL", "Idle", "Cancel sequence"),
        ("StepTransition", "CANCEL", "Idle", "Cancel (between stages)"),
        ("Idle", "STAGE_START", "Executing", "Direct stage start"),
    ]
    for src, ev, tgt, title in rules:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": ev, "condition": "", "action": "",
            "target": tgt, "transition_type": "external", "title": title,
            "has_else": "false", "else_target": "",
            "early_return": "true", "label": "T1"})

    for src in ["Idle", "Executing", "StepTransition", "Completed"]:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": "APP_FAULT", "condition": "", "action": "",
            "target": "Error", "transition_type": "external",
            "title": f"Fault ({src})", "has_else": "false",
            "else_target": "", "early_return": "true", "label": "T1"})

    ET.SubElement(trs, "Transition", {
        "source": "Error", "event": "RESET", "condition": "",
        "action": "", "target": "Idle", "transition_type": "external",
        "title": "Maintenance reset", "has_else": "false",
        "else_target": "", "early_return": "true", "label": "T1"})

    save(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())