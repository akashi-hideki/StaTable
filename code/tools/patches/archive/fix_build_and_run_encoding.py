"""fix_build_and_run_encoding.py

Fix: cp932 decode error in subprocess.run.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BR = ROOT / "tools" / "build_and_run.py"

t = BR.read_text(encoding="utf-8")

# 1) All subprocess.run(...) calls: add encoding="utf-8", errors="replace"
old1 = 'r = subprocess.run(cmd, capture_output=True, text=True)'
new1 = ('r = subprocess.run(cmd, capture_output=True, text=True,\n'
        '                       encoding="utf-8", errors="replace")')
if old1 not in t:
    raise SystemExit("[FAIL] anchor1 not found")
t = t.replace(old1, new1, 1)

old2 = 'r = subprocess.run(link_cmd, capture_output=True, text=True)'
new2 = ('r = subprocess.run(link_cmd, capture_output=True, text=True,\n'
        '                       encoding="utf-8", errors="replace")')
if old2 not in t:
    raise SystemExit("[FAIL] anchor2 not found")
t = t.replace(old2, new2, 1)

# 2) For .s files, add -x assembler-with-cpp
old3 = ('        cmd = [CC] + CFLAGS_COMMON + inc_flags '
        '+ ["-c", str(src), "-o", str(obj)]')
new3 = ('        if src.suffix.lower() == ".s":\n'
        '            cmd = ([CC, "-x", "assembler-with-cpp"]\n'
        '                   + CPU + inc_flags\n'
        '                   + ["-c", str(src), "-o", str(obj)])\n'
        '        else:\n'
        '            cmd = ([CC] + CFLAGS_COMMON + inc_flags\n'
        '                   + ["-c", str(src), "-o", str(obj)])')
if old3 not in t:
    raise SystemExit("[FAIL] anchor3 not found")
t = t.replace(old3, new3, 1)

BR.write_text(t, encoding="utf-8")
print(f"[OK] patched {BR}")
