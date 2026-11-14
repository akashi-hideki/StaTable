#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p13_sbrk_stub.py

Add a failing _sbrk stub to tools/arm_template/stub_main.c.

Root cause:
  statable_comm_monitor.c uses snprintf, which via newlib pulls in
  _malloc_r -> _sbrk_r -> _sbrk (from libnosys.a).  _sbrk references
  the linker symbol `end`, which the generic linker.ld does not define.
  Baseline state machine code did not use snprintf, so it linked fine.

Fix:
  Provide `void *_sbrk(int incr) { return (void *)-1; }` in the stub
  main.  This satisfies the link-time symbol requirement; the actual
  snprintf path does not allocate for our format specifiers, and any
  accidental malloc returns NULL (MISRA C:2012 Rule 21.3 avoidance).

Idempotent.
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "tools" / "arm_template" / "stub_main.c"

SBRK_STUB = (
    "\n"
    "/* No dynamic memory in embedded target (MISRA C:2012 Rule 21.3).\n"
    " * newlib's snprintf can reference _sbrk; provide a failing stub\n"
    " * so link succeeds and any actual malloc call returns NULL. */\n"
    "void *_sbrk(int incr) {\n"
    "    (void)incr;\n"
    "    return (void *)-1;\n"
    "}\n"
)


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p13_sbrk_stub ===")
    if not TARGET.is_file():
        print(f"[error] not found: {TARGET}", file=sys.stderr)
        return 1
    text = TARGET.read_text(encoding="utf-8")
    if "_sbrk" in text:
        print(f"  [skip] already patched: {TARGET.name}")
        return 0
    TARGET.write_text(text + SBRK_STUB, encoding="utf-8")
    print(f"  [patched] {TARGET.name}: added _sbrk stub")
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())