"""fix_linker_bom_and_sbrk.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TPL = ROOT / "eclipse_installer" / "templates"

# 1. Remove BOM from linker.ld
LD = TPL / "linker_stm32f405.ld"
raw = LD.read_bytes()
if raw.startswith(b"\xef\xbb\xbf"):
    LD.write_bytes(raw[3:])
    print(f"[OK] removed BOM from {LD}")
else:
    print(f"[SKIP] no BOM in {LD}")

# 2. Add _sbrk to syscalls.c
SC = TPL / "syscalls.c"
t = SC.read_text(encoding="utf-8")
if "_sbrk" not in t:
    sbrk_code = (
        "\n/* --- Heap management (required by newlib) --- */\n"
        "extern char _ebss;\n\n"
        "void *_sbrk(int incr)\n"
        "{\n"
        "    static char *heap_end = 0;\n"
        "    char *prev;\n"
        "    if (heap_end == 0) {\n"
        "        heap_end = &_ebss;\n"
        "    }\n"
        "    prev = heap_end;\n"
        "    heap_end += incr;\n"
        "    return prev;\n"
        "}\n"
    )
    marker = "void _exit(int status)"
    if marker in t:
        t = t.replace(marker, sbrk_code + "\n" + marker, 1)
    else:
        t += "\n" + sbrk_code
    SC.write_text(t, encoding="utf-8")
    print(f"[OK] added _sbrk to {SC}")
else:
    print(f"[SKIP] _sbrk already in {SC}")
