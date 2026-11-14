#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p11c_handler.py

Add the missing _on_comm_monitor_toggled method + state load.

Context:
  p11b added the QCheckBox UI and wired it to self._on_comm_monitor_toggled
  but the handler method itself was never added (skip check false-positive).
  Without this patch clicking the checkbox raises AttributeError.

Idempotent.
"""
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "statable_gui" / "code_generation_dialog.py"

HANDLER = (
    '\n'
    '    def _on_comm_monitor_toggled(self, checked: bool):\n'
    '        """[p11c] Sync comm_monitor checkbox to config + save."""\n'
    '        try:\n'
    '            from codegen.comm_monitor.config import (\n'
    '                CommMonitorConfig)\n'
    '            cfg = self.config_manager.get_config()\n'
    '            if getattr(cfg, "comm_monitor", None) is None:\n'
    '                cfg.comm_monitor = CommMonitorConfig()\n'
    '            cfg.comm_monitor.enabled = bool(checked)\n'
    '            self.config_manager.set_config(cfg)\n'
    '            self._save_settings()\n'
    '            logger.info(\n'
    '                f"[p11c] comm_monitor.enabled={checked}")\n'
    '        except Exception as e:\n'
    '            logger.warning(\n'
    '                f"[p11c] _on_comm_monitor_toggled failed: {e!r}")\n'
)


def patch_state_load(text: str) -> tuple[str, bool]:
    marker = "[p11c] load comm_monitor state"
    if marker in text:
        print("  [skip] state load already present")
        return text, True
    pat = re.compile(
        r'(        self\._update_info_labels\(config\)\r?\n)'
    )
    m = pat.search(text)
    if not m:
        print("  [error] _update_info_labels(config) not found")
        return text, False
    insert = (
        '        # [p11c] load comm_monitor state\n'
        '        if hasattr(self, "comm_monitor_check"):\n'
        '            _cm = getattr(config, "comm_monitor", None)\n'
        '            self.comm_monitor_check.setChecked(\n'
        '                bool(_cm and getattr(_cm, "enabled", False)))\n'
    )
    text = text[:m.end()] + insert + text[m.end():]
    print("  [patched] state load in _load_config_to_ui")
    return text, True


def patch_handler(text: str) -> tuple[str, bool]:
    if re.search(r"    def _on_comm_monitor_toggled\(", text):
        print("  [skip] handler already defined")
        return text, True
    # Insert handler right after _open_settings_dialog method (which we
    # know exists), before its next top-level def.
    pat = re.compile(
        r'(\n    def _open_settings_dialog\(self\):.*?\n(?=    \S|\Z))',
        re.DOTALL,
    )
    m = pat.search(text)
    if not m:
        print("  [error] _open_settings_dialog not found for anchor")
        return text, False
    text = text[:m.end()] + HANDLER + text[m.end():]
    print("  [patched] _on_comm_monitor_toggled method")
    return text, True


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p11c_handler ===")
    if not TARGET.is_file():
        print(f"[error] not found: {TARGET}", file=sys.stderr)
        return 1
    text = TARGET.read_text(encoding="utf-8")
    ok = True
    text, s = patch_state_load(text); ok = ok and s
    text, s = patch_handler(text);    ok = ok and s
    if not ok:
        print("=== FAILED (file NOT written) ===", file=sys.stderr)
        return 1
    TARGET.write_text(text, encoding="utf-8")
    print("=== done (file written) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())