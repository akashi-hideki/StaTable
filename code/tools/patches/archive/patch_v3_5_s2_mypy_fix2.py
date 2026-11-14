"""v3.5.0 S-2 Phase 1a: final smoke.py mypy cleanup (setattr-based patching)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"

OLD = '''    def _patch_dialogs(self) -> None:
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
        except ImportError:
            return
        QFileDialog.getOpenFileName = staticmethod(  # type: ignore[method-assign]
            lambda *a, **k: ("", ""))
        QFileDialog.getSaveFileName = staticmethod(  # type: ignore[method-assign]
            lambda *a, **k: ("", ""))
        QFileDialog.getExistingDirectory = staticmethod(  # type: ignore[method-assign]
            lambda *a, **k: "")
        QMessageBox.information = staticmethod(  # type: ignore[method-assign]
            lambda *a, **k: None)
        QMessageBox.warning = staticmethod(  # type: ignore[method-assign]
            lambda *a, **k: None)
        QMessageBox.critical = staticmethod(  # type: ignore[method-assign]
            lambda *a, **k: None)
        QMessageBox.question = staticmethod(  # type: ignore[method-assign]
            lambda *a, **k: QMessageBox.StandardButton.Yes)'''

NEW = '''    def _patch_dialogs(self) -> None:
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
        except ImportError:
            return
        # Use setattr() so mypy does not complain about assigning
        # to bound methods (the signatures differ by design here).
        setattr(QFileDialog, "getOpenFileName",
                staticmethod(lambda *a, **k: ("", "")))
        setattr(QFileDialog, "getSaveFileName",
                staticmethod(lambda *a, **k: ("", "")))
        setattr(QFileDialog, "getExistingDirectory",
                staticmethod(lambda *a, **k: ""))
        setattr(QMessageBox, "information",
                staticmethod(lambda *a, **k: None))
        setattr(QMessageBox, "warning",
                staticmethod(lambda *a, **k: None))
        setattr(QMessageBox, "critical",
                staticmethod(lambda *a, **k: None))
        setattr(QMessageBox, "question",
                staticmethod(lambda *a, **k:
                             QMessageBox.StandardButton.Yes))'''

OLD_L3 = '''            try:
                from PySide6.QtWidgets import QFileDialog
                QFileDialog.getSaveFileName = staticmethod(  # type: ignore[method-assign]
                    lambda *a, **k: (target, ""))
                QFileDialog.getOpenFileName = staticmethod(  # type: ignore[method-assign]
                    lambda *a, **k: (target, ""))'''

NEW_L3 = '''            try:
                from PySide6.QtWidgets import QFileDialog
                setattr(QFileDialog, "getSaveFileName",
                        staticmethod(lambda *a, **k: (target, "")))
                setattr(QFileDialog, "getOpenFileName",
                        staticmethod(lambda *a, **k: (target, "")))'''

p = CODE / "statable" / "smoke.py"
txt = p.read_text(encoding="utf-8")
for old, new, label in [(OLD, NEW, "_patch_dialogs"),
                        (OLD_L3, NEW_L3, "L3 patch")]:
    if old not in txt:
        print(f"[FAIL] pattern not found: {label}")
        sys.exit(1)
    txt = txt.replace(old, new, 1)
p.write_text(txt, encoding="utf-8")
print("  patched: smoke.py (setattr-based monkeypatching)")

# Also remove the now-unused pycparser override section
pyproject = CODE / "pyproject.toml"
ptxt = pyproject.read_text(encoding="utf-8")
unused = """
[[tool.mypy.overrides]]
module = [
    "PySide6.*",
    "pycparser.*",
]
ignore_missing_imports = true
"""
if unused in ptxt:
    ptxt = ptxt.replace(unused, "\n", 1)
    pyproject.write_text(ptxt, encoding="utf-8")
    print("  cleaned: pyproject.toml (removed unused PySide6/pycparser override)")

print()
print("[OK] done. Now run:")
print("     mypy statable statable_gui codegen 2>&1 | Tee-Object mypy_report.txt | Select-Object -Last 3")