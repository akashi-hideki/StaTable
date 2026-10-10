"""patch_main_filelog.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "eclipse_installer" / "__main__.py"
t = M.read_text(encoding="utf-8")

old = 'from __future__ import annotations\n\nimport sys\n'
new = (
    'from __future__ import annotations\n\n'
    'import sys\n'
    '\n'
    '# PyInstaller debug: log startup to file\n'
    'try:\n'
    '    with open(r"C:\\tmp\\eclipse_installer_startup.log", "a", encoding="utf-8") as _f:\n'
    '        _f.write(f"[startup] __main__ entered, argv={sys.argv}\\n")\n'
    'except Exception:\n'
    '    pass\n'
)
if old not in t:
    raise SystemExit("[FAIL] anchor not found")
t = t.replace(old, new, 1)
M.write_text(t, encoding="utf-8")
print(f"[OK] {M}")
