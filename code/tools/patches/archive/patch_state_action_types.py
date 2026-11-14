"""patch_state_action_types.py"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "statable" / "model.py"
t = M.read_text(encoding="utf-8")

def _must(old, new, label, count=1):
    global t
    n = t.count(old)
    if n != count:
        raise SystemExit(f"[FAIL] {label}: count={n} (expected {count})")
    t = t.replace(old, new)
    print(f"[OK] {label}")

# 1) Union を import
m = re.search(r"from typing import ([^\n]+)", t)
if not m:
    raise SystemExit("[FAIL] no typing import")
imported = m.group(1)
if "Union" not in imported:
    t = t.replace(
        f"from typing import {imported}",
        f"from typing import {imported}, Union",
        1,
    )
    print("[OK] added Union to typing import")

# 2) entry / exit / do_actions を Union[List[ActionStep], List[str]] に
_must(
    "    entry: List[ActionStep] = field(default_factory=list)\n"
    "    exit: List[ActionStep] = field(default_factory=list)\n",
    "    # [v3.5.1] Accept str for backward compatibility (auto-normalized\n"
    "    # in __post_init__ to List[ActionStep]).\n"
    "    entry: Union[List[ActionStep], List[str]] = field(default_factory=list)\n"
    "    exit: Union[List[ActionStep], List[str]] = field(default_factory=list)\n",
    "entry/exit type",
)

# do_actions field 確認
if "    do_actions:" in t:
    # 現在の型を表示
    m2 = re.search(r"(    do_actions:[^\n]+\n)", t)
    if m2:
        print(f"[INFO] current do_actions: {m2.group(1).strip()}")
        # Union に変更
        t = re.sub(
            r"    do_actions:\s*List\[ActionStep\](\s*=\s*field\(default_factory=list\))",
            r"    do_actions: Union[List[ActionStep], List[str]]\1",
            t,
            count=1,
        )
        print("[OK] do_actions type")
elif "    do:" in t:
    m2 = re.search(r"(    do:[^\n]+\n)", t)
    if m2:
        print(f"[INFO] current do: {m2.group(1).strip()}")

M.write_text(t, encoding="utf-8")
print(f"[OK] {M}")
