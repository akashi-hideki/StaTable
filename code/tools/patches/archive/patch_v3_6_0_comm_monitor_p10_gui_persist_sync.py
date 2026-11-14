#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p10_gui_persist_sync.py

Fix: GUI menu-path settings changes are lost when opening the code
generation dialog.

Root cause:
  - main_window.open_code_generation_settings() updates config_manager
    in memory when user clicks OK on settings dialog.
  - However, this update is NOT persisted to the settings JSON
    (DEFAULT_SETTINGS_FILE) used by CodeGenerationDialog._load_saved_settings().
  - When user opens the code generation dialog,
    CodeGenerationDialog.__init__ -> _load_saved_settings() reads the
    OLD JSON and overrides config_manager (incl. comm_monitor.enabled)
    back to the stale value.

Fix:
  - After settings dialog returns Accepted in
    main_window.open_code_generation_settings(), persist the current
    config_manager state to JSON (same schema as _save_settings).
  - Then CodeGenerationDialog._load_saved_settings() reads fresh state
    and no longer overrides it.

Idempotent.
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
MAINWIN = CODE / "statable_gui" / "main_window.py"

MARKER = "# [p10] persist settings to JSON"


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p10_gui_persist_sync ===")
    if not MAINWIN.is_file():
        print(f"[error] not found: {MAINWIN}", file=sys.stderr)
        return 1
    text = MAINWIN.read_text(encoding="utf-8")
    if MARKER in text:
        print(f"  [skip] already patched: {MAINWIN.name}")
        return 0

    old = (
        "    def open_code_generation_settings(self):\n"
        "        StaTableLogger.debug(\n"
        "            \"MainWindow.open_code_generation_settings called\")\n"
        "        dialog = CodeGenerationSettingsDialog(\n"
        "            config_manager=self.config_manager,\n"
        "            parent=self)\n"
        "        dialog.exec()\n"
        "        StaTableLogger.debug(\n"
        "            \"CodeGenerationSettingsDialog closed\")"
    )
    new = (
        "    def open_code_generation_settings(self):\n"
        "        StaTableLogger.debug(\n"
        "            \"MainWindow.open_code_generation_settings called\")\n"
        "        dialog = CodeGenerationSettingsDialog(\n"
        "            config_manager=self.config_manager,\n"
        "            parent=self)\n"
        "        if dialog.exec() == QDialog.DialogCode.Accepted:\n"
        "            # [p10] persist settings to JSON\n"
        "            self._persist_generation_settings_json()\n"
        "        StaTableLogger.debug(\n"
        "            \"CodeGenerationSettingsDialog closed\")\n"
        "\n"
        "    def _persist_generation_settings_json(self):\n"
        "        \"\"\"Persist config_manager state to DEFAULT_SETTINGS_FILE.\n"
        "\n"
        "        CodeGenerationDialog._load_saved_settings() reads this\n"
        "        JSON and would otherwise override fresh in-memory state\n"
        "        with stale values. Saving after menu-path settings\n"
        "        changes keeps memory and JSON in sync.\n"
        "        \"\"\"\n"
        "        import json as _json\n"
        "        from dataclasses import asdict as _asdict\n"
        "        try:\n"
        "            from .code_generation_dialog import (\n"
        "                DEFAULT_SETTINGS_FILE)\n"
        "        except ImportError:\n"
        "            from code_generation_dialog import (\n"
        "                DEFAULT_SETTINGS_FILE)\n"
        "        try:\n"
        "            cfg = self.config_manager.get_config()\n"
        "            data = {\n"
        "                'output_directory': cfg.output_directory,\n"
        "                'generation_style': cfg.generation_style,\n"
        "                'os_type': cfg.os_type,\n"
        "                'save_with_merge': cfg.save_with_merge,\n"
        "                'comm_monitor': (\n"
        "                    _asdict(cfg.comm_monitor)\n"
        "                    if getattr(cfg, 'comm_monitor', None)\n"
        "                    else None),\n"
        "            }\n"
        "            d = os.path.dirname(DEFAULT_SETTINGS_FILE)\n"
        "            if d:\n"
        "                os.makedirs(d, exist_ok=True)\n"
        "            with open(DEFAULT_SETTINGS_FILE, 'w',\n"
        "                      encoding='utf-8') as f:\n"
        "                _json.dump(data, f, ensure_ascii=False,\n"
        "                           indent=2)\n"
        "            StaTableLogger.debug(\n"
        "                f\"[p10] persisted settings: \"\n"
        "                f\"comm_monitor.enabled=\"\n"
        "                f\"{getattr(getattr(cfg,'comm_monitor',None),'enabled',None)}\")\n"
        "        except Exception as e:\n"
        "            StaTableLogger.debug(\n"
        "                f\"[p10] persist settings failed: {e!r}\")"
    )
    if old not in text:
        print("[error] open_code_generation_settings anchor not found",
              file=sys.stderr)
        return 1
    text = text.replace(old, new, 1)
    print("  [patched] open_code_generation_settings persists JSON")

    # Sanity: QDialog should be imported
    if "QDialog" not in text.split("from PySide6.QtWidgets import")[-1][:500]:
        print("[warn] QDialog may not be imported; verify manually")

    MAINWIN.write_text(text, encoding="utf-8")
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())