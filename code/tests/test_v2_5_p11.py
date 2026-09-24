#!/usr/bin/env python3
"""StaTable F-3 Step 2 test suite: per-layer pending_event slots.

Verifies:
  - SystemContext_t has per-layer pending_event_<Layer> + valid flags
  - SystemContext_t does NOT have bare pending_event
  - FIRE_EVENT_<Layer> macros exist, protected by ENTER/EXIT_CRITICAL
  - Legacy FIRE_EVENT(ctx, evt) is not emitted
  - GetNextEvent_<Layer> reads only its own slot
  - SystemContext_InitQueues resets per-layer pending slots

Run:
  python tests/test_v2_5_p11.py
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  [PASS] {name}")

    def fail(self, name, msg=""):
        self.failed += 1
        self.errors.append((name, msg))
        print(f"  [FAIL] {name}")
        if msg:
            print(f"         {msg}")

    def summary(self):
        total = self.passed + self.failed
        print()
        print("=" * 70)
        print(f"  TOTAL: {total}  PASSED: {self.passed}  FAILED: {self.failed}")
        print("=" * 70)
        return self.failed == 0


R = TestResult()


def check(name, cond, msg=""):
    if cond:
        R.ok(name)
    else:
        R.fail(name, msg)
    return cond


def _make_layers():
    from statable.state_machine import StateMachine
    out = []
    for name in ("Driver", "Middleware", "Application"):
        sm = StateMachine()
        sm.layer_name = name
        out.append((name, sm))
    return out


# ======================================================================
# [1] SystemContext_t: per-layer members, no bare pending_event
# ======================================================================
def test_per_layer_members():
    print("\n[1] SystemContext_t per-layer pending members")

    from codegen.struct_generator import CStructGenerator
    gen = CStructGenerator()
    gen.set_layers(_make_layers())
    gen.set_layer("Driver")
    out = gen.generate_struct('system_context', None)

    check("Driver slot", "pending_event_Driver" in out, f"got:\n{out}")
    check("Driver valid flag", "pending_event_valid_Driver" in out)
    check("Middleware slot", "pending_event_Middleware" in out)
    check("Application slot", "pending_event_Application" in out)

    # Bare (old) form must NOT appear
    check("no bare pending_event decl",
          " pending_event;" not in out,
          f"got:\n{out}")
    check("no bare pending_event_valid decl",
          " pending_event_valid;" not in out,
          f"got:\n{out}")


# ======================================================================
# [2] FIRE_EVENT_<Layer> macros
# ======================================================================
def test_per_layer_macros():
    print("\n[2] FIRE_EVENT_<Layer> macros")

    from codegen.struct_generator import CStructGenerator
    gen = CStructGenerator()
    gen.set_layers(_make_layers())
    gen.set_layer("Driver")
    out = gen.generate_pending_event_macros()

    check("FIRE_EVENT_Driver", "#define FIRE_EVENT_Driver(" in out,
          f"got:\n{out}")
    check("FIRE_EVENT_Middleware", "#define FIRE_EVENT_Middleware(" in out)
    check("FIRE_EVENT_Application", "#define FIRE_EVENT_Application(" in out)

    check("uses pending_event_Driver",
          "pending_event_Driver" in out)
    check("uses pending_event_valid_Driver",
          "pending_event_valid_Driver" in out)

    check("protected by ENTER_CRITICAL",
          "STATABLE_ENTER_CRITICAL()" in out)
    check("protected by EXIT_CRITICAL",
          "STATABLE_EXIT_CRITICAL()" in out)

    # Legacy FIRE_EVENT(ctx, ...) must NOT be emitted
    check("no bare FIRE_EVENT macro",
          "#define FIRE_EVENT(ctx" not in out,
          f"got:\n{out}")

    # Removal notice present
    check("removal notice",
          "FIRE_EVENT(ctx, evt) is removed" in out,
          f"got:\n{out}")


# ======================================================================
# [3] GetNextEvent_<Layer> uses own slot
# ======================================================================
def test_get_next_event_uses_own_slot():
    print("\n[3] GetNextEvent_<Layer> uses own slot")

    from statable.state_machine import StateMachine
    from codegen.transition_generator import TransitionGenerator

    sm = StateMachine()
    sm.layer_name = "Driver"
    gen = TransitionGenerator()
    gen.set_layer("Driver")
    out = gen.generate_get_next_event_function(sm)

    check("reads pending_event_Driver",
          "ctx->pending_event_Driver" in out, f"got:\n{out}")
    check("reads pending_event_valid_Driver",
          "ctx->pending_event_valid_Driver" in out)
    check("no bare ctx->pending_event;",
          "ctx->pending_event;" not in out)
    check("F-3 S2 comment present",
          "[F-3 S2]" in out)


# ======================================================================
# [4] SystemContext_InitQueues resets pending slots
# ======================================================================
def test_init_queues_resets_pending():
    print("\n[4] InitQueues resets pending slots")

    from statable.xml_io import project_from_xml
    from codegen.c_code_generator import CCodeGenerator
    from codegen.config import CodeGenerationConfig

    xml = PROJECT_ROOT / "docs" / "tutorial" / "vending_machine.xml"
    if not xml.exists():
        R.fail("vending XML not found", str(xml))
        return

    tabs, gd, _, _, _, ps = project_from_xml(str(xml))
    cfg = CodeGenerationConfig(**{
        k: v for k, v in ps.items()
        if hasattr(CodeGenerationConfig, k)
    })
    gen = CCodeGenerator(config=cfg)
    files = gen.generate_all_layers(tabs, gd)

    init_c = None
    for k, v in files.items():
        if k.endswith("statable_init.c"):
            init_c = v
            break

    check("statable_init.c generated", init_c is not None)
    if init_c:
        check("resets pending_event_Driver",
              "ctx->pending_event_Driver = 0U" in init_c,
              f"got:\n{init_c}")
        check("resets pending_event_valid_Driver",
              "ctx->pending_event_valid_Driver = false" in init_c)
        check("resets pending_event_Middleware",
              "ctx->pending_event_Middleware = 0U" in init_c)
        check("resets pending_event_Application",
              "ctx->pending_event_Application = 0U" in init_c)


# ======================================================================
# [5] Full vending generation
# ======================================================================
def test_full_vending():
    print("\n[5] Full vending generation")

    from statable.xml_io import project_from_xml
    from codegen.c_code_generator import CCodeGenerator
    from codegen.config import CodeGenerationConfig

    xml = PROJECT_ROOT / "docs" / "tutorial" / "vending_machine.xml"
    if not xml.exists():
        R.fail("vending XML not found", str(xml))
        return

    tabs, gd, _, _, _, ps = project_from_xml(str(xml))
    cfg = CodeGenerationConfig(**{
        k: v for k, v in ps.items()
        if hasattr(CodeGenerationConfig, k)
    })
    gen = CCodeGenerator(config=cfg)
    files = gen.generate_all_layers(tabs, gd)

    h = None
    for k, v in files.items():
        if k.endswith("statable_types_common.h"):
            h = v
            break

    check("statable_types_common.h generated", h is not None)
    if h:
        check("3-layer pending slots present",
              all(f"pending_event_{L}" in h
                  for L in ("Driver", "Middleware", "Application")))
        check("3-layer valid flags present",
              all(f"pending_event_valid_{L}" in h
                  for L in ("Driver", "Middleware", "Application")))
        check("3 FIRE_EVENT_<Layer> macros",
              all(f"#define FIRE_EVENT_{L}(" in h
                  for L in ("Driver", "Middleware", "Application")))


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable F-3 Step 2 (per-layer pending_event)")
    print("=" * 70)

    from PySide6.QtWidgets import QApplication
    _ = QApplication.instance() or QApplication(sys.argv)

    test_per_layer_members()
    test_per_layer_macros()
    test_get_next_event_uses_own_slot()
    test_init_queues_resets_pending()
    test_full_vending()

    ok = R.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()