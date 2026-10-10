"""Dump current XML structure for documentation alignment."""
from __future__ import annotations
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

XML = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "cooking_heater_controller.xml")


def main() -> int:
    if not XML.exists():
        print(f"[ERR] {XML} not found")
        return 1

    root = ET.parse(XML).getroot()
    print(f"\n{'=' * 74}")
    print(f"  XML structure: {XML.name}")
    print(f"{'=' * 74}")

    tabs = root.findall("Tab")
    print(f"\nTabs: {len(tabs)}\n")

    total_states = 0
    total_events = 0
    total_transitions = 0

    for tab in tabs:
        name = tab.get("name")
        sm = tab.find("StateMachine")
        if sm is None:
            print(f"  [WARN] {name}: no StateMachine")
            continue

        layer_name = sm.get("layer_name", "")
        priority = sm.get("layer_priority", "")
        initial = sm.get("initial", "")

        states = sm.findall("States/State")
        events = sm.findall("Events/Event")
        roles = sm.findall("RoleFunctions/RoleFunction")
        transitions = sm.findall("Transitions/Transition")

        total_states += len(states)
        total_events += len(events)
        total_transitions += len(transitions)

        print(f"  [{name}]")
        print(f"    layer_name    : {layer_name}")
        print(f"    priority      : {priority}")
        print(f"    initial       : {initial}")
        print(f"    states        : {len(states)}")
        for s in states:
            print(f"      - {s.get('name'):20s} type={s.get('type')}")
        print(f"    events        : {len(events)}")
        print(f"    roles         : {len(roles)}")
        for r in roles:
            print(f"      - {r.get('namespace')}.{r.get('name')}")
        print(f"    transitions   : {len(transitions)}")
        print()

    # Roles in shared library
    rfl = root.find("SharedLibraries/RoleFunctionLibrary")
    all_roles = rfl.findall("RoleFunction") if rfl is not None else []
    print(f"{'=' * 74}")
    print(f"  TOTAL")
    print(f"{'=' * 74}")
    print(f"  tabs        : {len(tabs)}")
    print(f"  states      : {total_states}")
    print(f"  events      : {total_events}")
    print(f"  transitions : {total_transitions}")
    print(f"  roles(lib)  : {len(all_roles)}")

    # Roles grouped by namespace
    from collections import Counter
    ns_counts = Counter(r.get("namespace") for r in all_roles)
    print(f"\n  Roles by namespace:")
    for ns, cnt in sorted(ns_counts.items()):
        print(f"    {ns:20s} : {cnt}")

    return 0


if __name__ == "__main__":
    sys.exit(main())