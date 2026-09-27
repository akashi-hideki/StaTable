# code/tools/patch_v2_8_fix6.py
"""
Patch v2.8.0-fix6:
  tools/gui_smoke_v2_8.py: fix ItemFlag vs int comparisons.

  PySide6's Qt.ItemFlag is an enum.Flag subclass that does NOT
  inherit from int, so `(flags & Flag) == 0` is always False.
  Replace with `bool(flags & Flag)` / `not bool(flags & Flag)`.

Usage:
    cd code
    python tools\\patch_v2_8_fix6.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
SMOKE = CODE_DIR / "tools" / "gui_smoke_v2_8.py"


OLD_RO0 = (
    '        check("row0 checkable & checked",\n'
    '              (row0.flags() & Qt.ItemIsUserCheckable) != 0\n'
    '              and row0.checkState(0) == Qt.Checked)\n'
)
NEW_RO0 = (
    '        check("row0 checkable & checked",\n'
    '              bool(row0.flags() & Qt.ItemIsUserCheckable)\n'
    '              and row0.checkState(0) == Qt.Checked)\n'
)

OLD_RO1 = (
    '        check("row1 not checkable",\n'
    '              (row1.flags() & Qt.ItemIsUserCheckable) == 0)\n'
)
NEW_RO1 = (
    '        check("row1 not checkable",\n'
    '              not bool(row1.flags() & Qt.ItemIsUserCheckable))\n'
)


def _apply(path: Path, anchor: str, replacement: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(anchor)
    if count == 0:
        print(f"  [SKIP] {label}: anchor not found (already applied?)")
        return
    if count > 1:
        print(f"  [FAIL] {label}: anchor found {count} times")
        raise SystemExit(1)
    print(f"  [APPLY] {label}")
    path.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")


def main() -> int:
    print("=" * 70)
    print("  v2.8.0-fix6 patch")
    print("=" * 70)

    if not SMOKE.exists():
        print(f"[FAIL] target not found: {SMOKE}")
        return 1

    print(f"\nTarget: {SMOKE}")
    bak = SMOKE.with_suffix(SMOKE.suffix + ".bak_fix6")
    if not bak.exists():
        bak.write_text(SMOKE.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Backup: {bak}")
    else:
        print(f"  Backup: already exists, keeping {bak}")

    _apply(SMOKE, OLD_RO0, NEW_RO0, "row0: bool(...) instead of != 0")
    _apply(SMOKE, OLD_RO1, NEW_RO1, "row1: not bool(...) instead of == 0")

    print()
    print("[DONE] fix6 applied.")
    print()
    print("Verify:")
    print("  python tools\\gui_smoke_v2_8.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())