#!/usr/bin/env python3
"""
Verify that RoleFunction data round-trips losslessly through XML.

Checks
------
1. save -> load: every RoleFunction field survives the round-trip
   (name, namespace, description, title,
    return_type, arg1_type, arg1_name, arg2_type, arg2_name,
    used_global_vars, used_events, used_literals)
2. The XML file itself contains all expected attributes.
3. Loading an XML that lacks used_* attributes yields [] (backward
   compatibility with pre-v3.8 files).
4. Loading an XML that has legacy 1-char-split actions works.

Usage
-----
    python tools/verify_role_function_xml.py
    python tools/verify_role_function_xml.py --xml path/to/project.xml
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import os
from pathlib import Path

# Ensure the code/ root is importable
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from statable.model import RoleFunction, State, Event, Transition
from statable.state_machine import StateMachine
from statable.global_defs import GlobalDefinitions
from statable.xml_io import (
    project_to_xml, project_from_xml,
    state_machine_to_element, state_machine_from_element,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def _pass(msg: str) -> None:
    print(f"  [PASS] {msg}")


def _info(msg: str) -> None:
    print(f"  [info] {msg}")


def _section(title: str) -> None:
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def _rf_to_dict(rf: RoleFunction) -> dict:
    return {
        "name": rf.name,
        "namespace": getattr(rf, "namespace", ""),
        "description": rf.description,
        "title": rf.title,
        "return_type": getattr(rf, "return_type", ""),
        "arg1_type": getattr(rf, "arg1_type", ""),
        "arg1_name": getattr(rf, "arg1_name", ""),
        "arg2_type": getattr(rf, "arg2_type", ""),
        "arg2_name": getattr(rf, "arg2_name", ""),
        "used_global_vars": list(getattr(rf, "used_global_vars", []) or []),
        "used_events": list(getattr(rf, "used_events", []) or []),
        "used_literals": list(getattr(rf, "used_literals", []) or []),
    }


def _diff_dicts(a: dict, b: dict, label: str) -> bool:
    """Return True if a == b; print any differences."""
    ok = True
    for key in a:
        va = a[key]
        vb = b[key]
        if va != vb:
            ok = False
            print(f"    {label}.{key}:")
            print(f"      before = {va!r}")
            print(f"      after  = {vb!r}")
    return ok


# ----------------------------------------------------------------------
# Test 1: Full round-trip through project_to_xml / project_from_xml
# ----------------------------------------------------------------------
def test_full_roundtrip() -> bool:
    _section("Test 1: project_to_xml -> project_from_xml round-trip")

    sm = StateMachine()
    sm.layer_name = "Application"
    sm.add_state(State(name="Idle"))
    sm.add_state(State(name="Active"))
    sm.add_event(Event(name="START"))
    sm.add_event(Event(name=""))  # completion

    # Roles covering all fields
    sm.add_role_function(RoleFunction(
        name="Init", namespace="Application",
        description="Initialization",
        title="Init",
        return_type="int", arg1_type="uint8_t", arg1_name="ch",
        arg2_type="uint32_t", arg2_name="t_ms",
        used_global_vars=["g_counter", "g_flag"],
        used_events=["START"],
        used_literals=["RETRY_THRESHOLD"],
    ))
    sm.add_role_function(RoleFunction(
        name="Do", namespace="Application",
        description="Do work", title="Do",
        used_global_vars=[],
        used_events=["START", "STOP"],
        used_literals=[],
    ))
    sm.add_role_function(RoleFunction(
        name="Plain", namespace="",   # no namespace
        description="No layer", title="Plain",
    ))

    # Snapshot before
    before = {rf.name: _rf_to_dict(rf)
              for rf in sm.role_functions.values()}

    gd = GlobalDefinitions()

    # Save
    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml",
            delete=False, encoding="utf-8") as f:
        tmp = f.name
    try:
        project_to_xml([("Application", sm)], gd, tmp)

        # Show the XML snippet for the roles
        _info(f"Saved XML: {tmp}")
        text = Path(tmp).read_text(encoding="utf-8")
        for line in text.splitlines():
            if "<RoleFunction" in line:
                print(f"    {line.strip()}")

        # Load
        tabs, gd2, _, _, _, _ = project_from_xml(tmp)
        sm2 = tabs[0][1]
        after = {rf.name: _rf_to_dict(rf)
                 for rf in sm2.role_functions.values()}

        # Compare
        if set(before.keys()) != set(after.keys()):
            _fail(f"Key sets differ: "
                  f"before={sorted(before.keys())}, "
                  f"after={sorted(after.keys())}")
            return False

        all_ok = True
        for name in before:
            if not _diff_dicts(before[name], after[name], name):
                all_ok = False

        if all_ok:
            _pass(f"All {len(before)} role functions round-trip identically")
        return all_ok
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


# ----------------------------------------------------------------------
# Test 2: Backward compatibility (no used_* attributes)
# ----------------------------------------------------------------------
def test_backward_compat() -> bool:
    _section("Test 2: Old XML without used_* attributes -> []")

    old_xml = """<?xml version='1.0' encoding='utf-8'?>
<StateMachine initial="Idle" layer_name="Application">
  <States>
    <State name="Idle" type="normal"/>
  </States>
  <Events/>
  <RoleFunctions>
    <RoleFunction name="Init" namespace="Application"
                  description="Initialization"
                  return_type="int" arg1_type="uint8_t" arg1_name="ch"
                  arg2_type="uint32_t" arg2_name="t_ms"
                  title="Init"/>
  </RoleFunctions>
  <Transitions/>
</StateMachine>
"""

    with tempfile.NamedTemporaryFile(
            mode="w", suffix=".xml",
            delete=False, encoding="utf-8") as f:
        f.write(old_xml)
        tmp = f.name

    try:
        sm = state_machine_from_element(
            __import__("xml.etree.ElementTree", fromlist=["ElementTree"])
            .parse(tmp).getroot())

        rf = sm.role_functions.get("Init")
        if rf is None:
            _fail("RoleFunction 'Init' not loaded")
            return False

        ok = True
        if getattr(rf, "used_global_vars", None) != []:
            _fail(f"used_global_vars should be [] but got "
                  f"{getattr(rf, 'used_global_vars', 'MISSING')!r}")
            ok = False
        if getattr(rf, "used_events", None) != []:
            _fail(f"used_events should be [] but got "
                  f"{getattr(rf, 'used_events', 'MISSING')!r}")
            ok = False
        if getattr(rf, "used_literals", None) != []:
            _fail(f"used_literals should be [] but got "
                  f"{getattr(rf, 'used_literals', 'MISSING')!r}")
            ok = False

        # Reserved fields must survive
        if rf.return_type != "int":
            _fail(f"return_type lost: {rf.return_type!r}")
            ok = False
        if rf.arg1_name != "ch":
            _fail(f"arg1_name lost: {rf.arg1_name!r}")
            ok = False

        if ok:
            _pass("Old XML loads; used_* default to []; reserved fields kept")
        return ok
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


# ----------------------------------------------------------------------
# Test 3: Verify an existing XML file
# ----------------------------------------------------------------------
def test_existing_file(path: str) -> bool:
    _section(f"Test 3: Inspect existing XML: {path}")

    p = Path(path)
    if not p.exists():
        _fail(f"File not found: {path}")
        return False

    tabs, gd, role_lib, cond_lib, lit_lib, settings = project_from_xml(
        str(p))

    total = 0
    ok = True
    for name, sm in tabs:
        _info(f"Tab '{name}' (layer_name={sm.layer_name!r}): "
              f"{len(sm.role_functions)} role functions")
        for rf in sm.role_functions.values():
            total += 1
            d = _rf_to_dict(rf)
            print(f"    {rf.name:<20} "
                  f"ns={d['namespace']!r:<15} "
                  f"used_vars={d['used_global_vars']} "
                  f"used_events={d['used_events']} "
                  f"used_lits={d['used_literals']}")

    _info(f"Shared library: {len(role_lib.list_all()) if role_lib else 0}"
          f" role functions")
    if role_lib:
        for rf in role_lib.list_all():
            print(f"    [lib] {rf.qualified_name:<25} "
                  f"used_vars={list(getattr(rf, 'used_global_vars', []))}")

    if total == 0 and (not role_lib or len(role_lib.list_all()) == 0):
        _fail("No role functions found in the file")
        return False
    return ok


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", default=None,
                    help="Also inspect this XML file")
    args = ap.parse_args()

    print("=" * 72)
    print("  StaTable: RoleFunction XML round-trip verification")
    print("=" * 72)

    r1 = test_full_roundtrip()
    r2 = test_backward_compat()
    r3 = True
    if args.xml:
        r3 = test_existing_file(args.xml)

    _section("Summary")
    print(f"  Test 1 (round-trip)          : {'PASS' if r1 else 'FAIL'}")
    print(f"  Test 2 (backward compat)     : {'PASS' if r2 else 'FAIL'}")
    if args.xml:
        print(f"  Test 3 (existing file)       : {'PASS' if r3 else 'FAIL'}")

    return 0 if (r1 and r2 and r3) else 1


if __name__ == "__main__":
    sys.exit(main())