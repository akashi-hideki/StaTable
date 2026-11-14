"""fix_core_duplicate_settings.py

Remove duplicate _write_template calls for settings/* files
(L154-157 in core.py).
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "eclipse_installer" / "core.py"
t = CORE.read_text(encoding="utf-8")

# Remove the SECOND pair (duplicate)
old = '''        _write_template("settings/org.eclipse.core.resources.prefs",
                        root / ".settings" / "org.eclipse.core.resources.prefs",
                        opts.overwrite_scaffolding, res, repls)
        _write_template("settings/language.settings.xml",
                        root / ".settings" / "language.settings.xml",
                        opts.overwrite_scaffolding, res, repls)
        _write_template("settings/org.eclipse.core.resources.prefs",
                        root / ".settings" / "org.eclipse.core.resources.prefs",
                        opts.overwrite_scaffolding, res, repls)
        _write_template("settings/language.settings.xml",
                        root / ".settings" / "language.settings.xml",
                        opts.overwrite_scaffolding, res, repls)
'''

new = '''        _write_template("settings/org.eclipse.core.resources.prefs",
                        root / ".settings" / "org.eclipse.core.resources.prefs",
                        opts.overwrite_scaffolding, res, repls)
        _write_template("settings/language.settings.xml",
                        root / ".settings" / "language.settings.xml",
                        opts.overwrite_scaffolding, res, repls)
'''

n = t.count(old)
if n != 1:
    raise SystemExit(f"[FAIL] duplicate block count={n} (expected 1)")
t = t.replace(old, new, 1)
CORE.write_text(t, encoding="utf-8")
print(f"[OK] removed duplicate settings block from {CORE}")
