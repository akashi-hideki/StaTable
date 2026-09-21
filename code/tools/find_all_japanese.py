# find_all_japanese.py - Scan all .py files for Japanese characters
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JP_RE = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF]')

DIRS = ["statable", "statable_gui", "codegen"]
SKIP = {"tools", "tests", "__pycache__", "_backup"}

hits = 0
for d in DIRS:
    root = PROJECT_ROOT / d
    if not root.exists():
        continue
    for f in root.rglob("*.py"):
        if any(s in str(f) for s in SKIP):
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            if JP_RE.search(line):
                rel = f.relative_to(PROJECT_ROOT)
                print(f"{rel}:{i}: {line.strip()[:100]}")
                hits += 1

print()
print(f"Total: {hits} line(s) with Japanese")
sys.exit(0 if hits == 0 else 1)
