"""Register test_v3_4_0_signal_safety.py in CI check.yml (idempotent)."""
from __future__ import annotations
import sys
from pathlib import Path

CHECK_YML = (Path(__file__).resolve().parent.parent.parent.parent
             / ".github" / "workflows" / "check.yml")

NEW_LINE = "          python tests/test_v3_4_0_signal_safety.py\n"
ANCHOR = "          python tests/test_v3_4_0_state_actions.py\n"


def main() -> int:
    if not CHECK_YML.exists():
        print(f"[ERR] {CHECK_YML} not found")
        return 1
    text = CHECK_YML.read_text(encoding="utf-8")

    if "test_v3_4_0_signal_safety.py" in text:
        print("[SKIP] check.yml already has signal_safety test")
        return 0

    if ANCHOR not in text:
        print("[ERR] anchor line not found:")
        print(f"      {ANCHOR.rstrip()}")
        return 1

    text = text.replace(ANCHOR, ANCHOR + NEW_LINE, 1)
    CHECK_YML.write_text(text, encoding="utf-8", newline="\n")
    print("[OK]   check.yml: inserted test_v3_4_0_signal_safety.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())