#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p9_gui_persist.py

Fix GUI persistence of comm_monitor settings.

Root cause:
  _save_settings / _load_saved_settings in code_generation_dialog.py only
  persist {output_directory, generation_style, os_type, save_with_merge}.
  comm_monitor.enabled therefore resets to False every time the generation
  dialog reopens, even if the user checked the box in the settings dialog.

Fix:
  1. _save_settings: add 'comm_monitor' (asdict) to the JSON dict.
  2. _load_saved_settings: restore comm_monitor from the dict.
  3. main_window: pass config_manager=self.config_manager to
     CodeGenerationDialog so its config_manager is shared with the rest
     of the GUI (defensive; keeps state consistent across dialogs).
  4. CodeGenerationDialog.__init__: accept optional config_manager
     parameter.

Idempotent.
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
DIALOG = CODE / "statable_gui" / "code_generation_dialog.py"
MAINWIN = CODE / "statable_gui" / "main_window.py"


def patch_dialog() -> bool:
    if not DIALOG.is_file():
        print(f"  [error] not found: {DIALOG}")
        return False
    text = DIALOG.read_text(encoding="utf-8")

    if "'comm_monitor':" in text and "comm_monitor=data[" in text:
        print(f"  [skip] already patched: {DIALOG.name}")
        return True

    # --- 1) __init__ accepts config_manager ---
    old_init = (
        "    def __init__(self, state_machine=None,\n"
        "                 global_defs=None,\n"
        "                 parent=None,\n"
        "                 settings_file=None,\n"
        "                 role_function_library=None):\n"
        "        super().__init__(parent)\n"
        "        self.state_machine = state_machine\n"
        "        self.global_defs = global_defs\n"
        "        self.generated_files: Dict[str, str] = {}\n"
        "        self.config_manager = ConfigManager()"
    )
    new_init = (
        "    def __init__(self, state_machine=None,\n"
        "                 global_defs=None,\n"
        "                 parent=None,\n"
        "                 settings_file=None,\n"
        "                 role_function_library=None,\n"
        "                 config_manager=None):\n"
        "        super().__init__(parent)\n"
        "        self.state_machine = state_machine\n"
        "        self.global_defs = global_defs\n"
        "        self.generated_files: Dict[str, str] = {}\n"
        "        self.config_manager = config_manager or ConfigManager()"
    )
    if old_init not in text:
        print("  [error] __init__ anchor not found")
        return False
    text = text.replace(old_init, new_init, 1)
    print("  [patched] __init__ accepts config_manager")

    # --- 2) _load_saved_settings: restore comm_monitor ---
    old_load = (
        "                if 'save_with_merge' in data:\n"
        "                    self.config_manager.update(\n"
        "                        save_with_merge=data['save_with_merge'])"
    )
    new_load = (
        old_load + "\n"
        "                if 'comm_monitor' in data and isinstance(\n"
        "                        data['comm_monitor'], dict):\n"
        "                    from codegen.comm_monitor.config import (\n"
        "                        CommMonitorConfig)\n"
        "                    self.config_manager.update(\n"
        "                        comm_monitor=CommMonitorConfig(\n"
        "                            **data['comm_monitor']))"
    )
    if old_load not in text:
        print("  [error] _load_saved_settings anchor not found")
        return False
    text = text.replace(old_load, new_load, 1)
    print("  [patched] _load_saved_settings restores comm_monitor")

    # --- 3) _save_settings: persist comm_monitor ---
    old_save = (
        "            config = self.config_manager.get_config()\n"
        "            data = {\n"
        "                'output_directory': config.output_directory,\n"
        "                'generation_style': config.generation_style,\n"
        "                'os_type': config.os_type,\n"
        "                'save_with_merge': config.save_with_merge,\n"
        "            }"
    )
    new_save = (
        "            from dataclasses import asdict\n"
        "            config = self.config_manager.get_config()\n"
        "            data = {\n"
        "                'output_directory': config.output_directory,\n"
        "                'generation_style': config.generation_style,\n"
        "                'os_type': config.os_type,\n"
        "                'save_with_merge': config.save_with_merge,\n"
        "                'comm_monitor': asdict(config.comm_monitor)\n"
        "                    if getattr(config, 'comm_monitor', None)\n"
        "                    else None,\n"
        "            }"
    )
    if old_save not in text:
        print("  [error] _save_settings anchor not found")
        return False
    text = text.replace(old_save, new_save, 1)
    print("  [patched] _save_settings persists comm_monitor")

    DIALOG.write_text(text, encoding="utf-8")
    return True


def patch_main_window() -> bool:
    if not MAINWIN.is_file():
        print(f"  [error] not found: {MAINWIN}")
        return False
    text = MAINWIN.read_text(encoding="utf-8")

    if "config_manager=self.config_manager," in text and "CodeGenerationDialog(" in text:
        # Check whether the pattern already exists in the dialog block
        anchor = (
            "        dialog = CodeGenerationDialog(\n"
            "            state_machine=primary_sm,\n"
            "            global_defs=gd,\n"
            "            parent=self,\n"
            "            role_function_library=(\n"
            "                self.role_function_library),\n"
            "            config_manager=self.config_manager,"
        )
        if anchor in text:
            print(f"  [skip] already patched: {MAINWIN.name}")
            return True

    old_call = (
        "        dialog = CodeGenerationDialog(\n"
        "            state_machine=primary_sm,\n"
        "            global_defs=gd,\n"
        "            parent=self,\n"
        "            role_function_library=(\n"
        "                self.role_function_library),\n"
        "        )"
    )
    new_call = (
        "        dialog = CodeGenerationDialog(\n"
        "            state_machine=primary_sm,\n"
        "            global_defs=gd,\n"
        "            parent=self,\n"
        "            role_function_library=(\n"
        "                self.role_function_library),\n"
        "            config_manager=self.config_manager,\n"
        "        )"
    )
    if old_call not in text:
        print("  [error] main_window CodeGenerationDialog anchor not found")
        return False
    text = text.replace(old_call, new_call, 1)
    MAINWIN.write_text(text, encoding="utf-8")
    print(f"  [patched] {MAINWIN.name} shares config_manager")
    return True


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p9_gui_persist ===")
    ok1 = patch_dialog()
    ok2 = patch_main_window()
    if not (ok1 and ok2):
        print("=== FAILED ===", file=sys.stderr)
        return 1
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())