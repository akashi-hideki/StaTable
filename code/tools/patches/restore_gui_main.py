"""restore_gui_main.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUI = ROOT / "eclipse_installer" / "gui.py"
t = GUI.read_text(encoding="utf-8")

# Find the debug version of main()
import re
pattern = re.compile(
    r'def main\(\) -> int:.*?return rc\n',
    re.DOTALL,
)
new_main = '''def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    dlg = InstallDialog()
    dlg.show()
    return app.exec()
'''
t2, n = pattern.subn(new_main, t, count=1)
if n != 1:
    raise SystemExit(f"[FAIL] pattern match count={n}")
GUI.write_text(t2, encoding="utf-8")
print(f"[OK] {GUI}")
