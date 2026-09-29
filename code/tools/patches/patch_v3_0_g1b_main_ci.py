# code/tools/patches/patch_v3_0_g1b_main_ci.py
r"""
Phase G-1b: friendly __main__ error + register v3.0 tests in CI.

Edits:
  E1. statable/__main__.py: try/except around PySide6 import
      with a friendly message pointing to statable[gui].
  E2. .github/workflows/check.yml: register S-1..S-4 test suites.

Usage:
    cd code
    python tools\patches\patch_v3_0_g1b_main_ci.py
    python tools\patches\patch_v3_0_g1b_main_ci.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
MAIN_PY = CODE / "statable" / "__main__.py"
CHECK_YML = CODE.parent / ".github" / "workflows" / "check.yml"

# --- E1: __main__.py rewrite ---
MAIN_NEW = '''"""Entry point for `python -m statable`.

Launches the StaTable GUI, or prints a friendly error if the
GUI extras are not installed.

    pip install statable[gui]    # to enable GUI
    python -m statable           # launch
"""
from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        sys.stderr.write(
            "error: The StaTable GUI requires PySide6.\\n"
            "       Install with:  pip install \\"statable[gui]\\"\\n"
            "       For CLI-only usage:  statable-cli --help\\n"
        )
        return 1

    try:
        from statable_gui.main_window import MainWindow
    except ImportError as exc:
        sys.stderr.write(
            f"error: Failed to import GUI module: {exc}\\n"
            "       The GUI files may be missing from the install.\\n"
        )
        return 1

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
'''

# --- E2: check.yml anchor ---
CI_OLD = (
    "      - name: Run README consistency test\n"
    "        run: |\n"
    "          python tests/test_readme_consistency.py\n"
)
CI_NEW = (
    "      - name: Run v3.0 test suites\n"
    "        run: |\n"
    "          python tests/test_v3_0_s1_packaging.py\n"
    "          python tests/test_v3_0_s2_public_api.py\n"
    "          python tests/test_v3_0_s3_cli.py\n"
    "          python tests/test_v3_0_s4_docs.py\n"
    "\n"
    "      - name: Run README consistency test\n"
    "        run: |\n"
    "          python tests/test_readme_consistency.py\n"
)


def _hdr(mode: str) -> None:
    print("=" * 70)
    print(f"  patch_v3_0_g1b_main_ci  [{mode}]")
    print("=" * 70)


def _backup_once(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak_g1b")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Backup: {bak.name}")


def edit_main(apply: bool) -> int:
    rel = MAIN_PY.relative_to(CODE.parent)
    if not MAIN_PY.exists():
        print(f"[FAIL] E1: not found: {rel}")
        return 1
    text = MAIN_PY.read_text(encoding="utf-8")
    if "pip install \\\"statable[gui]\\\"" in text or \
       "The StaTable GUI requires PySide6" in text:
        print("[SKIP] E1: already patched")
        return 0
    print("[APPLY] E1 statable/__main__.py: friendly PySide6 error")
    if not apply:
        return 0
    _backup_once(MAIN_PY)
    MAIN_PY.write_text(MAIN_NEW, encoding="utf-8")
    print(f"[DONE] {rel} rewritten ({len(MAIN_NEW)} chars)")
    return 0


def edit_check_yml(apply: bool) -> int:
    rel = CHECK_YML.relative_to(CODE.parent.parent)
    if not CHECK_YML.exists():
        print(f"[FAIL] E2: not found: {rel}")
        return 1
    text = CHECK_YML.read_text(encoding="utf-8")
    if "test_v3_0_s1_packaging.py" in text:
        print("[SKIP] E2: already registered")
        return 0
    n = text.count(CI_OLD)
    if n != 1:
        print(f"[FAIL] E2: anchor found {n} times (expected 1)")
        return 1
    new_text = text.replace(CI_OLD, CI_NEW, 1)
    print("[APPLY] E2 check.yml: register v3.0 test suites")
    if not apply:
        return 0
    _backup_once(CHECK_YML)
    CHECK_YML.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {rel} updated "
          f"({len(text)} -> {len(new_text)} chars)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    _hdr(mode)

    rc = 0
    rc |= edit_main(args.apply)
    print()
    rc |= edit_check_yml(args.apply)
    print()

    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return rc

    print("Verify:")
    print("  python -m statable")
    print("  # expect: friendly error (if no PySide6 in new process)")
    print("  Select-String -Path ..\\.github\\workflows\\check.yml "
          "-Pattern 'v3_0_s1'")
    return rc


if __name__ == "__main__":
    sys.exit(main())
