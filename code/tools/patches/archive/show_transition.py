from pathlib import Path

p = Path("codegen/transition_generator.py")
lines = p.read_text(encoding="utf-8").splitlines()

for ln in [685, 691, 752, 837, 843]:
    print(f"\n===== L{ln-5}-{ln+5} =====")
    for i in range(max(0, ln-6), min(ln+5, len(lines))):
        print(f"{i+1:5d}: {lines[i]}")

print("\n===== import 部 =====")
for i in range(0, 30):
    print(f"{i+1:5d}: {lines[i]}")
