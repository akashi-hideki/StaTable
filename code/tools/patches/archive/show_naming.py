from pathlib import Path

p = Path("codegen/naming_convention.py")
lines = p.read_text(encoding="utf-8").splitlines()

# CONVERSION_PATTERNS を表示
print("===== CONVERSION_PATTERNS =====")
in_block = False
for i, l in enumerate(lines):
    if "CONVERSION_PATTERNS" in l:
        in_block = True
    if in_block:
        print(f"{i+1:5d}: {l}")
        if in_block and l.strip() == "}" and i > 5:
            break

print()
print("===== import 部 =====")
for i in range(0, 30):
    print(f"{i+1:5d}: {lines[i]}")
