# code/tests/test_v3_0_s1_packaging.py
"""
Phase S-1 (v3.0) tests: packaging foundation.

Verifies:
  - code/pyproject.toml exists and declares statable/3.2.1
  - statable-cli entry point is defined
  - extras: gui / dev
  - statable.__version__ == "3.2.1"
  - codegen.__version__ == "3.2.1"
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

# code/tests/test_v3_0_s1_packaging.py -> parents[1] = code/
CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

PYPROJECT = CODE / "pyproject.toml"

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
    print("  test_v3_0_s1_packaging")
    print("=" * 70)

    # --- T1: pyproject.toml exists ---------------------------------
    check("pyproject.toml exists", PYPROJECT.exists(),
          f"missing: {PYPROJECT}")
    if not PYPROJECT.exists():
        _summary()
        return 1

    # --- T2: parseable TOML ----------------------------------------
    try:
        data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        check("pyproject.toml is valid TOML", True)
    except Exception as e:
        check("pyproject.toml is valid TOML", False, repr(e))
        _summary()
        return 1

    project = data.get("project", {})

    # --- T3: name / version ----------------------------------------
    check("project.name == 'statable'",
          project.get("name") == "statable",
          f"got: {project.get('name')!r}")
    check("project.version == '3.2.1'",
          project.get("version") == "3.2.1",
          f"got: {project.get('version')!r}")

    # --- T4: requires-python ---------------------------------------
    check("project.requires-python is set",
          "requires-python" in project,
          "missing requires-python")

    # --- T5: entry point -------------------------------------------
    scripts = project.get("scripts", {})
    check("entry point 'statable-cli' defined",
          "statable-cli" in scripts,
          f"scripts: {list(scripts)}")
    check("statable-cli -> statable.cli:main",
          scripts.get("statable-cli") == "statable.cli:main",
          f"got: {scripts.get('statable-cli')!r}")

    # --- T6: extras -------------------------------------------------
    extras = project.get("optional-dependencies", {})
    check("extras 'gui' defined", "gui" in extras,
          f"extras: {list(extras)}")
    check("extras 'dev' defined", "dev" in extras,
          f"extras: {list(extras)}")
    check("gui extra requires PySide6",
          any("PySide6" in dep for dep in extras.get("gui", [])),
          f"gui deps: {extras.get('gui')}")

    # --- T7: build-system ------------------------------------------
    bs = data.get("build-system", {})
    check("build-system.backend == 'setuptools.build_meta'",
          bs.get("build-backend") == "setuptools.build_meta",
          f"got: {bs.get('build-backend')!r}")

    # --- T8: runtime __version__ -----------------------------------
    try:
        import statable
        check("statable.__version__ == '3.2.1'",
              getattr(statable, "__version__", None) == "3.2.1",
              f"got: {getattr(statable, '__version__', None)!r}")
    except Exception as e:
        check("statable importable", False, repr(e))

    try:
        import codegen
        check("codegen.__version__ == '3.2.1'",
              getattr(codegen, "__version__", None) == "3.2.1",
              f"got: {getattr(codegen, '__version__', None)!r}")
    except Exception as e:
        check("codegen importable", False, repr(e))

    _summary()
    return 0 if FAILED == 0 else 1


def _summary() -> None:
    print("-" * 70)
    print(f"TOTAL: {TOTAL}  PASSED: {PASSED}  FAILED: {FAILED}")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())