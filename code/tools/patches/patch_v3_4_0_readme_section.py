"""Add 'What's New in v3.4.0' section to README.md (idempotent)."""
from __future__ import annotations
import sys
from pathlib import Path

README = Path(__file__).resolve().parent.parent.parent.parent / "README.md"

SECTION = """## What's New in v3.4.0

**StateActionsDialog: combo-based editing + role/event management**

- **Target column is now a QComboBox** (Type-dependent)
  - `role`       -> `qualified_name` from `RoleFunctionLibrary` + `state_machine`
  - `fire_event` -> `EVENT_<Layer>_<Name>` from `state_machine.events`
  - Eliminates typos and makes generated C code deterministic
- **Role function management buttons**: `+ New` / `Edit` / `Delete`
  - Uses `RoleFunctionDialog` (same UX as `ActionEditorDialog`)
  - Registers into `state_machine.role_functions` on the fly
- **Event management buttons**: `+ New` / `Edit` / `Delete`
  - Uses `EventEditDialog`
  - Reference check before delete (transitions must be removed first)
- **Condition column**: `QLineEdit` + `[...]` button
  - Opens `ConditionBuilderDialog` (same as `ActionEditorDialog`)
- **New constructor args**: `role_function_library`, `literal_library`,
  `condition_library`, `layer_names_provider`, `global_defs`
- **Test**: `test_v3_4_0_state_actions.py` (30 PASS)

See [SPEC_STATE_ACTIONS_v1.md](code/docs/SPEC_STATE_ACTIONS_v1.md) for details.

"""

ANCHOR = "## What's New in v3.2.0"
MARKER = "## What's New in v3.4.0"


def main() -> int:
    if not README.exists():
        print(f"[ERR] {README} not found")
        return 1

    text = README.read_text(encoding="utf-8")

    if MARKER in text:
        print("[SKIP] README.md already has v3.4.0 section")
        return 0

    if ANCHOR not in text:
        print(f"[ERR] anchor '{ANCHOR}' not found in README.md")
        return 1

    text = text.replace(ANCHOR, SECTION + ANCHOR, 1)
    README.write_text(text, encoding="utf-8", newline="\n")
    print("[OK]   README.md: inserted v3.4.0 section before v3.2.0")
    return 0


if __name__ == "__main__":
    sys.exit(main())