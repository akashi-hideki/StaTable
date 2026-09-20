# code/check_smoke.py
"""StaTable smoke check.

Verifies that the recent Mermaid/widgets changes did not break
core functionality: data model, Mermaid generation, and code
generation module imports.

Usage:
    python check_smoke.py

Exit code:
    0 = all required checks passed
    1 = a required check failed
"""

import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

print("=" * 64)
print("StaTable smoke check")
print("=" * 64)
print(f"Python  : {sys.version.split()[0]}")
print(f"Code dir: {HERE}")
print()

failures = []


def check(name, fn, required=True):
    """Run a single check; print OK / FAIL / WARN."""
    print(f"[{name}]")
    try:
        result = fn()
        if result is False:
            print("    FAIL (returned False)")
            if required:
                failures.append(name)
        else:
            print("    OK")
        return True
    except Exception as e:
        label = "FAIL" if required else "WARN"
        print(f"    {label}: {e}")
        if required:
            failures.append(name)
            traceback.print_exc()
        return False


# ----------------------------------------------------------------------
# 1. Core statable modules
# ----------------------------------------------------------------------
def check_core_imports():
    from statable.model import State, Transition, StateType
    from statable.state_machine import StateMachine
    from statable.mermaid_gen import generate_mermaid
    return True


# ----------------------------------------------------------------------
# 2. Mermaid generation (functional)
# ----------------------------------------------------------------------
def check_mermaid_generation():
    from statable.model import State, Transition, StateType
    from statable.state_machine import StateMachine
    from statable.mermaid_gen import generate_mermaid

    sm = StateMachine()
    sm.add_state(State("Idle", type=StateType.NORMAL))
    sm.add_state(State("Running", type=StateType.NORMAL))
    sm.initial_state = "Idle"

    # Transition construction: use kwargs if supported, else attrs.
    tr = None
    try:
        tr = Transition(source="Idle", target="Running",
                        event="start", condition="x > 0")
    except TypeError:
        tr = Transition()
        tr.source = "Idle"
        tr.target = "Running"
        tr.event = "start"
        tr.condition = "x > 0"
    sm.transitions.append(tr)

    code = generate_mermaid(sm)
    print("    --- generated mermaid ---")
    for line in code.splitlines():
        print(f"    | {line}")

    assert "stateDiagram-v2" in code, "missing stateDiagram-v2 header"
    assert "direction LR" in code, "missing direction line"
    assert "Idle --> Running" in code, "missing primary transition"
    return True


# ----------------------------------------------------------------------
# 3. Code generation module import (safety only)
# ----------------------------------------------------------------------
def check_codegen_import():
    # Codegen lives under code/codegen/ in this project.
    codegen_dir = os.path.join(HERE, "codegen")
    if codegen_dir not in sys.path:
        sys.path.insert(0, codegen_dir)

    # Try both import styles the project uses.
    try:
        from codegen.c_code_generator import CCodeGenerator  # noqa: F401
    except ImportError:
        from c_code_generator import CCodeGenerator  # noqa: F401
    return True


# ----------------------------------------------------------------------
# 4. GUI widgets import (QtWebEngine may be heavy; non-required)
# ----------------------------------------------------------------------
def check_widgets_import():
    from statable_gui.widgets import MermaidWidget  # noqa: F401
    return True


# ----------------------------------------------------------------------
# 5. Mermaid_gen still exposes expected symbols
# ----------------------------------------------------------------------
def check_mermaid_gen_api():
    import statable.mermaid_gen as mg
    assert hasattr(mg, "generate_mermaid"), "generate_mermaid missing"
    assert hasattr(mg, "_sanitize_label"), "_sanitize_label missing"
    assert hasattr(mg, "_build_label"), "_build_label missing"
    return True


# ----------------------------------------------------------------------
# Run checks
# ----------------------------------------------------------------------
check("1. Core statable imports", check_core_imports, required=True)
check("2. Mermaid generation", check_mermaid_generation, required=True)
check("3. Codegen import", check_codegen_import, required=True)
check("4. GUI widgets import", check_widgets_import, required=False)
check("5. mermaid_gen API", check_mermaid_gen_api, required=True)

print()
print("=" * 64)
if failures:
    print("RESULT: FAIL")
    for f in failures:
        print(f"  - {f}")
    print("=" * 64)
    sys.exit(1)
else:
    print("RESULT: PASS")
    print("=" * 64)
    sys.exit(0)