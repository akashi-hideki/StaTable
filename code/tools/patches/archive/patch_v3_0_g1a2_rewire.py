# code/tools/patches/patch_v3_0_g1a2_rewire.py
r"""
Phase G-1a-2: rewire imports + convert old libcntrl files to stubs.

Edits:
  E1. statable/xml_io.py: import from statable.shared (not statable_gui)
  E2. statable_gui/libcntrl/role_function_library.py -> stub
  E3. statable_gui/libcntrl/condition_library.py     -> stub
  E4. statable_gui/libcntrl/literal_library.py       -> stub
  E5. statable_gui/libcntrl/__init__.py              -> stub

Backward compatibility:
  Old paths `statable_gui.libcntrl.X` still work via re-export.

Usage:
    cd code
    python tools\patches\patch_v3_0_g1a2_rewire.py
    python tools\patches\patch_v3_0_g1a2_rewire.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent

XML_IO = CODE / "statable" / "xml_io.py"
LIB = CODE / "statable_gui" / "libcntrl"
RF_LIB = LIB / "role_function_library.py"
COND_LIB = LIB / "condition_library.py"
LIT_LIB = LIB / "literal_library.py"
LIB_INIT = LIB / "__init__.py"

# --- E1: xml_io.py ---
XML_OLD = (
    "try:\n"
    "    from statable_gui.libcntrl.role_function_library import (\n"
    "        RoleFunctionLibrary, RoleFunction as LibRoleFunction)\n"
    "    from statable_gui.libcntrl.condition_library import (\n"
    "        ConditionLibrary, ConditionTemplate)\n"
    "    from statable_gui.libcntrl.literal_library import (\n"
    "        LiteralLibrary, LiteralDefinition)\n"
)
XML_NEW = (
    "try:\n"
    "    from statable.shared.role_function_library import (\n"
    "        RoleFunctionLibrary, RoleFunction as LibRoleFunction)\n"
    "    from statable.shared.condition_library import (\n"
    "        ConditionLibrary, ConditionTemplate)\n"
    "    from statable.shared.literal_library import (\n"
    "        LiteralLibrary, LiteralDefinition)\n"
)

# --- E2-E4: stub files ---
STUB_HEADER = (
    '"""[v3.0 / G-1a] Backward-compat shim.\n\n'
    'Content moved to: statable.shared.{mod}\n\n'
    'Old imports under ``statable_gui.libcntrl`` keep working via re-export.\n'
    'New code should import from ``statable.shared`` instead.\n"""\n'
)

STUB_RF = STUB_HEADER.format(mod="role_function_library") + (
    "from statable.shared.role_function_library import (  # noqa: F401\n"
    "    RoleFunction,\n"
    "    RoleFunctionLibrary,\n"
    ")\n\n"
    '__all__ = ["RoleFunction", "RoleFunctionLibrary"]\n'
)

STUB_COND = STUB_HEADER.format(mod="condition_library") + (
    "from statable.shared.condition_library import (  # noqa: F401\n"
    "    ConditionLibrary,\n"
    "    ConditionTemplate,\n"
    ")\n\n"
    '__all__ = ["ConditionLibrary", "ConditionTemplate"]\n'
)

STUB_LIT = STUB_HEADER.format(mod="literal_library") + (
    "from statable.shared.literal_library import (  # noqa: F401\n"
    "    LiteralDefinition,\n"
    "    LiteralLibrary,\n"
    ")\n\n"
    '__all__ = ["LiteralDefinition", "LiteralLibrary"]\n'
)

STUB_INIT = (
    '"""[v3.0 / G-1a] Backward-compat shim for statable_gui.libcntrl.\n\n'
    'All shared library classes now live in ``statable.shared``.\n'
    'This package re-exports them for backward compatibility.\n"""\n\n'
    "from statable.shared import (  # noqa: F401\n"
    "    RoleFunctionLibrary,\n"
    "    RoleFunction,\n"
    "    ConditionLibrary,\n"
    "    ConditionTemplate,\n"
    "    LiteralLibrary,\n"
    "    LiteralDefinition,\n"
    ")\n\n"
    "__all__ = [\n"
    '    "RoleFunctionLibrary",\n'
    '    "RoleFunction",\n'
    '    "ConditionLibrary",\n'
    '    "ConditionTemplate",\n'
    '    "LiteralLibrary",\n'
    '    "LiteralDefinition",\n'
    "]\n"
)


def _hdr(mode: str) -> None:
    print("=" * 70)
    print(f"  patch_v3_0_g1a2_rewire  [{mode}]")
    print("=" * 70)


def _backup_once(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak_g1a2")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Backup: {bak.name}")


def _write(path: Path, new_content: str, apply: bool,
           tag: str, skip_if: str) -> int:
    rel = path.relative_to(CODE.parent)
    if not path.exists():
        print(f"[FAIL] {tag}: not found: {rel}")
        return 1
    text = path.read_text(encoding="utf-8")
    if skip_if in text:
        print(f"[SKIP] {tag}: already applied")
        return 0
    print(f"[APPLY] {tag}")
    if not apply:
        return 0
    _backup_once(path)
    path.write_text(new_content, encoding="utf-8")
    print(f"[DONE] {rel} rewritten ({len(new_content)} chars)")
    return 0


def edit_xml_io(apply: bool) -> int:
    rel = XML_IO.relative_to(CODE.parent)
    if not XML_IO.exists():
        print(f"[FAIL] E1: not found: {rel}")
        return 1
    text = XML_IO.read_text(encoding="utf-8")
    if "from statable.shared.role_function_library" in text:
        print("[SKIP] E1 xml_io.py: already rewired")
        return 0
    n = text.count(XML_OLD)
    if n != 1:
        print(f"[FAIL] E1 xml_io.py: anchor found {n} times (expected 1)")
        return 1
    new_text = text.replace(XML_OLD, XML_NEW, 1)
    print("[APPLY] E1 xml_io.py: import from statable.shared")
    if not apply:
        return 0
    _backup_once(XML_IO)
    XML_IO.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {rel} updated ({len(text)} -> {len(new_text)} chars)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    _hdr(mode)

    rc = 0
    rc |= edit_xml_io(args.apply)
    print()
    rc |= _write(RF_LIB, STUB_RF, args.apply,
                 "E2 role_function_library.py -> stub",
                 "Content moved to: statable.shared.role_function_library")
    print()
    rc |= _write(COND_LIB, STUB_COND, args.apply,
                 "E3 condition_library.py -> stub",
                 "Content moved to: statable.shared.condition_library")
    print()
    rc |= _write(LIT_LIB, STUB_LIT, args.apply,
                 "E4 literal_library.py -> stub",
                 "Content moved to: statable.shared.literal_library")
    print()
    rc |= _write(LIB_INIT, STUB_INIT, args.apply,
                 "E5 libcntrl/__init__.py -> stub",
                 "Backward-compat shim for statable_gui.libcntrl")
    print()

    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return rc

    print("Verify:")
    print("  python -c \"import sys; sys.path.insert(0, '.'); "
          "from statable.shared import RoleFunctionLibrary; "
          "from statable_gui.libcntrl import RoleFunctionLibrary as L2; "
          "assert RoleFunctionLibrary is L2; print('OK: identity')\"")
    return rc


if __name__ == "__main__":
    sys.exit(main())
