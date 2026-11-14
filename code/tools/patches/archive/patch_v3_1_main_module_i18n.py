# code/tools/patches/patch_v3_1_main_module_i18n.py
r"""
v3.1: add install_translator to statable/__main__.py.

Ensures `python -m statable` applies the saved language preference
(same behavior as `python gui_main.py`).

Usage:
    cd code
    python tools\patches\patch_v3_1_main_module_i18n.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "statable" / "__main__.py"

OLD = """    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()"""

NEW = """    app = QApplication(sys.argv)

    # [v3.1] Apply saved language preference (en / zh_CN)
    try:
        from statable_gui.i18n import install_translator
        install_translator(app)
    except Exception:
        pass  # i18n is optional; fall back to English

    window = MainWindow()
    window.show()
    return app.exec()"""


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_main_module_i18n  [{mode}]")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] not found: {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8")
    if "install_translator" in text:
        print("[SKIP] already has install_translator")
        return 0

    n = text.count(OLD)
    if n != 1:
        print(f"[FAIL] anchor found {n} times (expected 1)")
        print("--- anchor:")
        print(OLD)
        return 1

    new_text = text.replace(OLD, NEW, 1)
    print("[APPLY] add install_translator to __main__.py")
    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply")
        return 0

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_i18n")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    TARGET.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {TARGET.relative_to(CODE.parent)} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())