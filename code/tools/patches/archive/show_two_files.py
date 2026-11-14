from pathlib import Path

def show(path, targets, ctx=3):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    shown = set()
    for ln in targets:
        for i in range(max(0, ln-1-ctx), min(ln-1+ctx+1, len(lines))):
            if i not in shown:
                print(f"{path}:{i+1:5d}: {lines[i]}")
                shown.add(i)
        print("---")

show("codegen/transition_generator.py", [273, 278])
show("codegen/naming_convention.py", [80, 82, 95, 98, 101, 108])
