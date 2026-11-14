"""templates.py の $crc32u / $var_countu を修正する（UTF-8 安全）。"""
from pathlib import Path

p = (Path(__file__).resolve().parent.parent.parent
     / "codegen" / "comm_monitor" / "templates.py")

t = p.read_text(encoding="utf-8")
before = t
t = t.replace("0x$crc32u", "0x${crc32}u")
t = t.replace("$var_countu", "${var_count}u")

if t == before:
    print("[skip] no pattern (already fixed?)")
else:
    p.write_text(t, encoding="utf-8")
    print("[fix ] applied:", p)