#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p6b_fix_tests.py

Update existing integration tests to the new _merge_comm_monitor_files
signature (state_machine param removed in p6).

Before: gen._merge_comm_monitor_files(base, None, gd)
After:  gen._merge_comm_monitor_files(base, gd)

Idempotent.
"""
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "tests" / "test_v3_6_0_comm_monitor_integration.py"


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p6b_fix_tests ===")
    if not TARGET.is_file():
        print(f"[error] not found: {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")

    # Idempotency: if no old-signature calls remain, skip
    old_pat = re.compile(
        r"_merge_comm_monitor_files\(\s*(\w+)\s*,\s*None\s*,\s*(\w+)\s*\)"
    )
    new_text, n = old_pat.subn(
        r"_merge_comm_monitor_files(\1, \2)", text
    )
    if n == 0:
        print(f"  [skip] already patched or no match: {TARGET.name}")
        return 0

    TARGET.write_text(new_text, encoding="utf-8")
    print(f"  [patched] {n} call site(s) in {TARGET.name}")
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())