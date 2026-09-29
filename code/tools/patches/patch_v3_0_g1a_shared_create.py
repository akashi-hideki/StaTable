# code/tools/patches/patch_v3_0_g1a_shared_create.py
r"""
Phase G-1a: create statable/shared/ with 3 moved library files.

Moves (copies content, keeps original as backward-compat stub later):
  - statable_gui/libcntrl/role_function_library.py
      -> statable/shared/role_function_library.py
  - statable_gui/libcntrl/condition_library.py
      -> statable/shared/condition_library.py
  - statable_gui/libcntrl/literal_library.py
      -> statable/shared/literal_library.py

Also creates statable/shared/__init__.py with re-exports.

Original files are NOT modified here (done in G-1b).

Usage:
    cd code
    python tools\patches\patch_v3_0_g1a_shared_create.py
    python tools\patches\patch_v3_0_g1a_shared_create.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent

SHARED_DIR = CODE / "statable" / "shared"
SRC_DIR = CODE / "statable_gui" / "libcntrl"

MOVES = [
    (
        SRC_DIR / "role_function_library.py",
        SHARED_DIR / "role_function_library.py",
        "# statable/shared/role_function_library.py",
    ),
    (
        SRC_DIR / "condition_library.py",
        SHARED_DIR / "condition_library.py",
        "# statable/shared/condition_library.py",
    ),
    (
        SRC_DIR / "literal_library.py",
        SHARED_DIR / "literal_library.py",
        "# statable/shared/literal_library.py",
    ),
]

INIT_CONTENT = '''# statable/shared/__init__.py
"""
Shared project libraries.

These modules have no PySide6 dependency and can be used from the SDK
without installing the GUI extras (statable[gui]).

[v3.0 / G-1a]
  Moved from statable_gui.libcntrl to allow SDK-only installs.
  Backward-compat shims remain at statable_gui.libcntrl.* for a while.
"""

from .role_function_library import RoleFunctionLibrary, RoleFunction
from .condition_library import ConditionLibrary, ConditionTemplate
from .literal_library import LiteralLibrary, LiteralDefinition

__all__ = [
    "RoleFunctionLibrary",
    "RoleFunction",
    "ConditionLibrary",
    "ConditionTemplate",
    "LiteralLibrary",
    "LiteralDefinition",
]
'''


def _hdr(mode: str) -> None:
    print("=" * 70)
    print(f"  patch_v3_0_g1a_shared_create  [{mode}]")
    print("=" * 70)


def _copy_with_new_header(src: Path, dst: Path,
                          new_first_line: str) -> str:
    content = src.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    if lines and lines[0].startswith("#"):
        lines[0] = new_first_line + "\n"
    new_content = "".join(lines)
    dst.write_text(new_content, encoding="utf-8")
    return new_content


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    _hdr(mode)

    rc = 0

    # --- plan / verify ---
    print("[PLAN] create statable/shared/")
    for src, dst, _ in MOVES:
        if not src.exists():
            print(f"  [FAIL] source missing: {src.relative_to(CODE.parent)}")
            rc = 1
        else:
            print(f"  [OK]   {src.relative_to(CODE.parent)} -> "
                  f"{dst.relative_to(CODE.parent)}")
    if not (SHARED_DIR / "__init__.py").exists():
        print(f"  [OK]   create statable/shared/__init__.py")
    else:
        print(f"  [SKIP] statable/shared/__init__.py exists")

    if rc != 0:
        print()
        print("[ABORT] source files missing.")
        return 1

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    print()
    SHARED_DIR.mkdir(parents=True, exist_ok=True)

    for src, dst, header in MOVES:
        if dst.exists():
            print(f"[SKIP] {dst.relative_to(CODE.parent)} already exists")
            continue
        content = _copy_with_new_header(src, dst, header)
        print(f"[DONE] {dst.relative_to(CODE.parent)} "
              f"({len(content)} chars)")

    init_py = SHARED_DIR / "__init__.py"
    if not init_py.exists():
        init_py.write_text(INIT_CONTENT, encoding="utf-8")
        print(f"[DONE] statable/shared/__init__.py "
              f"({len(INIT_CONTENT)} chars)")
    else:
        print(f"[SKIP] statable/shared/__init__.py already exists")

    print()
    print("Verify:")
    print("  python -c \"import sys; sys.path.insert(0, '.'); "
          "from statable.shared import RoleFunctionLibrary, "
          "ConditionLibrary, LiteralLibrary; "
          "print('OK: shared import')\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
