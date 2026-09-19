#!/usr/bin/env python3
"""Create shared.txt for find_missing_files.py"""

from pathlib import Path

SHARED = [
    # --- statable/ ---
    "statable/model.py",
    "statable/state_machine.py",
    "statable/global_defs.py",
    "statable/xml_io.py",
    "statable/mermaid_gen.py",
    # --- statable_gui/ (top level) ---
    "statable_gui/matrix_table.py",
    "statable_gui/dialogs.py",
    "statable_gui/condition_builder_dialog.py",
    "statable_gui/global_defs.py",
    "statable_gui/logger.py",
    "statable_gui/config.py",
    "statable_gui/symbol_picker.py",
    # --- statable_gui/transition_editor_direct/ ---
    "statable_gui/transition_editor_direct/canvas_widget.py",
    "statable_gui/transition_editor_direct/code_widget.py",
    "statable_gui/transition_editor_direct/dialog.py",
    "statable_gui/transition_editor_direct/draft.py",
    "statable_gui/transition_editor_direct/edit_dialogs.py",
    "statable_gui/transition_editor_direct/flow_widget.py",
    "statable_gui/transition_editor_direct/palette_widget.py",
    "statable_gui/transition_editor_direct/system_global_dialog.py",
    "statable_gui/transition_editor_direct/condition_edit_dialog.py",
    # --- statable_gui/libcntrl/ ---
    "statable_gui/libcntrl/condition_library.py",
    "statable_gui/libcntrl/role_function_library.py",
    "statable_gui/libcntrl/role_function_edit_dialog.py",
    "statable_gui/libcntrl/literal_library.py",
    # --- codegen/ ---
    "codegen/c_code_generator.py",
    "codegen/code_templates.py",
    "codegen/transition_generator.py",
    "codegen/role_function_generator.py",
    "codegen/code_merger.py",
    "codegen/config.py",
    "codegen/enum_generator.py",
    "codegen/naming_convention.py",
    "codegen/struct_generator.py",
    # --- tools/ ---
    "tools/find_affected_files.py",
    "tools/find_missing_files.py",
]


def main():
    out = Path("shared.txt")
    with out.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# StaTable v2.2 shared files\n")
        for p in SHARED:
            f.write(p + "\n")
    print(f"Created: {out.resolve()}")
    print(f"Entries: {len(SHARED)}")


if __name__ == "__main__":
    main()