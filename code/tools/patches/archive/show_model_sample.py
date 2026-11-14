from pathlib import Path

def show(path, targets, ctx=4):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    for ln in targets:
        print(f"\n===== {path}:L{ln-4}-{ln+4} =====")
        for i in range(max(0, ln-5), min(ln+4, len(lines))):
            print(f"{i+1:5d}: {lines[i]}")

show("statable/model.py", [161, 162, 164, 167])
show("statable/sample_data.py", [53, 59, 60])
