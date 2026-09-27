# code/tools/patch_v2_8_phase_d1.py
"""
Phase D-1 patch for v2.8.0.

Target:
    code/tests/test_v2_8_p1_ai_prompt.py

Adds two sections before the Summary block:

  [12] ResponseValidator integration
       - valid request accepted
       - invalid request rejected with reason
       - low-confidence warning emitted

  [13] validation_dialog wiring (source-level)
       - imports ResponseValidator
       - instantiates response_validator
       - stores validation_outcome
       - calls validate() in _parse_response
       - change_tree has Priority / Confidence / Status
       - invalid rows marked EXCLUDED

Usage:
    cd C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code
    python tools\\patch_v2_8_phase_d1.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
TARGET = CODE_DIR / "tests" / "test_v2_8_p1_ai_prompt.py"


ANCHOR = (
    "# ======================================================================\n"
    "# Summary\n"
    "# ======================================================================\n"
)


INSERT = '''# ======================================================================
# [12] ResponseValidator integration
# ======================================================================
section("12 ResponseValidator integrates with prompt workflow")

from codegen.validate.change_actions import (
    ChangeRequest, ChangeActionType,
)
from codegen.validate.response_validator import ResponseValidator

sm_v = make_basic_sm()
v = ResponseValidator()

# Valid request
r = v.validate([
    ChangeRequest(
        action=ChangeActionType.ADD_TRANSITION,
        params={"source": "Idle", "event": "START", "target": "Active"},
        reason="ok",
    ),
], sm_v)
check("valid request accepted", len(r.valid_requests) == 1)
check("invalid empty", len(r.invalid_requests) == 0)

# Invalid request
r = v.validate([
    ChangeRequest(
        action=ChangeActionType.ADD_TRANSITION,
        params={"source": "Ghost", "event": "START", "target": "Active"},
        reason="test",
    ),
], sm_v)
check("invalid request rejected", len(r.valid_requests) == 0)
check("invalid captured with reason",
      len(r.invalid_requests) == 1
      and "Ghost" in r.invalid_requests[0][1])

# Low-confidence warning
r = v.validate([
    ChangeRequest(
        action=ChangeActionType.ADD_STATE,
        params={"name": "New"},
        reason="test",
        id="C-001",
        confidence=0.3,
    ),
], sm_v)
check("low-confidence warning emitted", len(r.warnings) == 1)


# ======================================================================
# [13] validation_dialog exposes ResponseValidator
# ======================================================================
section("13 validation_dialog wires ResponseValidator")
from pathlib import Path as _P

_vd_path = _P(__file__).resolve().parent.parent \\
    / "codegen" / "validate" / "validation_dialog.py"
_vd_src = _vd_path.read_text(encoding="utf-8")
check("imports ResponseValidator",
      "from .response_validator import ResponseValidator" in _vd_src)
check("instantiates response_validator",
      "self.response_validator = ResponseValidator()" in _vd_src)
check("stores validation_outcome",
      "self.validation_outcome = None" in _vd_src)
check("validates in _parse_response",
      "self.response_validator.validate(" in _vd_src)
check("change_tree has Priority column",
      '"Priority"' in _vd_src)
check("change_tree has Confidence column",
      '"Confidence"' in _vd_src)
check("change_tree has Status column",
      '"Status"' in _vd_src)
check("invalid rows marked EXCLUDED",
      'EXCLUDED:' in _vd_src)


'''


def main() -> int:
    print("=" * 70)
    print("  v2.8.0 Phase D-1 patch")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] target not found: {TARGET}")
        return 1

    print(f"\nTarget: {TARGET}")
    original = TARGET.read_text(encoding="utf-8")

    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")
        print(f"  Backup: {backup}")
    else:
        print(f"  Backup: already exists, keeping {backup}")

    if "[12] ResponseValidator integration" in original:
        print("  [SKIP] D-1 already applied")
        return 0

    count = original.count(ANCHOR)
    if count == 0:
        print("  [FAIL] anchor (Summary block) not found")
        return 1
    if count > 1:
        print(f"  [FAIL] anchor found {count} times (expected 1)")
        return 1

    print("  [APPLY] D-1 insert [12] and [13] sections")
    patched = original.replace(ANCHOR, INSERT + ANCHOR, 1)
    TARGET.write_text(patched, encoding="utf-8")

    print()
    print("[DONE] test_v2_8_p1_ai_prompt.py patched.")
    print()
    print("Verify:")
    print("  python tests\\test_v2_8_p1_ai_prompt.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())