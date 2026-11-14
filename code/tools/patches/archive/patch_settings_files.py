"""patch_settings_files.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S = ROOT / "eclipse_installer" / "templates" / "settings"
S.mkdir(exist_ok=True)

# org.eclipse.core.resources.prefs
(S / "org.eclipse.core.resources.prefs").write_text(
    "eclipse.preferences.version=1\n"
    "encoding/<project>=UTF-8\n",
    encoding="utf-8",
)
print(f"[OK] org.eclipse.core.resources.prefs")

# language.settings.xml - short (providers only, no config IDs)
lang = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<project>
</project>
"""
(S / "language.settings.xml").write_text(lang, encoding="utf-8")
print(f"[OK] language.settings.xml")
