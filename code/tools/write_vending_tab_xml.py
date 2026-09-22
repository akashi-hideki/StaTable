#!/usr/bin/env python3
# code/tools/write_vending_tab_xml.py
"""Write a variant of the vending tutorial XML where the third layer's
Tab name / layer_name / namespace are ALL "Vending" (not "Application").

Purpose: verify that a user-chosen layer name works end-to-end
(GUI, codegen, gcc + arm), not just a user-chosen namespace.

Usage:
    python tools/write_vending_tab_xml.py
"""

from __future__ import annotations
from pathlib import Path


SRC = (Path(__file__).resolve().parent.parent
       / "docs" / "tutorial" / "vending_machine.xml")
DST = (Path(__file__).resolve().parent.parent
       / "docs" / "tutorial" / "vending_machine_vending_tab.xml")


# Substitutions to transform Application-layer into Vending-layer
SUBSTITUTIONS = [
    # Tab and StateMachine attributes
    ('<Tab name="Application">', '<Tab name="Vending">'),
    ('layer_name="Application"', 'layer_name="Vending"'),
    ('layer_description="Vending machine application"',
     'layer_description="Vending layer"'),
    # C identifiers used by codegen for the Application layer
    ('TransitionContext_Application_t', 'TransitionContext_Vending_t'),
    ('STATE_Application_', 'STATE_Vending_'),
    ('EVENT_Application_', 'EVENT_Vending_'),
    # Header / source file names in by_layer layout
    ('statable_role_functions_Application.h',
     'statable_role_functions_Vending.h'),
    ('statable_role_functions_Application.c',
     'statable_role_functions_Vending.c'),
    ('statable_transitions_Application.h',
     'statable_transitions_Vending.h'),
    ('statable_transitions_Application.c',
     'statable_transitions_Vending.c'),
    ('statable_types_Application.h', 'statable_types_Vending.h'),
    # Role function headers included from transition .c
    ('"Application/statable_role_functions_Application.h"',
     '"Vending/statable_role_functions_Vending.h"'),
]


def main() -> int:
    if not SRC.exists():
        print(f"ERROR: {SRC} not found")
        return 1

    text = SRC.read_text(encoding="utf-8")
    print(f"Source: {SRC}")
    print(f"Dest:   {DST}")
    print()
    print("Substitutions:")
    total = 0
    for old, new in SUBSTITUTIONS:
        n = text.count(old)
        if n:
            print(f"  [{n:3d}] {old!r}")
        text = text.replace(old, new)
        total += n
    print()
    print(f"Total: {total}")

    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(text, encoding="utf-8", newline="\n")
    print(f"Written: {DST}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())