"""Phase 1: add Driver tab."""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
from _cooking_common import (load_or_create, save, add_var, add_rolefn,
                              add_tab)

DRIVER_VARS = [
    ("zc_count", "uint32_t", "count", "Zero-cross count"),
    ("seq_step", "uint8_t", "", "Current sequence step"),
    ("seq_total", "uint8_t", "", "Total sequence steps"),
    ("ir_value", "uint16_t", "ADC", "IR sensor moving average"),
    ("steam_sensor", "uint16_t", "ADC", "Steam sensor (vacuum-therm diff)"),
    ("thermistor_top", "uint16_t", "degC", "Top thermistor"),
    ("thermistor_bottom", "uint16_t", "degC", "Bottom thermistor"),
    ("thermistor_back", "uint16_t", "degC", "Back thermistor"),
    ("humidity", "uint8_t", "%", "Humidity"),
    ("heater_top_duty", "uint8_t", "%", "Top heater PWM duty"),
    ("heater_bottom_duty", "uint8_t", "%", "Bottom heater PWM duty"),
    ("heater_back_duty", "uint8_t", "%", "Back heater PWM duty"),
    ("fan_duty", "uint8_t", "%", "Convection fan duty"),
    ("mw_power", "uint16_t", "W", "Microwave power"),
    ("mw_anode_current", "uint16_t", "mA", "Magnetron anode current"),
    ("boiler_temp", "uint16_t", "degC", "Steam boiler temperature"),
    ("pump_pulse_count", "uint8_t", "", "Boiler pump pulse count"),
]

DRIVER_ROLES = [
    ("ReadSensorsMovingAvg", "Read sensors and update moving averages"),
    ("EmitIrReady", "Emit IR_READY event"),
    ("EmitSteamReady", "Emit STEAM_READY event"),
    ("EmitThermReady", "Emit THERM_READY event"),
    ("SendStatusMaster", "Send status to panel (master mode)"),
    ("ReceiveCommand", "Receive command from panel"),
    ("SetHeaterPwm", "Set heater PWM duty"),
    ("SetConvectionFan", "Set convection fan duty"),
    ("SetMagnetronPower", "Set magnetron power"),
    ("PulseBoilerPump", "Pulse boiler pump"),
    ("CheckAnodeCurrent", "Check magnetron anode current"),
    ("LogHwFault", "Log hardware fault"),
    ("ClearHwFault", "Clear hardware fault"),
]


def main() -> int:
    root = load_or_create()

    # --- GlobalDefinitions: add driver variables ---
    sv = root.find("GlobalDefinitions/SystemVariables")
    for name, typ, unit, desc in DRIVER_VARS:
        add_var(sv, name, typ, unit, desc)

    # --- SharedLibraries: add driver role functions ---
    rfl = root.find("SharedLibraries/RoleFunctionLibrary")
    for name, desc in DRIVER_ROLES:
        add_rolefn(rfl, name, "Driver", desc, desc)

    # --- Add Driver tab ---
    tab = add_tab(root, "Driver", "HwIdle", "1", "Driver",
                  "Hardware driver layer")
    sm = tab.find("StateMachine")

    states = ET.SubElement(sm, "States")
    for sname, stype, sdesc in [
        ("HwIdle", "initial", "Waiting for HW event"),
        ("HwTxStatus", "normal", "Master TX to panel"),
        ("HwRxCommand", "normal", "Receiving command"),
        ("HwSensing", "normal", "Sensing + moving average"),
        ("HwHeating", "normal", "Heating output"),
        ("HwError", "normal", "Hardware error"),
    ]:
        ET.SubElement(states, "State", {"name": sname, "type": stype,
            "parent": "", "do": "", "description": sdesc})

    events = ET.SubElement(sm, "Events")
    for eid, (ename, params, prio, edesc, dt) in enumerate([
        ("ZC_PULSE", "", "9", "AC zero-cross pulse", "direct"),
        ("TX_DONE", "", "0", "Master TX done", "direct"),
        ("RX_DONE", "", "0", "RX complete", "direct"),
        ("SENSOR_TICK", "", "0", "Periodic sensor tick", "queue"),
        ("HEAT_START", "", "0", "Start heating", "direct"),
        ("HEAT_STOP", "", "0", "Stop heating", "direct"),
        ("HW_FAULT", "err_code", "9", "Hardware fault", "queue"),
        ("CLEAR_FAULT", "", "0", "Clear fault", "direct"),
    ], 1):
        ET.SubElement(events, "Event", {
            "name": ename, "id": str(eid), "kind": "signal", "params": params,
            "priority": prio, "description": edesc, "delivery_type": dt,
            "source_layer": "driver",
            "data_type": "uint8_t" if params else "",
            "data_name": params, "title": edesc})

    rfs = ET.SubElement(sm, "RoleFunctions")
    for name, desc in DRIVER_ROLES:
        add_rolefn(rfs, name, "Driver", desc, desc)

    trs = ET.SubElement(sm, "Transitions")
    rules = [
        ("HwIdle", "ZC_PULSE", "HwTxStatus", "Zero-cross: start TX"),
        ("HwTxStatus", "TX_DONE", "HwRxCommand", "TX done: await RX"),
        ("HwRxCommand", "RX_DONE", "HwIdle", "RX done: idle"),
        ("HwIdle", "SENSOR_TICK", "HwSensing", "Sensor tick"),
        ("HwSensing", "TX_DONE", "HwIdle", "Sensing done"),
        ("HwIdle", "HEAT_START", "HwHeating", "Start heating"),
        ("HwHeating", "HEAT_STOP", "HwIdle", "Stop heating"),
    ]
    for src, ev, tgt, title in rules:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": ev, "condition": "", "action": "",
            "target": tgt, "transition_type": "external", "title": title,
            "has_else": "false", "else_target": "",
            "early_return": "true", "label": "T1"})

    for src in ["HwIdle", "HwTxStatus", "HwRxCommand", "HwSensing", "HwHeating"]:
        ET.SubElement(trs, "Transition", {
            "source": src, "event": "HW_FAULT", "condition": "", "action": "",
            "target": "HwError", "transition_type": "external",
            "title": f"Fault ({src})", "has_else": "false", "else_target": "",
            "early_return": "true", "label": "T1"})

    ET.SubElement(trs, "Transition", {
        "source": "HwError", "event": "CLEAR_FAULT", "condition": "",
        "action": "", "target": "HwIdle", "transition_type": "external",
        "title": "Clear fault", "has_else": "false", "else_target": "",
        "early_return": "true", "label": "T1"})

    save(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())