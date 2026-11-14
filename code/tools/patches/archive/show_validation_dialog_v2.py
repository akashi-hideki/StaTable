from pathlib import Path
p = Path("codegen/validate/validation_dialog.py")
lines = p.read_text(encoding="utf-8").splitlines()
# mypy error lines
targets = [196, 197, 198, 210, 259, 260, 274, 301]
shown = set()
for ln in targets:
    for i in range(ln-1, min(ln+2, len(lines))):
        if i not in shown:
            print(f"{i+1:5d}: {lines[i]}")
            shown.add(i)
    print("---")
