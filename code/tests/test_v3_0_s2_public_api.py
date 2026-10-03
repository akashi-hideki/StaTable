# code/tests/test_v3_0_s2_public_api.py
"""
Phase S-2 (v3.0) tests: public API definition.

Verifies:
  - statable.__all__ contains '__version__'
  - codegen.__all__ contains 'validate' and '__version__'
  - codegen.validate accessible (PEP 562 lazy import)
  - codegen.validate.__all__ includes ResponseValidator / ResponseValidationResult
  - No regression: existing exports intact
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

TOTAL = 0
PASSED = 0
FAILED = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global TOTAL, PASSED, FAILED
    TOTAL += 1
    if cond:
        PASSED += 1
        print(f"[PASS] {name}")
    else:
        FAILED += 1
        print(f"[FAIL] {name}" + (f" -- {detail}" if detail else ""))


def main() -> int:
    print("=" * 70)
    print("  test_v3_0_s2_public_api")
    print("=" * 70)

    # --- T1: statable -------------------------------------------------
    try:
        import statable
        check("statable importable", True)
    except Exception as e:
        check("statable importable", False, repr(e))
        _summary()
        return 1

    check("statable has __version__ == '3.2.0'",
          getattr(statable, "__version__", None) == "3.2.0",
          f"got: {getattr(statable, '__version__', None)!r}")
    check("'__version__' in statable.__all__",
          "__version__" in statable.__all__,
          f"all: {statable.__all__}")

    # Regression: pre-existing exports
    for name in ("State", "Event", "Transition", "StateMachine",
                 "GlobalDefinitions", "CustomTypeDef"):
        check(f"statable.__all__ still has {name!r}",
              name in statable.__all__)

    # --- T2: codegen --------------------------------------------------
    try:
        import codegen
        check("codegen importable", True)
    except Exception as e:
        check("codegen importable", False, repr(e))
        _summary()
        return 1

    check("codegen has __version__ == '3.2.0'",
          getattr(codegen, "__version__", None) == "3.2.0",
          f"got: {getattr(codegen, '__version__', None)!r}")
    check("'validate' in codegen.__all__",
          "validate" in codegen.__all__,
          f"all: {codegen.__all__}")
    check("'__version__' in codegen.__all__",
          "__version__" in codegen.__all__,
          f"all: {codegen.__all__}")

    # Regression
    for name in ("CCodeGenerator", "CodeGenerationConfig", "ConfigManager"):
        check(f"codegen.__all__ still has {name!r}",
              name in codegen.__all__)

    # --- T3: codegen.validate lazy import ----------------------------
    try:
        import importlib
        validate = importlib.import_module("codegen.validate")
        check("codegen.validate importable", True)
    except Exception as e:
        check("codegen.validate importable", False, repr(e))
        _summary()
        return 1

    # Lazy accessor on codegen
    try:
        v2 = codegen.validate
        check("codegen.validate attribute access works", v2 is validate)
    except Exception as e:
        check("codegen.validate attribute access works", False, repr(e))

    # --- T4: codegen.validate exports ---------------------------------
    expected = {
        "logger", "setup_logger",
        "ValidationSeverity", "ValidationIssue",
        "ValidationResult", "ValidationContext",
        "CodeGenerationValidator",
        "AIPromptGenerator", "AIResponseParser",
        "ChangeRequest", "ChangeActionType", "ChangeApplier",
        "ClipboardManager",
        "ResponseValidator", "ResponseValidationResult",
    }
    for name in sorted(expected):
        check(f"validate.__all__ has {name!r}",
              name in validate.__all__,
              f"missing; all={validate.__all__}")

    # Importable attrs
    for name in ("ResponseValidator", "ResponseValidationResult"):
        check(f"validate.{name} importable",
              hasattr(validate, name))

    _summary()
    return 0 if FAILED == 0 else 1


def _summary() -> None:
    print("-" * 70)
    print(f"TOTAL: {TOTAL}  PASSED: {PASSED}  FAILED: {FAILED}")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())
