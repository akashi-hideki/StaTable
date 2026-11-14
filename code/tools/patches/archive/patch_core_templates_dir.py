"""patch_core_templates_dir.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "eclipse_installer" / "core.py"
t = CORE.read_text(encoding="utf-8")

old = 'TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"\n'
new = (
    '# PyInstaller: templates are bundled under sys._MEIPASS\n'
    'if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):\n'
    '    TEMPLATES_DIR = Path(sys._MEIPASS) / "eclipse_installer" / "templates"\n'
    'else:\n'
    '    TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"\n'
)
if old not in t:
    raise SystemExit("[FAIL] anchor not found")

# Ensure `import sys` exists
if "import sys\n" not in t:
    t = t.replace("import os\n", "import os\nimport sys\n", 1)

t = t.replace(old, new, 1)
CORE.write_text(t, encoding="utf-8")
print(f"[OK] {CORE}")
