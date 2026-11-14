"""patch_model_dict_type.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "statable" / "model.py"
t = M.read_text(encoding="utf-8")

old = '        d = {"type": self.type}\n'
new = '        d: Dict[str, Any] = {"type": self.type}\n'
if old not in t:
    raise SystemExit("[FAIL] anchor not found")
if t.count(old) != 1:
    raise SystemExit(f"[FAIL] not unique ({t.count(old)})")
t = t.replace(old, new, 1)

# 念のため import 確認
if "from typing import" not in t:
    raise SystemExit("[FAIL] no typing import")
# Dict/Any が import されているか
import re
m = re.search(r"from typing import ([^\n]+)", t)
if m:
    imported = m.group(1)
    needs = []
    if "Dict" not in imported:
        needs.append("Dict")
    if "Any" not in imported:
        needs.append("Any")
    if needs:
        t = t.replace(
            f"from typing import {imported}",
            f"from typing import {imported}, {', '.join(needs)}",
            1,
        )
        print(f"[OK] added {needs} to typing import")

M.write_text(t, encoding="utf-8")
print(f"[OK] {M}")
