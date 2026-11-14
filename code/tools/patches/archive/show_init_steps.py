from pathlib import Path
lines = Path("codegen/variable_generator.py").read_text(encoding="utf-8").splitlines()
print("===== INIT_FUNCTION_STEPS =====")
for i in range(90, 130):
    print(f"{i+1:5d}: {lines[i]}")
print()
print("===== step_executors =====")
for i in range(177, 200):
    print(f"{i+1:5d}: {lines[i]}")
