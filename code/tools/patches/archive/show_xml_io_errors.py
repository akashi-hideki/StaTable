import sys
from pathlib import Path

p = Path("statable/xml_io.py")
lines = p.read_text(encoding="utf-8").splitlines()

def show(label, start, end):
    print(f"\n===== {label} (L{start}-{end}) =====")
    for i in range(start - 1, min(end, len(lines))):
        print(f"{i+1:5d}: {lines[i]}")

show("A: L55-75 (type reassignment)", 55, 75)
show("B: L170-185 (Element kwargs)", 170, 185)
show("C: L398-425 (Event/str)", 398, 425)
show("D: L465-478 (int None)", 465, 478)
show("E: L1105-1125 (append None)", 1105, 1125)
