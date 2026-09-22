#!/usr/bin/env python3
# code/tools/diagnose_xml.py
"""Diagnose how project_from_xml parses a given file.

Usage:
    python tools/diagnose_xml.py docs/tutorial/vending_machine.xml
"""

from __future__ import annotations

import sys
from pathlib import Path

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from statable.xml_io import project_from_xml


def describe(sm, label: str) -> None:
    layer_name = getattr(sm, 'layer_name', '?')
    states = getattr(sm, 'states', {})
    events = getattr(sm, 'events', {})
    transitions = getattr(sm, 'transitions', [])
    role_funcs = getattr(sm, 'role_functions', {})
    initial = getattr(sm, 'initial_state', None)
    priority = getattr(sm, 'layer_priority', '?')

    print(f"  {label}")
    print(f"    layer_name      = {layer_name!r}")
    print(f"    layer_priority  = {priority}")
    print(f"    initial_state   = {initial!r}")
    print(f"    states          = {len(states)}")
    print(f"    events          = {len(events)}")
    print(f"    transitions     = {len(transitions)}")
    print(f"    role_functions  = {len(role_funcs)}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python tools/diagnose_xml.py <xml>")
        return 1

    xml_path = sys.argv[1]
    print(f"Loading: {xml_path}")

    result = project_from_xml(xml_path)
    tabs = result[0]

    print()
    print(f"type(tabs) = {type(tabs).__name__}")
    print(f"len(tabs)  = {len(tabs)}")
    print()

    if isinstance(tabs, dict):
        for name, sm in tabs.items():
            describe(sm, f"tab name={name!r}")
    else:
        for i, item in enumerate(tabs):
            if isinstance(item, tuple) and len(item) >= 2:
                name, sm = item[0], item[1]
                describe(sm, f"[{i}] tab name={name!r}")
            else:
                describe(item, f"[{i}] (no name)")

    return 0


if __name__ == "__main__":
    sys.exit(main())