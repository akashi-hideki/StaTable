"""v3.5.0 Phase 1b: annotate all CodeTemplates dicts as dict[str, Any]."""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"
TARGET = CODE / "codegen" / "code_templates.py"

DICTS = [
    "STRINGS", "SECTION_HEADERS", "STRUCT_COMMENTS", "ENUM_COMMENTS",
    "TYPE_NAMES", "FUNCTION_NAMES", "MACRO_NAMES", "FORMATS",
    "LAYER_TEMPLATES", "COMMON_TYPES_TEMPLATES", "ISR_TEMPLATES",
    "DEBUG_MESSAGES", "OSAL",
    "SUPER_INCLUDE_TEMPLATES", "SUPER_LOOP_TEMPLATES",
]


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_6_phase1b_codetemplates")
    print("=" * 70)

    txt = TARGET.read_text(encoding="utf-8")

    # 1) add typing.Any import after module docstring
    if "from typing import Any" not in txt:
        marker = '"""\n\n\nclass CodeTemplates:'
        replacement = '"""\n\nfrom typing import Any\n\n\nclass CodeTemplates:'
        if marker not in txt:
            print("[FAIL] docstring/class marker not found")
            sys.exit(1)
        txt = txt.replace(marker, replacement, 1)
        print("  added: from typing import Any")
    else:
        print("  [SKIP] typing.Any already imported")

    # 2) annotate each dict
    applied = 0
    for name in DICTS:
        # Match only the class-level assignment (4 spaces indent)
        old = f"    {name} = {{"
        new = f"    {name}: dict[str, Any] = {{"
        if old not in txt:
            print(f"  [SKIP] {name}: pattern not found")
            continue
        txt = txt.replace(old, new, 1)
        applied += 1
    print(f"  annotated: {applied}/{len(DICTS)} dicts")

    TARGET.write_text(txt, encoding="utf-8")
    print()
    print("[OK] done. Next:")
    print("     cd code")
    print("     python -m mypy codegen statable statable_gui 2>&1 | Select-Object -Last 3")
    return 0


if __name__ == "__main__":
    sys.exit(main())