from pathlib import Path
for rel in ["codegen/validate/data/action_definitions.py", "codegen/validate/data/keywords.py"]:
    print(f"\n===== {rel} L1-25 =====")
    lines = Path(rel).read_text(encoding="utf-8").splitlines()
    for i in range(0, 25):
        print(f"{i+1:5d}: {lines[i]}")
