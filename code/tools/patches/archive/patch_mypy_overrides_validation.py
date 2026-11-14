"""patch_mypy_overrides_validation.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYPROJ = ROOT / "pyproject.toml"
t = PYPROJ.read_text(encoding="utf-8")

NEW_OVERRIDE = '''

# [v3.5.1 / Phase 1c] PySide6 Qt enum stubs are incomplete
# (Qt.Checked, Qt.ItemIsUserCheckable, ...). Suppress in the
# validation dialog which uses them heavily at module scope.
[[tool.mypy.overrides]]
module = ["codegen.validate.validation_dialog"]
disable_error_code = ["attr-defined", "union-attr"]
'''

if "codegen.validate.validation_dialog" in t:
    print("[SKIP] override already present")
else:
    t = t.rstrip() + "\n" + NEW_OVERRIDE
    PYPROJ.write_text(t, encoding="utf-8")
    print(f"[OK] appended override to {PYPROJ}")
