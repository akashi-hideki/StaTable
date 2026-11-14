#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p8_volatile.py

Fix -Wdiscarded-qualifiers warning in comm_monitor registry.

Root cause:
  VarEntry_t.ptr is `const void *` (non-volatile), but registered
  variables such as g_ctx.data.<name> are declared `volatile`.
  Initialization {&g_ctx.data.x, 4} therefore discards the volatile
  qualifier, which fails under -Werror in verify_c_syntax.py --strict.

Fix:
  - VarEntry_t.ptr  -> const volatile void *
  - comm_registry_read casts -> const volatile uint8_t/16/32 *

Idempotent.
"""
import re
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "codegen" / "comm_monitor" / "templates.py"


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p8_volatile ===")
    if not TARGET.is_file():
        print(f"[error] not found: {TARGET}", file=sys.stderr)
        return 1

    text = TARGET.read_text(encoding="utf-8")

    if "const volatile void *ptr" in text:
        print(f"  [skip] already patched: {TARGET.name}")
        return 0

    # 1) VarEntry_t.ptr: const void * -> const volatile void *
    old_h = "typedef struct { const void *ptr; uint8_t size; } VarEntry_t;"
    new_h = "typedef struct { const volatile void *ptr; uint8_t size; } VarEntry_t;"
    if old_h not in text:
        print("[error] registry.h typedef anchor not found", file=sys.stderr)
        return 1
    text = text.replace(old_h, new_h, 1)
    print("  [patched] VarEntry_t.ptr -> const volatile void *")

    # 2) read casts: add volatile while preserving original spacing
    #    *(const uint8_t  *)e->ptr  ->  *(const volatile uint8_t  *)e->ptr
    #    *(const uint16_t *)e->ptr  ->  *(const volatile uint16_t *)e->ptr
    #    *(const uint32_t *)e->ptr  ->  *(const volatile uint32_t *)e->ptr
    pat = re.compile(r"\*\(const (uint8_t|uint16_t|uint32_t)(\s*)\*\)e->ptr")
    text, n = pat.subn(
        lambda m: f"*(const volatile {m.group(1)}{m.group(2)}*)e->ptr",
        text,
    )
    if n == 0:
        print("[error] read cast anchor not found", file=sys.stderr)
        return 1
    print(f"  [patched] {n} read cast(s)")

    TARGET.write_text(text, encoding="utf-8")
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())