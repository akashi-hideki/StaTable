"""patch_core_write_settings.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "eclipse_installer" / "core.py"
t = CORE.read_text(encoding="utf-8")

old = (
    '    if opts.with_eclipse_project:\n'
    '        _write_template("project.tmpl",\n'
    '                        root / ".project",\n'
    '                        opts.overwrite_scaffolding, res, repls)\n'
    '        _write_template("cproject.tmpl",\n'
    '                        root / ".cproject",\n'
    '                        opts.overwrite_scaffolding, res, repls)\n'
)
new = (
    '    if opts.with_eclipse_project:\n'
    '        _write_template("project.tmpl",\n'
    '                        root / ".project",\n'
    '                        opts.overwrite_scaffolding, res, repls)\n'
    '        _write_template("cproject.tmpl",\n'
    '                        root / ".cproject",\n'
    '                        opts.overwrite_scaffolding, res, repls)\n'
    '        _write_template("settings/org.eclipse.core.resources.prefs",\n'
    '                        root / ".settings" / "org.eclipse.core.resources.prefs",\n'
    '                        opts.overwrite_scaffolding, res, repls)\n'
    '        _write_template("settings/language.settings.xml",\n'
    '                        root / ".settings" / "language.settings.xml",\n'
    '                        opts.overwrite_scaffolding, res, repls)\n'
)
if old not in t:
    raise SystemExit("[FAIL] anchor not found")
t = t.replace(old, new, 1)
CORE.write_text(t, encoding="utf-8")
print(f"[OK] patched {CORE}")
