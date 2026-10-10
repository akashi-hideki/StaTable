# code/tests/test_v3_0_g1_shared.py
"""
Phase G-1 (v3.0) tests: GUI/shared separation.

Verifies:
  - statable.shared package exists with 3 libraries
  - statable_gui.libcntrl stubs re-export same identities
  - statable/xml_io.py imports from statable.shared
  - statable/__main__.py has friendly PySide6 error path
  - check.yml registers v3.0 test suites
  - pyproject.toml keeps statable_gui in packages + gui extras
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
REPO = CODE.parent
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
    print("  test_v3_0_g1_shared")
    print("=" * 70)

    # --- T1: statable.shared exists with libs -------------------------
    try:
        from statable.shared import (
            RoleFunctionLibrary, RoleFunction,
            ConditionLibrary, ConditionTemplate,
            LiteralLibrary, LiteralDefinition,
        )
        check("statable.shared imports OK", True)
    except Exception as e:
        check("statable.shared imports OK", False, repr(e))
        _summary()
        return 1

    shared_dir = CODE / "statable" / "shared"
    check("statable/shared/__init__.py exists",
          (shared_dir / "__init__.py").exists())
    check("statable/shared/role_function_library.py exists",
          (shared_dir / "role_function_library.py").exists())
    check("statable/shared/condition_library.py exists",
          (shared_dir / "condition_library.py").exists())
    check("statable/shared/literal_library.py exists",
          (shared_dir / "literal_library.py").exists())

    # --- T2: no PySide6 in statable/shared ----------------------------
    pyside6_count = 0
    for f in shared_dir.glob("*.py"):
        txt = f.read_text(encoding="utf-8")
        pyside6_count += txt.count("from PySide6") + txt.count("import PySide6")
    check("statable/shared has 0 PySide6 imports",
          pyside6_count == 0,
          f"found {pyside6_count}")

    # --- T3: backward-compat stub identity ----------------------------
    try:
        from statable_gui.libcntrl import (
            RoleFunctionLibrary as StubRFL,
            ConditionLibrary as StubCL,
            LiteralLibrary as StubLL,
        )
        check("statable_gui.libcntrl stub importable", True)
        check("RoleFunctionLibrary is identical (stub == shared)",
              StubRFL is RoleFunctionLibrary)
        check("ConditionLibrary is identical (stub == shared)",
              StubCL is ConditionLibrary)
        check("LiteralLibrary is identical (stub == shared)",
              StubLL is LiteralLibrary)
    except Exception as e:
        check("statable_gui.libcntrl stub importable", False, repr(e))

    # --- T4: xml_io imports from statable.shared ----------------------
    xml_io = CODE / "statable" / "xml_io.py"
    check("statable/xml_io.py exists", xml_io.exists())
    if xml_io.exists():
        txt = xml_io.read_text(encoding="utf-8")
        check("xml_io imports from statable.shared",
              "from statable.shared.role_function_library" in txt)
        check("xml_io does NOT import from statable_gui directly",
              "from statable_gui.libcntrl" not in txt,
              "still has direct statable_gui import")

    # --- T5: __main__.py friendly error path --------------------------
    main_py = CODE / "statable" / "__main__.py"
    check("statable/__main__.py exists", main_py.exists())
    if main_py.exists():
        txt = main_py.read_text(encoding="utf-8")
        check("__main__ has try/except around PySide6",
              "try:" in txt and "ImportError" in txt)
        check("__main__ mentions 'statable[gui]'",
              "statable[gui]" in txt)

    # --- T6: check.yml registers v3.0 tests ---------------------------
    check_yml = REPO / ".github" / "workflows" / "check.yml"
    check("check.yml exists", check_yml.exists(), str(check_yml))
    if check_yml.exists():
        txt = check_yml.read_text(encoding="utf-8")
        for name in ("test_v3_0_s1_packaging.py",
                     "test_v3_0_s2_public_api.py",
                     "test_v3_0_s3_cli.py",
                     "test_v3_0_s4_docs.py"):
            check(f"check.yml registers {name}",
                  name in txt)

    # --- T7: pyproject.toml config ------------------------------------
    pyproj = CODE / "pyproject.toml"
    check("pyproject.toml exists", pyproj.exists())
    if pyproj.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        data = tomllib.loads(pyproj.read_text(encoding="utf-8"))
        extras = data.get("project", {}).get("optional-dependencies", {})
        check("pyproject has 'gui' extras",
              "gui" in extras)
        check("pyproject gui extras mentions PySide6",
              any("PySide6" in d for d in extras.get("gui", [])))
        include = (data.get("tool", {})
                       .get("setuptools", {})
                       .get("packages", {})
                       .get("find", {})
                       .get("include", []))
        check("pyproject includes statable_gui*",
              any("statable_gui" in i for i in include))
        check("pyproject includes statable*",
              any(i == "statable*" for i in include))

    # --- T8: SDK-only smoke (no statable_gui import needed) -----------
    # If xml_io can load without statable_gui, the split works.
    import importlib
    try:
        importlib.import_module("statable.xml_io")
        check("statable.xml_io importable", True)
    except Exception as e:
        check("statable.xml_io importable", False, repr(e))

    _summary()
    return 0 if FAILED == 0 else 1


def _summary() -> None:
    print("-" * 70)
    print(f"TOTAL: {TOTAL}  PASSED: {PASSED}  FAILED: {FAILED}")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())