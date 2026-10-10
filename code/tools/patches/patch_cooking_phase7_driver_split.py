"""Phase 7: split Driver into DriverInput / DriverOutput.

Content:
  1. Remove old Driver tab
  2. Rename  thermistor_back  -> thermistor_middle
             heater_back_duty -> heater_middle_duty
  3. Add DriverInput vars / RoleFunctions / Tab (5 states, 6 roles)
  4. Add DriverOutput vars / RoleFunctions / Tab (6 states, 13 roles)
  5. Extend MwMicrowave (+1 state: Preheating)
  6. Extend MwSteam     (+2 states: PumpOn / PumpOff)
  7. Reorder tabs: DriverInput, DriverOutput, MwMicrowave, MwOven,
                   MwGrill, MwSteam, Application
"""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
from _cooking_common import (
    load_or_create, save, add_var, remove_var, add_rolefn,
    remove_rolefn_by_ns, add_tab, remove_tab, reorder_tabs,
)

# ==================================================================
# DriverInput definition
# ==================================================================
INPUT_VARS = [
    # (name, type, unit, desc)  -- add_var skips if already present
    ("ir_value",          "uint16_t", "ADC",  "IR sensor moving average"),
    ("steam_sensor",      "uint16_t", "ADC",  "Steam sensor"),
    ("thermistor_top",    "uint16_t", "degC", "Top thermistor"),
    ("thermistor_middle", "uint16_t", "degC", "Middle thermistor"),      # renamed
    ("thermistor_bottom", "uint16_t", "degC", "Bottom thermistor"),
    ("humidity",          "uint8_t",  "%",    "Humidity"),
    ("door_open",         "uint8_t",  "",     "Door open flag"),
    ("zc_count",          "uint32_t", "count","Zero-cross count"),
    ("rx_buf",            "uint8_t",  "",     "UART RX buffer"),
]

INPUT_ROLES = [
    ("ReadSensorsMovingAvg", "Read sensors with moving average"),
    ("EmitIrReady",          "Emit IR_READY event"),
    ("EmitSteamReady",       "Emit STEAM_READY event"),
    ("EmitThermReady",       "Emit THERM_READY event"),
    ("ReceiveCommand",       "Receive command from panel"),
    ("OnDoorOpen",           "Safety: door open immediate stop"),
]

INPUT_STATES = [
    ("InIdle",     "initial", "Waiting for input events"),
    ("InSensing",  "normal",  "ADC reading + moving average"),
    ("InTxRx",     "normal",  "Zero-cross sync UART RX"),
    ("InDoorOpen", "normal",  "Door open (safety)"),
    ("InError",    "normal",  "Input error"),
]

INPUT_EVENTS = [
    # (name, params, prio, desc, delivery)
    ("SENSOR_TICK", "",         "0", "Periodic sensor tick",       "queue"),
    ("ADC_DONE",    "",         "0", "ADC conversion complete",    "direct"),
    ("ZC_PULSE",    "",         "9", "AC zero-cross pulse",        "direct"),
    ("RX_DONE",     "",         "0", "UART RX complete",           "direct"),
    ("RX_TIMEOUT",  "",         "5", "UART RX timeout",            "direct"),
    ("DOOR_OPEN",   "",         "9", "Door opened (safety)",       "direct"),
    ("DOOR_CLOSE",  "",         "9", "Door closed",                "direct"),
    ("HW_FAULT",    "err_code", "9", "Hardware fault",             "queue"),
    ("CLEAR_FAULT", "",         "0", "Clear fault",                "direct"),
]

# ==================================================================
# DriverOutput definition (PWM version: 6 states / 13 roles)
# ==================================================================
OUTPUT_VARS = [
    ("heater_top_on",      "uint8_t",  "",  "Top heater ON flag"),
    ("heater_middle_on",   "uint8_t",  "",  "Middle heater ON flag"),
    ("heater_bottom_on",   "uint8_t",  "",  "Bottom heater ON flag"),
    ("heater_top_duty",    "uint8_t",  "%", "Top heater PWM duty"),
    ("heater_middle_duty", "uint8_t",  "%", "Middle heater PWM duty"),    # renamed
    ("heater_bottom_duty", "uint8_t",  "%", "Bottom heater PWM duty"),
    ("fan_on",             "uint8_t",  "",  "Fan ON flag"),
    ("fan_duty",           "uint8_t",  "%", "Fan PWM duty"),
    ("pump_on",            "uint8_t",  "",  "Pump ON flag"),
    ("mag_on",             "uint8_t",  "",  "Magnetron ON flag"),
    ("mw_power",           "uint16_t", "W", "Magnetron power"),
    ("mw_anode_current",   "uint16_t", "mA","Anode current"),
]

OUTPUT_ROLES = [
    # Heater
    ("SetHeaterOn",        "Set heaters ON (full power)"),
    ("SetHeaterOff",       "Set heaters OFF"),
    ("SetHeaterPwm",       "Set heater PWM duty"),
    # Fan
    ("SetFanOn",           "Set fan ON"),
    ("SetFanOff",          "Set fan OFF"),
    ("SetFanPwm",          "Set fan PWM duty"),
    # Pump
    ("SetPumpOn",          "Set pump ON"),
    ("SetPumpOff",         "Set pump OFF"),
    # Magnetron
    ("SetMagOn",           "Set magnetron ON (full power)"),
    ("SetMagOff",          "Set magnetron OFF"),
    ("SetMagPwm",          "Set magnetron PWM power"),
    # Comm / Monitor
    ("SendStatusMaster",   "Send status to panel"),
    ("CheckAnodeCurrent",  "Check magnetron anode current"),
]

OUTPUT_STATES = [
    ("OutIdle",     "initial", "All outputs OFF"),
    ("OutHeating",  "normal",  "Heater output active"),
    ("OutFanPump",  "normal",  "Fan / pump active"),
    ("OutMag",      "normal",  "Magnetron active"),
    ("OutTx",       "normal",  "UART TX active"),
    ("OutError",    "normal",  "Output error"),
]

OUTPUT_EVENTS = [
    ("HEAT_START",     "",         "0", "Start heater",            "direct"),
    ("HEAT_STOP",      "",         "0", "Stop heater",             "direct"),
    ("FAN_PUMP_START", "",         "0", "Start fan / pump",        "direct"),
    ("FAN_PUMP_STOP",  "",         "0", "Stop fan / pump",         "direct"),
    ("MAG_START",      "",         "0", "Start magnetron",         "direct"),
    ("MAG_STOP",       "",         "0", "Stop magnetron",          "direct"),
    ("ZC_TX_START",    "",         "9", "Zero-cross TX start",     "direct"),
    ("TX_DONE",        "",         "0", "UART TX complete",        "direct"),
    ("TX_TIMEOUT",     "",         "5", "UART TX timeout",         "direct"),
    ("HW_FAULT",       "err_code", "9", "Hardware fault",          "queue"),
    ("CLEAR_FAULT",    "",         "0", "Clear fault",             "direct"),
]


# ==================================================================
# Helpers
# ==================================================================
def _fill_states(sm: ET.Element, states) -> None:
    el = ET.SubElement(sm, "States")
    for name, typ, desc in states:
        ET.SubElement(el, "State", {
            "name": name, "type": typ, "parent": "",
            "do": "", "description": desc})


def _fill_events(sm: ET.Element, events, source_layer: str) -> None:
    el = ET.SubElement(sm, "Events")
    for eid, (name, params, prio, desc, dt) in enumerate(events, 1):
        ET.SubElement(el, "Event", {
            "name": name, "id": str(eid), "kind": "signal",
            "params": params, "priority": prio, "description": desc,
            "delivery_type": dt, "source_layer": source_layer,
            "data_type": "uint8_t" if params else "",
            "data_name": params, "title": desc})


def _fill_roles(sm: ET.Element, roles, ns: str) -> None:
    el = ET.SubElement(sm, "RoleFunctions")
    for name, desc in roles:
        add_rolefn(el, name, ns, desc, desc)


def _fill_transitions(sm: ET.Element, rules, fault_sources) -> None:
    el = ET.SubElement(sm, "Transitions")
    for src, ev, tgt, title in rules:
        ET.SubElement(el, "Transition", {
            "source": src, "event": ev, "condition": "", "action": "",
            "target": tgt, "transition_type": "external", "title": title,
            "has_else": "false", "else_target": "",
            "early_return": "true", "label": "T1"})
    for src in fault_sources:
        ET.SubElement(el, "Transition", {
            "source": src, "event": "HW_FAULT", "condition": "", "action": "",
            "target": "ErrorTargetPlaceholder" if False else
                      el.get("_err", "") or "ErrorTargetPlaceholder",
            "transition_type": "external",
            "title": f"Fault ({src})", "has_else": "false",
            "else_target": "", "early_return": "true", "label": "T1"})


# ==================================================================
# Main
# ==================================================================
def main() -> int:
    root = load_or_create()

    # ---------------- 1. Remove old Driver tab ----------------
    remove_tab(root, "Driver")

    # ---------------- 2. Rename back -> middle ----------------
    sv = root.find("GlobalDefinitions/SystemVariables")
    if sv is None:
        print("[ERR] GlobalDefinitions/SystemVariables not found")
        return 1
    remove_var(sv, "thermistor_back")
    remove_var(sv, "heater_back_duty")

    # ---------------- 3. Extend GlobalDefinitions ----------------
    for name, typ, unit, desc in INPUT_VARS:
        add_var(sv, name, typ, unit, desc)
    for name, typ, unit, desc in OUTPUT_VARS:
        add_var(sv, name, typ, unit, desc)

    # ---------------- 4. Extend SharedLibraries ----------------
    rfl = root.find("SharedLibraries/RoleFunctionLibrary")
    if rfl is None:
        print("[ERR] SharedLibraries/RoleFunctionLibrary not found")
        return 1
    remove_rolefn_by_ns(rfl, "Driver")
    for name, desc in INPUT_ROLES:
        add_rolefn(rfl, name, "DriverInput", desc, desc)
    for name, desc in OUTPUT_ROLES:
        add_rolefn(rfl, name, "DriverOutput", desc, desc)

    # ---------------- 5. Create DriverInput tab ----------------
    tab = add_tab(root, "DriverInput", "InIdle", "1",
                  "DriverInput", "Input devices layer")
    sm = tab.find("StateMachine")

    _fill_states(sm, INPUT_STATES)
    _fill_events(sm, INPUT_EVENTS, source_layer="driver")
    _fill_roles(sm, INPUT_ROLES, ns="DriverInput")

    trs = ET.SubElement(sm, "Transitions")
    input_rules = [
        ("InIdle",     "SENSOR_TICK", "InSensing",  "Sensor tick"),
        ("InSensing",  "ADC_DONE",    "InIdle",     "Sensing done"),
        ("InIdle",     "ZC_PULSE",    "InTxRx",     "ZC: start RX"),
        ("InTxRx",     "RX_DONE",     "InIdle",     "RX done"),
        ("InTxRx",     "RX_TIMEOUT",  "InError",    "RX timeout"),
        ("InIdle",     "DOOR_OPEN",   "InDoorOpen", "Door open"),
        ("InDoorOpen", "DOOR_CLOSE",  "InIdle",     "Door closed"),
    ]
    for src, ev, tgt, title in input_rules:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": ev, "condition": "", "action": "",
            "target": tgt, "transition_type": "external", "title": title,
            "has_else": "false", "else_target": "",
            "early_return": "true", "label": "T1"})
    for src in ["InIdle", "InSensing", "InTxRx", "InDoorOpen"]:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": "HW_FAULT", "condition": "",
            "action": "", "target": "InError",
            "transition_type": "external",
            "title": f"Fault ({src})", "has_else": "false",
            "else_target": "", "early_return": "true", "label": "T1"})
    ET.SubElement(trs, "Transition", {
        "source": "InError", "event": "CLEAR_FAULT", "condition": "",
        "action": "", "target": "InIdle", "transition_type": "external",
        "title": "Clear fault", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})

    # ---------------- 6. Create DriverOutput tab ----------------
    tab = add_tab(root, "DriverOutput", "OutIdle", "1",
                  "DriverOutput", "Output devices layer")
    sm = tab.find("StateMachine")

    _fill_states(sm, OUTPUT_STATES)
    _fill_events(sm, OUTPUT_EVENTS, source_layer="driver")
    _fill_roles(sm, OUTPUT_ROLES, ns="DriverOutput")

    trs = ET.SubElement(sm, "Transitions")
    output_rules = [
        ("OutIdle",    "HEAT_START",     "OutHeating", "Start heating"),
        ("OutHeating", "HEAT_STOP",      "OutIdle",    "Stop heating"),
        ("OutIdle",    "FAN_PUMP_START", "OutFanPump", "Start fan/pump"),
        ("OutFanPump", "FAN_PUMP_STOP",  "OutIdle",    "Stop fan/pump"),
        ("OutIdle",    "MAG_START",      "OutMag",     "Start magnetron"),
        ("OutMag",     "MAG_STOP",       "OutIdle",    "Stop magnetron"),
        ("OutIdle",    "ZC_TX_START",    "OutTx",      "ZC: start TX"),
        ("OutTx",      "TX_DONE",        "OutIdle",    "TX done"),
        ("OutTx",      "TX_TIMEOUT",     "OutError",   "TX timeout"),
    ]
    for src, ev, tgt, title in output_rules:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": ev, "condition": "", "action": "",
            "target": tgt, "transition_type": "external", "title": title,
            "has_else": "false", "else_target": "",
            "early_return": "true", "label": "T1"})
    for src in ["OutIdle", "OutHeating", "OutFanPump", "OutMag", "OutTx"]:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": "HW_FAULT", "condition": "",
            "action": "", "target": "OutError",
            "transition_type": "external",
            "title": f"Fault ({src})", "has_else": "false",
            "else_target": "", "early_return": "true", "label": "T1"})
    ET.SubElement(trs, "Transition", {
        "source": "OutError", "event": "CLEAR_FAULT", "condition": "",
        "action": "", "target": "OutIdle", "transition_type": "external",
        "title": "Clear fault", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})

    # ---------------- 7. MwMicrowave: +1 state (Preheating) ----------------
    _add_state(root, "MwMicrowave",
               ("Preheating", "normal", "Magnetron preheat / soft-start"))
    _add_transition(root, "MwMicrowave",
                    src="MwIdle", ev="MW_START", tgt="Preheating",
                    title="Start preheat")
    _add_transition(root, "MwMicrowave",
                    src="Preheating", ev="MW_ANODE_OK", tgt="Heating",
                    title="Preheat done: heating")
    _add_transition(root, "MwMicrowave",
                    src="Preheating", ev="MW_STOP", tgt="MwIdle",
                    title="Stop preheat")
    for ev in ("MW_ANODE_FAULT", "MW_OVERHEAT"):
        _add_transition(root, "MwMicrowave",
                        src="Preheating", ev=ev, tgt="MwError",
                        title=f"{ev} (Preheating)")

    # ---------------- 8. MwSteam: +2 states (PumpOn / PumpOff) ----------------
    _add_state(root, "MwSteam",
               ("PumpOn",  "normal", "Boiler pump pulse ON"))
    _add_state(root, "MwSteam",
               ("PumpOff", "normal", "Boiler pump pulse OFF"))
    # Replace self-loop  Steaming --ST_PUMP_TICK--> Steaming
    _remove_transition(root, "MwSteam",
                       src="Steaming", ev="ST_PUMP_TICK")
    _add_transition(root, "MwSteam",
                    src="Steaming", ev="ST_PUMP_TICK", tgt="PumpOn",
                    title="Pump pulse ON")
    _add_transition(root, "MwSteam",
                    src="PumpOn", ev="ST_PUMP_TICK", tgt="PumpOff",
                    title="Pump pulse OFF")
    _add_transition(root, "MwSteam",
                    src="PumpOff", ev="ST_PUMP_TICK", tgt="PumpOn",
                    title="Pump pulse ON")
    for src in ("PumpOn", "PumpOff"):
        _add_transition(root, "MwSteam",
                        src=src, ev="ST_STOP", tgt="StIdle",
                        title="Stop steam")
        _add_transition(root, "MwSteam",
                        src=src, ev="ST_OVERHEAT", tgt="StError",
                        title=f"Overheat ({src})")

    # ---------------- 9. Reorder tabs ----------------
    reorder_tabs(root, [
        "DriverInput", "DriverOutput",
        "MwMicrowave", "MwOven", "MwGrill", "MwSteam",
        "Application",
    ])

    save(root)
    return 0


# ==================================================================
# XML micro-helpers (state / transition manipulation)
# ==================================================================
def _add_state(root: ET.Element, tab_name: str,
               state_spec: tuple) -> None:
    tab = _find_tab(root, tab_name)
    if tab is None:
        print(f"[WARN] tab not found: {tab_name}")
        return
    states = tab.find("StateMachine/States")
    if states is None:
        print(f"[WARN] States not found in {tab_name}")
        return
    name = state_spec[0]
    for s in states.findall("State"):
        if s.get("name") == name:
            print(f"[SKIP] state exists: {tab_name}.{name}")
            return
    ET.SubElement(states, "State", {
        "name": name, "type": state_spec[1], "parent": "",
        "do": "", "description": state_spec[2]})
    print(f"[ADD]  state: {tab_name}.{name}")


def _add_transition(root: ET.Element, tab_name: str,
                    src: str, ev: str, tgt: str, title: str) -> None:
    tab = _find_tab(root, tab_name)
    if tab is None:
        print(f"[WARN] tab not found: {tab_name}")
        return
    trs = tab.find("StateMachine/Transitions")
    if trs is None:
        print(f"[WARN] Transitions not found in {tab_name}")
        return
    for t in trs.findall("Transition"):
        if t.get("source") == src and t.get("event") == ev:
            t.set("target", tgt)
            t.set("title", title)
            print(f"[MOD]  transition: {tab_name} {src}--{ev}-->{tgt}")
            return
    ET.SubElement(trs, "Transition", {
        "source": src, "event": ev, "condition": "", "action": "",
        "target": tgt, "transition_type": "external", "title": title,
        "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})
    print(f"[ADD]  transition: {tab_name} {src}--{ev}-->{tgt}")


def _remove_transition(root: ET.Element, tab_name: str,
                       src: str, ev: str) -> bool:
    tab = _find_tab(root, tab_name)
    if tab is None:
        return False
    trs = tab.find("StateMachine/Transitions")
    if trs is None:
        return False
    for t in list(trs.findall("Transition")):
        if t.get("source") == src and t.get("event") == ev:
            trs.remove(t)
            print(f"[DEL]  transition: {tab_name} {src}--{ev}")
            return True
    return False


def _find_tab(root: ET.Element, name: str) -> ET.Element | None:
    for t in root.findall("Tab"):
        if t.get("name") == name:
            return t
    return None


if __name__ == "__main__":
    sys.exit(main())