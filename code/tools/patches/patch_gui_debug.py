"""patch_gui_debug.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "eclipse_installer" / "gui.py"
t = GUI.read_text(encoding="utf-8")

old = '''def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    dlg = InstallDialog()
    dlg.show()
    return app.exec()'''

new = '''def main() -> int:
    print("[DBG] gui.main() entered", file=sys.stderr, flush=True)
    import PySide6
    print(f"[DBG] PySide6 file: {PySide6.__file__}", file=sys.stderr, flush=True)
    print(f"[DBG] Qt plugin path: {__import__('PySide6.QtCore', fromlist=['QLibraryInfo']).QLibraryInfo.path(__import__('PySide6.QtCore', fromlist=['QLibraryInfo']).QLibraryInfo.LibraryPath.PluginsPath)}", file=sys.stderr, flush=True)
    app = QApplication.instance() or QApplication(sys.argv)
    print(f"[DBG] QApplication: {app}", file=sys.stderr, flush=True)
    dlg = InstallDialog()
    print(f"[DBG] Dialog created", file=sys.stderr, flush=True)
    dlg.show()
    print(f"[DBG] Dialog shown, entering exec()", file=sys.stderr, flush=True)
    rc = app.exec()
    print(f"[DBG] app.exec() returned: {rc}", file=sys.stderr, flush=True)
    return rc'''

if old not in t:
    raise SystemExit("[FAIL] anchor not found")
t = t.replace(old, new, 1)
GUI.write_text(t, encoding="utf-8")
print(f"[OK] patched {GUI}")
