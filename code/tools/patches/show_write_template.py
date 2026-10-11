from pathlib import Path
p = Path("eclipse_installer/core.py")
lines = p.read_text(encoding="utf-8").splitlines()
# _write_template 関数全体を表示
start = None
for i, l in enumerate(lines):
    if l.startswith("def _write_template"):
        start = i
        break
if start is not None:
    for i in range(start, min(start + 40, len(lines))):
        print(f"{i+1:5d}: {lines[i]}")
