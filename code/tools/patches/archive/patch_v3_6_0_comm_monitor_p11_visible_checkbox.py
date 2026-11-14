#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p11_visible_checkbox.py

Add a visible comm_monitor checkbox directly to CodeGenerationDialog.

Root cause:
  'Generate comm_monitor code' checkbox lives only in
  CodeGenerationSettingsDialog (accessed via 'Advanced settings...').
  Users open CodeGenerationDialog and click 'Code generation' without
  ever discovering it, so statable_comm_*.c/h are silently omitted.

Fix:
  1. Import QCheckBox.
  2. Add QCheckBox('Comm monitor:') to _setup_ui's info_group.
  3. Wire it to config via _on_comm_monitor_toggled (auto-saves JSON).
  4. Load state in _load_config_to_ui.

Idempotent.
"""
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "statable_gui" / "code_generation_dialog.py"


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p11_visible_checkbox ===")
    if not TARGET.is_file():
        print(f"[error] not found: {TARGET}", file=sys.stderr)
        return 1
    text = TARGET.read_text(encoding="utf-8")
    if "self.comm_monitor_check" in text:
        print(f"  [skip] already patched: {TARGET.name}")
        return 0

    # 1) Import QCheckBox
    old_import = "    QProgressBar, QLineEdit\n)"
    new_import = "    QProgressBar, QLineEdit, QCheckBox\n)"
    if old_import in text:
        text = text.replace(old_import, new_import, 1)
        print("  [patched] multi-line QtWidgets import")
    else:
        m = re.search(r"from PySide6\.QtWidgets import ([^\n]+)", text)
        if m and "QCheckBox" not in m.group(1):
            text = text.replace(
                "from PySide6.QtWidgets import " + m.group(1),
                "from PySide6.QtWidgets import QCheckBox, " + m.group(1),
                1,
            )
            print("  [patched] single-line QtWidgets import")
        else:
            print("  [warn] could not patch import; verify manually")

    # 2) Add checkbox in _setup_ui
    old_ui = (
        "        # Advanced settings button\n"
        "        self.settings_btn = QPushButton(self.tr(\"Advanced settings...\"))\n"
        "        self.settings_btn.clicked.connect(\n"
        "            self._open_settings_dialog)\n"
        "        info_layout.addRow(\"\", self.settings_btn)\n"
        "\n"
        "        main_layout.addWidget(info_group)"
    )
    new_ui = (
        "        # CommMonitor toggle (visible in main dialog)\n"
        "        self.comm_monitor_check = QCheckBox(\n"
        "            self.tr(\"Generate comm_monitor code (ASCII GET protocol)\"))\n"
        "        self.comm_monitor_check.setToolTip(\n"
        "            self.tr(\"Generates statable_comm_*.c/h files.\\n\"\n"
        "                    \"UART ISR + TX hook must be wired in user code.\"))\n"
        "        self.comm_monitor_check.toggled.connect(\n"
        "            self._on_comm_monitor_toggled)\n"
        "        info_layout.addRow(\"Comm monitor:\",\n"
        "                          self.comm_monitor_check)\n"
        "\n"
        "        # Advanced settings button\n"
        "        self.settings_btn = QPushButton(self.tr(\"Advanced settings...\"))\n"
        "        self.settings_btn.clicked.connect(\n"
        "            self._open_settings_dialog)\n"
        "        info_layout.addRow(\"\", self.settings_btn)\n"
        "\n"
        "        main_layout.addWidget(info_group)"
    )
    if old_ui not in text:
        print("[error] _setup_ui anchor not found", file=sys.stderr)
        return 1
    text = text.replace(old_ui, new_ui, 1)
    print("  [patched] _setup_ui adds visible checkbox")

    # 3) Load state + add toggle handler
    old_load = (
        "        idx = self.style_combo.findData(\n"
        "            config.generation_style)\n"
        "        if idx >= 0:\n"
        "            self.style_combo.setCurrentIndex(idx)\n"
        "        self._update_info_labels(config)"
    )
    new_load = (
        "        idx = self.style_combo.findData(\n"
        "            config.generation_style)\n"
        "        if idx >= 0:\n"
        "            self.style_combo.setCurrentIndex(idx)\n"
        "        # [p11] load comm_monitor state into checkbox\n"
        "        if hasattr(self, 'comm_monitor_check'):\n"
        "            cm = getattr(config, 'comm_monitor', None)\n"
        "            self.comm_monitor_check.setChecked(\n"
        "                bool(cm and getattr(cm, 'enabled', False)))\n"
        "        self._update_info_labels(config)\n"
        "\n"
        "    def _on_comm_monitor_toggled(self, checked: bool):\n"
        "        \"\"\"[p11] Sync comm_monitor checkbox to config + save.\"\"\"\n"
        "        try:\n"
        "            from codegen.comm_monitor.config import (\n"
        "                CommMonitorConfig)\n"
        "            cfg = self.config_manager.get_config()\n"
        "            if getattr(cfg, 'comm_monitor', None) is None:\n"
        "                cfg.comm_monitor = CommMonitorConfig()\n"
        "            cfg.comm_monitor.enabled = bool(checked)\n"
        "            self.config_manager.set_config(cfg)\n"
        "            self._save_settings()\n"
        "            logger.info(\n"
        "                f'[p11] comm_monitor.enabled={checked}')\n"
        "        except Exception as e:\n"
        "            logger.warning(\n"
        "                f'[p11] _on_comm_monitor_toggled failed: {e!r}')"
    )
    if old_load not in text:
        print("[error] _load_config_to_ui anchor not found", file=sys.stderr)
        return 1
    text = text.replace(old_load, new_load, 1)
    print("  [patched] _load_config_to_ui + _on_comm_monitor_toggled")

    TARGET.write_text(text, encoding="utf-8")
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())