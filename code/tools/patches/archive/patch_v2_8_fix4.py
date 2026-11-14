# code/tools/patch_v2_8_fix4.py
"""
Patch script for v2.8.0-fix4.

Target:
    code/codegen/validate/prompt_generator.py

Problem (fix2):
    `TimerBaseDef.__post_init__` auto-populates `title` to
    "Timer base: <variable_name>". The fix2 pristine check expected
    `title == ''`, so a freshly constructed GlobalDefinitions() was
    mis-detected as "user-customized" and produced a non-empty
    <timers> section, preventing <global_definitions/> from being
    emitted for an empty GD.

Fix (fix4):
    Remove `title` from the pristine-defaults comparison. `title`
    is UI-only metadata; the semantic identity of a timer is
    determined by variable_name / unit / data_type / derived.

Safety:
    - Backup once to prompt_generator.py.bak (kept if present).
    - Literal anchor: refuses to apply if the anchor is missing
      or appears more than once.
    - Idempotent: re-running after a successful apply does nothing.

Usage:
    cd C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code
    python tools\\patch_v2_8_fix4.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
TARGET = CODE_DIR / "codegen" / "validate" / "prompt_generator.py"


# ----------------------------------------------------------------------
# Anchor: current _has_timer_content (as installed by fix2)
# ----------------------------------------------------------------------
ANCHOR_OLD = '''    def _has_timer_content(self, tb) -> bool:
        """Return True if the timer_base has user-meaningful content.

        [v2.8.0-fix2]
          A freshly constructed GlobalDefinitions() has a default
          TimerBaseDef with only pristine values. Those defaults
          carry no information for the AI, so a pristine timer_base
          can be skipped in <global_definitions>. Any deviation
          from the defaults (or any derived timers) makes this
          method return True.
        """
        if getattr(tb, 'derived', None):
            return True
        defaults = {
            'variable_name': 'g_system_tick',
            'unit': '1ms',
            'data_type': 'volatile uint32_t',
            'title': '',
            'interrupt_name': '',
        }
        for attr, expected in defaults.items():
            if getattr(tb, attr, '') != expected:
                return True
        return False
'''

ANCHOR_NEW = '''    def _has_timer_content(self, tb) -> bool:
        """Return True if the timer_base has user-meaningful content.

        [v2.8.0-fix2]
          A freshly constructed GlobalDefinitions() has a default
          TimerBaseDef with only pristine values. Those defaults
          carry no information for the AI, so a pristine timer_base
          can be skipped in <global_definitions>. Any deviation
          from the defaults (or any derived timers) makes this
          method return True.

        [v2.8.0-fix4]
          `TimerBaseDef.title` is auto-populated to
          "Timer base: <variable_name>" by __post_init__, so it is
          NOT a reliable indicator of user customization. The title
          field is excluded from the pristine comparison; the
          semantic identity of a timer is determined by
          variable_name / unit / data_type / derived.
        """
        if getattr(tb, 'derived', None):
            return True
        defaults = {
            'variable_name': 'g_system_tick',
            'unit': '1ms',
            'data_type': 'volatile uint32_t',
            'interrupt_name': '',
        }
        for attr, expected in defaults.items():
            if getattr(tb, attr, '') != expected:
                return True
        return False
'''


def _apply_edit(text: str, anchor: str, replacement: str, label: str) -> str:
    count = text.count(anchor)
    if count == 0:
        print(f"  [SKIP] {label}: anchor not found (already applied?)")
        return text
    if count > 1:
        print(f"  [FAIL] {label}: anchor found {count} times (expected 1)")
        raise SystemExit(1)
    print(f"  [APPLY] {label}: replacing 1 occurrence")
    return text.replace(anchor, replacement, 1)


def main() -> int:
    print("=" * 70)
    print("  v2.8.0-fix4 patch")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] target not found: {TARGET}")
        return 1

    print(f"Target: {TARGET}")
    original = TARGET.read_text(encoding="utf-8")

    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")
        print(f"Backup: {backup}")
    else:
        print(f"Backup: already exists, keeping {backup}")

    patched = _apply_edit(
        original,
        ANCHOR_OLD,
        ANCHOR_NEW,
        "Edit 1 (exclude title from pristine check)",
    )

    if patched == original:
        print()
        print("[INFO] No changes were made (already up to date).")
        return 0

    TARGET.write_text(patched, encoding="utf-8")
    print()
    print("[DONE] prompt_generator.py patched (fix4).")
    print()
    print("Next:")
    print("  python tools\\diag_gd_empty.py         (should now print <global_definitions/>)")
    print("  python tests\\test_v2_8_p1_ai_prompt.py")
    print("  python tests\\test_v2_2_p12_6.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())