"""patch_validation_dialog_union.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VD = ROOT / "codegen" / "validate" / "validation_dialog.py"
t = VD.read_text(encoding="utf-8")

old = (
    "        for i in range(self.change_tree.topLevelItemCount()):\n"
    "            item = self.change_tree.topLevelItem(i)\n"
    "            if item.checkState(0)"
)
new = (
    "        for i in range(self.change_tree.topLevelItemCount()):\n"
    "            item = self.change_tree.topLevelItem(i)\n"
    "            if item is None:\n"
    "                continue\n"
    "            if item.checkState(0)"
)
if old not in t:
    raise SystemExit("[FAIL] anchor not found")
t = t.replace(old, new, 1)
VD.write_text(t, encoding="utf-8")
print(f"[OK] {VD}")
