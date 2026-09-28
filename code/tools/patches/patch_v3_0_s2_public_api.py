# code/tools/patches/patch_v3_0_s2_public_api.py
"""
Phase S-2 patch for v3.0: public API definition.

Targets:
  - code/statable/__init__.py           (E1)
  - code/codegen/__init__.py            (E2, E3)
  - code/codegen/validate/__init__.py   (E4)

Edits:
  E1. statable.__all__: add '__version__'
  E2. codegen.__all__: add 'validate', '__version__'
  E3. codegen.__getattr__: handle 'validate'
  E4. codegen.validate: export ResponseValidator / ResponseValidationResult

Safety:
  - EOL-agnostic anchors (handles CRLF / LF)
  - Trailing-newline-agnostic (anchors end before EOF newline)
  - Idempotent (skips if marker already present)
  - Backup once (.bak_s2)
  - Literal anchors; each must appear exactly once

Usage:
    cd code
    python tools\patches\patch_v3_0_s2_public_api.py
    python tools\patches\patch_v3_0_s2_public_api.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent

STATABLE_INIT = CODE / "statable" / "__init__.py"
CODEGEN_INIT = CODE / "codegen" / "__init__.py"
VALIDATE_INIT = CODE / "codegen" / "validate" / "__init__.py"


def _hdr(mode: str) -> None:
    print("=" * 70)
    print(f"  patch_v3_0_s2_public_api  [{mode}]")
    print("=" * 70)


def _backup_once(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak_s2")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Backup: {bak.name}")


def _detect_eol(text: str) -> str:
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    return "\r\n" if crlf > 0 and crlf >= lf else "\n"


def _apply_replacement(
    text: str,
    old_lf: str,
    new_lf: str,
    tag: str,
    skip_if: str | None = None,
) -> tuple[str, bool, bool]:
    eol = _detect_eol(text)
    old = old_lf.replace("\n", eol)
    new = new_lf.replace("\n", eol)
    skip = skip_if.replace("\n", eol) if skip_if else None

    if skip is not None and skip in text:
        print(f"[SKIP] {tag}: already applied")
        return text, False, True
    n = text.count(old)
    if n == 0:
        print(f"[FAIL] {tag}: anchor not found (eol={eol!r})")
        return text, False, False
    if n > 1:
        print(f"[FAIL] {tag}: anchor found {n} times")
        return text, False, False
    print(f"[APPLY] {tag}")
    return text.replace(old, new, 1), True, True


def edit_statable(apply: bool) -> int:
    path = STATABLE_INIT
    rel = path.relative_to(CODE.parent)
    if not path.exists():
        print(f"[FAIL] not found: {rel}")
        return 1
    text = path.read_text(encoding="utf-8")
    old = "    'StructMemberDef',\n]"
    new = (
        "    'StructMemberDef',\n"
        "    # version\n"
        "    '__version__',\n"
        "]"
    )
    text, changed, ok = _apply_replacement(
        text, old, new, "E1 statable.__all__ += __version__",
        skip_if="    '__version__',\n",
    )
    if not ok:
        return 1
    if not changed:
        return 0
    if not apply:
        return 0
    _backup_once(path)
    path.write_text(text, encoding="utf-8")
    print(f"[DONE] {rel} updated")
    return 0


def edit_codegen_all(apply: bool) -> int:
    path = CODEGEN_INIT
    rel = path.relative_to(CODE.parent)
    if not path.exists():
        print(f"[FAIL] not found: {rel}")
        return 1
    text = path.read_text(encoding="utf-8")
    old = (
        "__all__ = [\n"
        "    'CCodeGenerator',\n"
        "    'CodeGenerationConfig',\n"
        "    'ConfigManager',\n"
        "]"
    )
    new = (
        "__all__ = [\n"
        "    'CCodeGenerator',\n"
        "    'CodeGenerationConfig',\n"
        "    'ConfigManager',\n"
        "    'validate',\n"
        "    '__version__',\n"
        "]"
    )
    text, changed, ok = _apply_replacement(
        text, old, new, "E2 codegen.__all__ += validate, __version__",
        skip_if="    'validate',\n    '__version__',\n",
    )
    if not ok:
        return 1
    if not changed:
        return 0
    if not apply:
        return 0
    _backup_once(path)
    path.write_text(text, encoding="utf-8")
    print(f"[DONE] {rel} updated (E2)")
    return 0


def edit_codegen_getattr(apply: bool) -> int:
    path = CODEGEN_INIT
    rel = path.relative_to(CODE.parent)
    text = path.read_text(encoding="utf-8")
    old = (
        "    if name == 'ConfigManager':\n"
        "        from .config import ConfigManager\n"
        "        return ConfigManager\n"
    )
    new = old + (
        "    if name == 'validate':\n"
        "        import importlib\n"
        "        return importlib.import_module('.validate', __name__)\n"
    )
    text, changed, ok = _apply_replacement(
        text, old, new, "E3 codegen.__getattr__ handles 'validate'",
        skip_if="    if name == 'validate':\n",
    )
    if not ok:
        return 1
    if not changed:
        return 0
    if not apply:
        return 0
    _backup_once(path)
    path.write_text(text, encoding="utf-8")
    print(f"[DONE] {rel} updated (E3)")
    return 0


def edit_validate(apply: bool) -> int:
    path = VALIDATE_INIT
    rel = path.relative_to(CODE.parent)
    if not path.exists():
        print(f"[FAIL] not found: {rel}")
        return 1
    text = path.read_text(encoding="utf-8")
    old_imp = "from .clipboard_manager import ClipboardManager\n"
    new_imp = (
        "from .clipboard_manager import ClipboardManager\n"
        "from .response_validator import (\n"
        "    ResponseValidator,\n"
        "    ResponseValidationResult,\n"
        ")\n"
    )
    old_all = "    'ClipboardManager',\n]"
    new_all = (
        "    'ClipboardManager',\n"
        "    'ResponseValidator',\n"
        "    'ResponseValidationResult',\n"
        "]"
    )
    ok_all = True
    for tag, old, new, skip in (
        ("E4a validate import block", old_imp, new_imp,
         "from .response_validator import"),
        ("E4b validate __all__", old_all, new_all,
         "    'ResponseValidationResult',\n"),
    ):
        text, changed, ok = _apply_replacement(
            text, old, new, tag, skip_if=skip)
        if not ok:
            ok_all = False
    if not ok_all:
        return 1
    if not apply:
        return 0
    _backup_once(path)
    path.write_text(text, encoding="utf-8")
    print(f"[DONE] {rel} updated (E4)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    mode = "APPLY" if args.apply else "DRY-RUN"
    _hdr(mode)
    rc = 0
    rc |= edit_statable(args.apply)
    print()
    rc |= edit_codegen_all(args.apply)
    print()
    rc |= edit_codegen_getattr(args.apply)
    print()
    rc |= edit_validate(args.apply)
    print()
    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply to execute.")
    else:
        print("Verify:")
        print("  python tests\\test_v3_0_s2_public_api.py")
    return rc


if __name__ == "__main__":
    sys.exit(main())
