"""fix_validation_dialog_syntax.py

Move `# type: ignore[...]` AFTER the trailing comma to fix
syntax-broken lines like:
  'error': Qt.red  # type: ignore[attr-defined],
->
  'error': Qt.red,  # type: ignore[attr-defined]
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VD = ROOT / "codegen" / "validate" / "validation_dialog.py"
t = VD.read_text(encoding="utf-8")

# Pattern: <expr>  # type: ignore[xxx],
# Replace with: <expr>,  # type: ignore[xxx]
pattern = re.compile(
    r"(?P<expr>[^\n#]+?)\s*#\s*type:\s*ignore\[(?P<codes>[^\]]+)\],"
)

def repl(m):
    expr = m.group("expr").rstrip()
    codes = m.group("codes")
    return f"{expr},  # type: ignore[{codes}]"

new_t, n = pattern.subn(repl, t)
if n == 0:
    print("[SKIP] no broken patterns found")
else:
    VD.write_text(new_t, encoding="utf-8")
    print(f"[OK] fixed {n} line(s)")

# Also handle non-comma cases (e.g., function call args ending with `)`)
# Pattern: <expr>  # type: ignore[xxx])
pattern2 = re.compile(
    r"(?P<expr>[^\n#]+?)\s*#\s*type:\s*ignore\[(?P<codes>[^\]]+)\)"
)

def repl2(m):
    expr = m.group("expr").rstrip()
    codes = m.group("codes")
    return f"{expr})  # type: ignore[{codes}]"

t2 = VD.read_text(encoding="utf-8")
new_t2, n2 = pattern2.subn(repl2, t2)
if n2 > 0:
    VD.write_text(new_t2, encoding="utf-8")
    print(f"[OK] fixed {n2} paren case(s)")
