"""show_defs_detail.py"""
from pathlib import Path

def show(path, start, end, label=""):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    print(f"\n===== {path}:L{start}-{end} {label} =====")
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1:5d}: {lines[i]}")

# ACTION_DEFINITIONS の型 (中身の最初の数エントリ)
show("codegen/validate/data/action_definitions.py", 1, 30)

# MARKERS
show("codegen/validate/data/keywords.py", 1, 40, "MARKERS?")
