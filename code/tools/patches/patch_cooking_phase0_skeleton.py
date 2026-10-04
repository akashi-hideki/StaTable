"""Phase 0: skeleton (Project + settings + minimal global defs)."""
from __future__ import annotations

import sys
from xml.etree import ElementTree as ET

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _cooking_common import save


def main() -> int:
    root = ET.Element("Project", {"name": "CookingHeaterController"})

    # --- ProjectSettings ---
    ps = ET.SubElement(root, "ProjectSettings")
    ET.SubElement(ps, "CodeGeneration", {
        "project_name": "CookingHeaterController",
        "table_type": "array", "generation_style": "table_driven",
        "os_type": "non_rtos", "folder_structure": "by_layer",
        "include_dir_name": "include", "source_dir_name": "src",
        "common_dir_name": "common", "project_dir_name": "project",
        "generate_super_include": "true", "super_include_file": "statable_all.h",
        "max_consecutive_pending_events": "16",
        "external_includes_in_super": "true",
        "external_includes_in_role": "true",
        "external_includes_in_transitions": "false",
        "external_includes_in_common": "false",
    })

    # --- GlobalDefinitions ---
    gd = ET.SubElement(root, "GlobalDefinitions")
    sv = ET.SubElement(gd, "SystemVariables")
    ET.SubElement(sv, "Variable", {
        "name": "g_system_tick", "type": "volatile uint32_t", "unit": "1ms",
        "default_value": "0", "group": "Timer",
        "description": "System tick", "title": "System tick", "array_size": "0"})
    ET.SubElement(sv, "Variable", {
        "name": "error_code", "type": "uint8_t", "unit": "",
        "default_value": "0", "group": "System",
        "description": "Error code", "title": "Error code", "array_size": "0"})

    ef = ET.SubElement(gd, "EventFlags")
    ET.SubElement(ef, "Flag", {
        "name": "EVT_SEQ_READY", "min_value": "0", "max_value": "1",
        "group": "System", "description": "Sequence ready flag",
        "title": "Sequence ready"})
    ET.SubElement(ef, "Flag", {
        "name": "EVT_OVERHEAT", "min_value": "0", "max_value": "1",
        "group": "Safety", "description": "Overheat flag",
        "title": "Overheat"})

    ints = ET.SubElement(gd, "Interrupts")
    it = ET.SubElement(ints, "Interrupt", {
        "name": "TIMER0", "description": "1ms timer", "event_names": "",
        "is_timer": "true", "title": "Timer0"})
    ET.SubElement(it, "Action", {"condition": "",
        "action": "ctx->data.g_system_tick++"})
    ET.SubElement(it, "UsedVariable", {"name": "g_system_tick"})

    tb = ET.SubElement(gd, "TimerBase")
    ET.SubElement(tb, "Timer", {
        "variable_name": "g_system_tick", "unit": "1ms",
        "data_type": "volatile uint32_t", "title": "System tick",
        "interrupt_name": "TIMER0"})

    # --- SharedLibraries ---
    sl = ET.SubElement(root, "SharedLibraries")
    ET.SubElement(sl, "RoleFunctionLibrary")
    ET.SubElement(sl, "ConditionLibrary")
    ET.SubElement(sl, "LiteralLibrary")

    save(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())