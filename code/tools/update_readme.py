#!/usr/bin/env python3
"""Update README.md Roadmap for v2.4.

Version History
---------------
v1.0 - Initial: replace v2.3 (Current) section with v2.4 (Current) + v2.3 (Released).
"""

from pathlib import Path
import sys


OLD = """### v2.3 (Current — Released 2026-09-21)

- ✅ New Project feature (Ctrl+N)
- ✅ Unsaved-changes dialog (Save / Discard / Cancel)
- ✅ Window title modified marker (`*`)
- ✅ `StateMachineTab.dataModified` signal
- ✅ Logger guard against deleted TraceBall widgets (C-40)
- ✅ **551 PASS / 0 FAIL / 2 SKIP**"""

NEW = """### v2.4 (Current — Released 2026-09-22)

- ✅ UI cleanup: State list 5 columns, Role function 4 columns
- ✅ Namespace combo box listing all project layers
- ✅ Reserved fields hidden from UI (State.do, RoleFunction signature)
- ✅ XML round-trip preserved for reserved fields (empty `used_*` attributes suppressed)
- ✅ Role function Edit path restored (button + row double-click)
- ✅ **551 PASS / 0 FAIL / 2 SKIP**

### v2.3 (Released 2026-09-21)

- ✅ New Project feature (Ctrl+N)
- ✅ Unsaved-changes dialog (Save / Discard / Cancel)
- ✅ Window title modified marker (`*`)
- ✅ `StateMachineTab.dataModified` signal
- ✅ Logger guard against deleted TraceBall widgets (C-40)
- ✅ **551 PASS / 0 FAIL / 2 SKIP**"""


def main() -> int:
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
    else:
        # Default: repository root (parent of code/)
        here = Path(__file__).resolve().parent.parent.parent
        root = here

    path = root / "README.md"
    print(f"Target: {path}")

    if not path.exists():
        print("  [FAIL] README.md not found")
        return 1

    text = path.read_text(encoding="utf-8")

    if OLD not in text:
        print("  [SKIP] anchor not found.")
        print("  Searching for v2.3 mentions:")
        for i, line in enumerate(text.splitlines(), 1):
            if "v2.3" in line and "Roadmap" not in line:
                print(f"    {i}: {line}")
        return 2

    new_text = text.replace(OLD, NEW, 1)
    path.write_text(new_text, encoding="utf-8", newline="\n")
    print("  [OK] README.md updated")
    print("       - v2.4 section added at top")
    print("       - v2.3 section relabeled 'Released'")
    return 0


if __name__ == "__main__":
    sys.exit(main())