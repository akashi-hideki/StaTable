# tests/test_v2_8_p4_gui_integration.py
"""
StaTable v2.8 P4 (GUI integration) test suite

Static checks of the ValidationDialog integration (Phase C-2):
  - Module imports ResponseValidator
  - __init__ creates self.response_validator / self.validation_outcome
  - Change tree has 7 columns (Selection..Status)
  - _parse_response calls validate() and handles invalid_requests
  - ValidationDialog class importable (offscreen Qt)
  - Round-trip: Request -> validator -> applier
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

_total = 0
_passed = 0
_failed = 0


def check(label, condition):
    global _total, _passed, _failed
    _total += 1
    if condition:
        _passed += 1
        print(f"  [PASS] {label}")
    else:
        _failed += 1
        print(f"  [FAIL] {label}")


def section(title):
    print()
    print(f"[{title}]")


VD_PATH = Path(__file__).resolve().parent.parent \
    / "codegen" / "validate" / "validation_dialog.py"


# ======================================================================
# [1] Source-level structure
# ======================================================================
section("1 validation_dialog.py source structure")
src = VD_PATH.read_text(encoding="utf-8")

check("imports ResponseValidator",
      "from .response_validator import ResponseValidator" in src)
check("instantiates ResponseValidator",
      "self.response_validator = ResponseValidator()" in src)
check("validation_outcome initialized",
      "self.validation_outcome = None" in src)

for col in ("Selection", "Action", "Parameter", "Reason",
            "Priority", "Confidence", "Status"):
    check(f"header has {col}", f'"{col}"' in src)

check("calls response_parser.parse",
      "self.response_parser.parse(text)" in src)
check("calls response_validator.validate",
      "self.response_validator.validate(" in src)
check("iterates valid_requests",
      "outcome.valid_requests" in src)
check("iterates invalid_requests",
      "outcome.invalid_requests" in src)
check("uses warnings list", "outcome.warnings" in src)
check("EXCLUDED label present", "EXCLUDED:" in src)


# ======================================================================
# [2] Qt import + class availability
# ======================================================================
section("2 ValidationDialog imports (headless Qt)")

try:
    from PySide6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication([])
    qt_ok = True
except Exception as e:
    print(f"  [INFO] Qt init failed: {e}")
    qt_ok = False

check("PySide6 QtWidgets importable", qt_ok)

if qt_ok:
    try:
        import importlib
        mod = importlib.import_module("codegen.validate.validation_dialog")
        check("validation_dialog module imported", True)
        check("ValidationDialog class present",
              hasattr(mod, "ValidationDialog"))
        cls = getattr(mod, "ValidationDialog")
        for name in ("_setup_changes_tab", "_parse_response",
                     "_apply_changes", "_run_validation"):
            check(f"has {name}", hasattr(cls, name))
    except Exception as e:
        print(f"  [INFO] import error: {e}")
        check("validation_dialog module imported", False)


# ======================================================================
# [3] Round-trip: Request -> validator -> applier
# ======================================================================
section("3 Round-trip: ChangeRequest via validator and applier")
try:
    from codegen.validate.change_actions import (
        ChangeRequest, ChangeActionType,
    )
    from codegen.validate.response_validator import ResponseValidator
    from codegen.validate.change_applier import ChangeApplier
    from statable.state_machine import StateMachine
    from statable.model import State, Event, StateType, EventKind

    sm = StateMachine()
    sm.layer_name = "L"
    sm.add_state(State(name="A", type=StateType.NORMAL))
    sm.add_state(State(name="B", type=StateType.NORMAL))
    sm.add_event(Event(name="E", kind=EventKind.SIGNAL))
    sm.set_initial("A")

    req = ChangeRequest(
        action=ChangeActionType.ADD_TRANSITION,
        params={"source": "A", "event": "E", "target": "B"},
        reason="connect A to B",
        id="C-001",
        priority="high",
        confidence=0.9,
    )
    v = ResponseValidator()
    outcome = v.validate([req], sm)
    check("validator accepts", len(outcome.valid_requests) == 1)

    if outcome.valid_requests:
        applier = ChangeApplier(sm, None)
        result = applier.apply_all(outcome.valid_requests)
        check("applier applied 1", result.get("applied", 0) == 1)
        check("transition exists",
              any(t.source == "A" and t.event == "E" and t.target == "B"
                  for t in sm.transitions))
except Exception as e:
    print(f"  [INFO] round-trip failed: {e}")
    check("round-trip completed", False)


# ======================================================================
# Summary
# ======================================================================
print()
print("=" * 70)
print(f"  TOTAL: {_total}  PASSED: {_passed}  FAILED: {_failed}")
print("=" * 70)

sys.exit(0 if _failed == 0 else 1)