# tests/test_v3_2_s2_signals.py
"""Test Qt signal-slot safety (v3.2.2).

Regression test for the v3.2.0 bug where `open_project(filepath=None)`
received Qt's `triggered(bool)` argument, resulting in
`project_from_xml(False)` and a hang on `open(False, "rb")`.

Key insight: PySide6 auto-truncates args for slots with fixed signatures,
so most `triggered.connect(self.slot)` are safe. The bug only occurs
when the slot has an OPTIONAL parameter that receives the bool.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    passed = 0
    failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"[PASS] {name}")
        else:
            failed += 1
            print(f"[FAIL] {name}")

    # ================================================================
    # T1: open_project normalizes bool arguments
    # ================================================================
    print("=" * 70)
    print("  T1: open_project(bool) normalization")
    print("=" * 70)

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)

        from statable_gui.main_window import MainWindow

        win = MainWindow()

        import statable_gui.main_window as mw_mod
        original_pfx = mw_mod.project_from_xml
        called_with = []

        def fake_pfx(path):
            called_with.append(path)
            raise RuntimeError("TEST_STOP")

        mw_mod.project_from_xml = fake_pfx

        from PySide6.QtWidgets import QFileDialog
        original_dialog = QFileDialog.getOpenFileName
        QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ("", ""))

        try:
            win.open_project(False)
            check("open_project(False) does not hang", True)
        except Exception as e:
            check(f"open_project(False) raised: {e}", False)

        check("project_from_xml not called with False",
              False not in called_with)

        called_with.clear()
        try:
            win.open_project(True)
            check("open_project(True) does not hang", True)
        except Exception as e:
            check(f"open_project(True) raised: {e}", False)
        check("project_from_xml not called with True",
              True not in called_with)

        mw_mod.project_from_xml = original_pfx
        QFileDialog.getOpenFileName = original_dialog

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        check(f"T1 setup failed: {e}", False)

    # ================================================================
    # T2: open_project is connected via lambda (the actual bug)
    # ================================================================
    print()
    print("=" * 70)
    print("  T2: open_project is lambda-wrapped")
    print("=" * 70)

    mw_path = Path(__file__).parent.parent / "statable_gui" / "main_window.py"
    src = mw_path.read_text(encoding="utf-8")

    # The bug: `triggered.connect(self.open_project)` without lambda
    # would pass triggered(bool) as filepath.
    # FIX: must use `triggered.connect(lambda: self.open_project())`
    bug_pattern = re.compile(
        r'triggered\.connect\(\s*self\.open_project\s*\)'
    )
    check("open_project not connected without lambda",
          not bug_pattern.search(src))

    fix_pattern = re.compile(
        r'triggered\.connect\(\s*lambda\s*:\s*self\.open_project\(\)\s*\)'
    )
    check("open_project connected via lambda",
          bool(fix_pattern.search(src)))

    # ================================================================
    # T3: open_project has bool guard in body
    # ================================================================
    print()
    print("=" * 70)
    print("  T3: open_project has bool normalization guard")
    print("=" * 70)

    check("open_project has isinstance(filepath, bool) guard",
          "isinstance(filepath, bool)" in src)

    # Verify that the signature accepts Optional[str]
    check("open_project signature has filepath parameter",
          re.search(r'def open_project\(self,\s*filepath', src) is not None)

    # ================================================================
    # Summary
    # ================================================================
    print()
    print("=" * 70)
    print(f"  TOTAL: {passed + failed}   PASSED: {passed}   FAILED: {failed}")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    os._exit(main())