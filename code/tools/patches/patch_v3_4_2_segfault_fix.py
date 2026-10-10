"""v3.4.2: fix Linux CI segfault in test_v2_2_p4a.py.

Root cause:
  Qt teardown at Python exit races on Linux/glibc.
  Test body passes (82/82) but process exits with SIGSEGV (139).
  Windows teardown order differs, so the bug is CI-only.

Fix:
  Flush output and use os._exit() to skip Python/Qt teardown
  entirely. 100% reliable.

This test uses the RESULT object pattern:
    ok = RESULT.summary()
    sys.exit(0 if ok else 1)
"""
from __future__ import annotations
import sys
from pathlib import Path

TEST = (Path(__file__).resolve().parent.parent.parent.parent
        / "code" / "tests" / "test_v2_2_p4a.py")

OLD_TAIL = """    ok = RESULT.summary()
    sys.exit(0 if ok else 1)"""

NEW_TAIL = """    ok = RESULT.summary()
    # ------------------------------------------------------------------
    # [v3.4.2] Linux CI fix: skip Python/Qt teardown to avoid SIGSEGV.
    # Qt C++ destructors race on Linux glibc at process exit; the test
    # body already passed, so exit the process immediately after
    # flushing stdout/stderr.
    # ------------------------------------------------------------------
    sys.stdout.flush()
    sys.stderr.flush()
    import os as _os
    _os._exit(0 if ok else 1)"""


def main() -> int:
    if not TEST.exists():
        print(f"[ERR] {TEST} not found")
        return 1
    text = TEST.read_text(encoding="utf-8")

    if "_os._exit" in text:
        print("[SKIP] test_v2_2_p4a.py already uses os._exit")
        return 0

    if OLD_TAIL not in text:
        print("[ERR] tail marker not found:")
        print(repr(OLD_TAIL))
        print("       Please inspect the end of the file manually.")
        return 1

    text = text.replace(OLD_TAIL, NEW_TAIL, 1)
    TEST.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK]   patched {TEST.name}: sys.exit -> os._exit")
    return 0


if __name__ == "__main__":
    sys.exit(main())