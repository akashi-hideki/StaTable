#!/usr/bin/env python3
"""
StaTable SDK Quick Start
========================

Demonstrates the Python SDK:
  1. Build a StateMachine
  2. Configure code generation
  3. Generate C code
  4. Save with marker-based merge

Run:
    cd code
    python examples/quickstart.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `code/` importable
CODE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE))

from statable import (
    State, Event, Transition, StateMachine,
    StateType, EventKind,
)
from statable.global_defs import GlobalDefinitions
from codegen import CCodeGenerator, CodeGenerationConfig


def build_state_machine() -> StateMachine:
    sm = StateMachine()

    sm.add_state(State(name="Idle", type=StateType.INITIAL))
    sm.add_state(State(name="Running", type=StateType.NORMAL))
    sm.add_state(State(name="Done", type=StateType.FINAL))

    sm.add_event(Event(name="START", kind=EventKind.SIGNAL))
    sm.add_event(Event(name="STOP", kind=EventKind.SIGNAL))

    sm.set_initial("Idle")

    sm.add_transition(Transition(
        source="Idle", event="START", target="Running",
    ))
    sm.add_transition(Transition(
        source="Running", event="STOP", target="Done",
    ))

    return sm


def main() -> int:
    print("=== StaTable SDK Quick Start ===")

    sm = build_state_machine()
    gd = GlobalDefinitions()

    cfg = CodeGenerationConfig()
    cfg.folder_structure = "by_type"

    gen = CCodeGenerator(config=cfg)
    generated = gen.generate_all_layers(
        [("Application", sm)], gd,
    )
    print(f"Generated {len(generated)} files:")
    for name in sorted(generated.keys()):
        print(f"  {name}")

    out_dir = Path(__file__).parent / "_output"
    out_dir.mkdir(exist_ok=True)
    saved = gen.save_generated_code(generated, str(out_dir))
    print(f"Saved {len(saved)} files to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
