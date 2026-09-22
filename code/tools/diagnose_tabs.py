#!/usr/bin/env python3
# code/tools/diagnose_tabs.py
"""Diagnose per-tab parsing in project_from_xml.

Usage:
    python tools/diagnose_tabs.py docs/tutorial/vending_machine.xml
"""

from __future__ import annotations

import sys
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from statable import xml_io


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python tools/diagnose_tabs.py <xml>")
        return 1

    xml_path = Path(sys.argv[1])
    print(f"File: {xml_path}")
    print()

    # ---- 1. Well-formedness ----
    print("=== [1] XML well-formedness ===")
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        print(f"  root tag: {root.tag}")
        tabs_elems = root.findall("Tab")
        print(f"  <Tab> count: {len(tabs_elems)}")
        for i, tab in enumerate(tabs_elems):
            print(f"    [{i}] name={tab.get('name')!r}")
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        return 1
    print()

    # ---- 2. Per-tab parse via xml_io internals ----
    print("=== [2] Per-tab parse (via state_machine_from_element) ===")
    fn = getattr(xml_io, "state_machine_from_element", None)
    if fn is None:
        print("  (state_machine_from_element not found; skipping)")
    else:
        for i, tab in enumerate(tabs_elems):
            name = tab.get("name")
            sm_elem = tab.find("StateMachine")
            if sm_elem is None:
                print(f"  [{i}] {name}: <StateMachine> NOT FOUND")
                continue
            try:
                sm = fn(sm_elem)
                print(f"  [{i}] {name}: OK "
                      f"(states={len(sm.states)}, "
                      f"events={len(sm.events)}, "
                      f"transitions={len(sm.transitions)})")
            except Exception as e:
                print(f"  [{i}] {name}: FAILED -> "
                      f"{type(e).__name__}: {e}")
                traceback.print_exc()
    print()

    # ---- 3. Full project_from_xml with trace ----
    print("=== [3] Full project_from_xml (with trace) ===")
    try:
        result = xml_io.project_from_xml(str(xml_path))
        tabs = result[0]
        print(f"  type(tabs) = {type(tabs).__name__}")
        print(f"  len(tabs)  = {len(tabs)}")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()

    return 0


if __name__ == "__main__":
    sys.exit(main())