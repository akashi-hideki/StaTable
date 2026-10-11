from pathlib import Path
p = Path("eclipse_installer/core.py")
lines = p.read_text(encoding="utf-8").splitlines()
# _write_template 定義 と with_eclipse_project ブロックを表示
for i, l in enumerate(lines):
    if "_write_template" in l or "settings/" in l or "with_eclipse_project" in l:
        print(f"{i+1:5d}: {l}")
