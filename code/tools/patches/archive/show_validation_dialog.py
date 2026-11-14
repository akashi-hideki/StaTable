from pathlib import Path
p = Path("codegen/validate/validation_dialog.py")
lines = p.read_text(encoding="utf-8").splitlines()
# エラー箇所周辺を表示
for start in [295, 300, 305]:
    print(f"\n===== L{start-5}-{start+10} =====")
    for i in range(start-6, min(start+10, len(lines))):
        print(f"{i+1:5d}: {lines[i]}")
