"""patch_validation_dialog_mypy.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VD = ROOT / "codegen" / "validate" / "validation_dialog.py"

lines = VD.read_text(encoding="utf-8").split("\n")
out = []
fixed = 0

# Enum attributes to annotate
ENUM_ATTRS = [
    "Qt.red", "Qt.yellow", "Qt.blue", "Qt.black",
    "Qt.ItemIsUserCheckable", "Qt.ItemIsEnabled", "Qt.Checked",
]

for line in lines:
    if "type: ignore" in line:
        out.append(line)
        continue
    changed = False
    for attr in ENUM_ATTRS:
        # Only replace if the attr appears as an identifier (not part of another)
        if attr in line:
            line = line.replace(attr, f"{attr}  # type: ignore[attr-defined]", 1)
            changed = True
            break  # only one per line to avoid double-ignore
    if changed:
        fixed += 1
    out.append(line)

if fixed == 0:
    raise SystemExit("[FAIL] no changes")

VD.write_text("\n".join(out), encoding="utf-8")
print(f"[OK] fixed {fixed} line(s) in {VD}")
