#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p11b_visible.py

Add visible comm_monitor checkbox to CodeGenerationDialog.

Applies 3 things idempotently:
  1. QCheckBox in QtWidgets import
  2. checkbox UI in _setup_ui (3 fallback anchors)
  3. state load + toggle handler in _load_config_to_ui
"""
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "statable_gui" / "code_generation_dialog.py"

CHECKBOX_UI = (
    '        # [p11] comm_monitor toggle (visible in main dialog)\n'
    '        self.comm_monitor_check = QCheckBox(\n'
    '            self.tr("Generate comm_monitor code (ASCII GET protocol)"))\n'
    '        self.comm_monitor_check.setToolTip(\n'
    '            self.tr("Generates statable_comm_*.c/h files."))\n'
    '        self.comm_monitor_check.toggled.connect(\n'
    '            self._on_comm_monitor_toggled)\n'
    '        info_layout.addRow("Comm monitor:", self.comm_monitor_check)\n'
    '\n'
)

HANDLER_AND_LOAD = (
    '        # [p11] load comm_monitor state into checkbox\n'
    '        if hasattr(self, "comm_monitor_check"):\n'
    '            cm = getattr(config, "comm_monitor", None)\n'
    '            self.comm_monitor_check.setChecked(\n'
    '                bool(cm and getattr(cm, "enabled", False)))\n'
    '\n'
    '    def _on_comm_monitor_toggled(self, checked: bool):\n'
    '        """[p11] Sync comm_monitor checkbox to config + save."""\n'
    '        try:\n'
    '            from codegen.comm_monitor.config import (\n'
    '                CommMonitorConfig)\n'
    '            cfg = self.config_manager.get_config()\n'
    '            if getattr(cfg, "comm_monitor", None) is None:\n'
    '                cfg.comm_monitor = CommMonitorConfig()\n'
    '            cfg.comm_monitor.enabled = bool(checked)\n'
    '            self.config_manager.set_config(cfg)\n'
    '            self._save_settings()\n'
    '            logger.info(f"[p11] comm_monitor.enabled={checked}")\n'
    '        except Exception as e:\n'
    '            logger.warning(\n'
    '                f"[p11] _on_comm_monitor_toggled failed: {e!r}")\n'
)


def patch_import(text: str) -> tuple[str, bool]:
    if "QCheckBox" in text.split("\n\n")[0] or "QCheckBox," in text[:2000]:
        print("  [skip] QCheckBox already imported")
        return text, True
    # multi-line form
    m = re.search(r"from PySide6\.QtWidgets import \(\s*\n([^)]+)\)", text)
    if m:
        inner = m.group(1).rstrip()
        if "QCheckBox" not in inner:
            new_block = (
                "from PySide6.QtWidgets import (\n"
                + inner + ",\n    QCheckBox\n)"
            )
            text = text[:m.start()] + new_block + text[m.end():]
            print("  [patched] QCheckBox in multi-line import")
            return text, True
    # single-line form
    m = re.search(r"from PySide6\.QtWidgets import ([^\n(]+)\n", text)
    if m and "QCheckBox" not in m.group(1):
        new_line = "from PySide6.QtWidgets import QCheckBox, " + m.group(1).strip() + "\n"
        text = text.replace(m.group(0), new_line, 1)
        print("  [patched] QCheckBox in single-line import")
        return text, True
    print("  [error] cannot patch import")
    return text, False


def patch_ui(text: str) -> tuple[str, bool]:
    if "self.comm_monitor_check" in text:
        print("  [skip] checkbox already present")
        return text, True
    # 3 fallback anchors (regex, tolerant to \r and trailing ws)
    anchors = [
        # A: insert after settings_btn addRow
        (re.compile(r'(        info_layout\.addRow\("", self\.settings_btn\)\r?\n)'),
         lambda m: m.group(1) + '\n' + CHECKBOX_UI.rstrip('\n') + '\n'),
        # B: insert before main_layout.addWidget(info_group) (first occurrence)
        (re.compile(r'(        main_layout\.addWidget\(info_group\))'),
         lambda m: CHECKBOX_UI + m.group(1)),
        # C: insert after merge_label addRow
        (re.compile(r'(        info_layout\.addRow\("Merge:", self\.merge_label\)\r?\n)'),
         lambda m: m.group(1) + '\n' + CHECKBOX_UI.rstrip('\n') + '\n'),
    ]
    for i, (pat, fn) in enumerate(anchors, 1):
        if pat.search(text):
            text = pat.sub(fn, text, count=1)
            print(f"  [patched] checkbox UI via strategy {i}")
            return text, True
    print("  [error] no UI anchor matched")
    return text, False


def patch_load_and_handler(text: str) -> tuple[str, bool]:
    if "_on_comm_monitor_toggled" in text:
        print("  [skip] handler already present")
        return text, True
    # Insert after `self._update_info_labels(config)` inside _load_config_to_ui
    m = re.search(
        r'(        self\._update_info_labels\(config\)\r?\n)',
        text,
    )
    if m:
        text = text[:m.end()] + '\n' + HANDLER_AND_LOAD + text[m.end():]
        print("  [patched] state load + toggle handler")
        return text, True
    print("  [error] _load_config_to_ui anchor not found")
    return text, False


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p11b_visible ===")
    if not TARGET.is_file():
        print(f"[error] not found: {TARGET}", file=sys.stderr)
        return 1
    text = TARGET.read_text(encoding="utf-8")
    ok = True

    text, s = patch_import(text);         ok = ok and s
    text, s = patch_ui(text);             ok = ok and s
    text, s = patch_load_and_handler(text); ok = ok and s

    if not ok:
        print("=== FAILED (file NOT written) ===", file=sys.stderr)
        return 1

    TARGET.write_text(text, encoding="utf-8")
    print("=== done (file written) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())