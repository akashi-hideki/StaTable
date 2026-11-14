"""v3.4.3: universal Linux CI segfault fix for all Qt test files.

Applies the same fix as test_v2_2_p4a.py (v3.4.2) to the remaining
16 Qt-using test files:
  1. Find the LAST `sys.exit(` call in each file
  2. Replace it with `os._exit(` (skip Python/Qt teardown)
  3. Ensure `import os` exists at the top if not present

Rationale:
  On Linux glibc, Qt C++ destructors race with Python interpreter
  shutdown. This causes random SIGSEGV (exit 139) AFTER the test
  body completes successfully. os._exit() bypasses this entirely.

  Symptom is flaky: different tests fail on different runs
  (observed: test_v2_2_p4a.py, then test_v2_2_p3.py).
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

TESTS = (Path(__file__).resolve().parent.parent.parent.parent
         / "code" / "tests")

FILES = [
    "test_v2_2_p3.py",
    "test_v2_2_p4b.py",
    "test_v2_3_p1.py",
    "test_v2_5_p1.py",
    "test_v2_5_p11.py",
    "test_v2_5_p5.py",
    "test_v2_5_p6.py",
    "test_v2_5_p9.py",
    "test_v2_6_p2.py",
    "test_v2_6_p3.py",
    "test_v2_7_p4.py",
    "test_v2_8_p4_gui_integration.py",
    "test_v3_2_s1_wizard.py",
    "test_v3_2_s2_signals.py",
    "test_v3_4_0_signal_safety.py",
    "test_v3_4_0_state_actions.py",
]


def ensure_import_os(text: str) -> str:
    """Ensure `import os` is present at module top-level."""
    if re.search(r"^import os\b", text, re.MULTILINE):
        return text
    # Insert after __future__ import if present
    m = re.search(r"^(from __future__ import [^\n]+\n)", text, re.MULTILINE)
    if m:
        return text[:m.end()] + "import os\n" + text[m.end():]
    # Otherwise, at the very top
    return "import os\n" + text


def patch_file(fname: str) -> str:
    path = TESTS / fname
    if not path.exists():
        return f"[MISS] {fname}"

    text = path.read_text(encoding="utf-8")

    if "os._exit" in text:
        return f"[SKIP] {fname}: already uses os._exit"

    # Find LAST occurrence of sys.exit(
    idx = text.rfind("sys.exit(")
    if idx == -1:
        return f"[WARN] {fname}: no sys.exit() found"

    # Replace only that occurrence
    new_text = text[:idx] + "os._exit(" + text[idx + len("sys.exit("):]

    # Ensure import os
    new_text = ensure_import_os(new_text)

    path.write_text(new_text, encoding="utf-8", newline="\n")
    line_no = text[:idx].count("\n") + 1
    return f"[OK]   {fname} (L{line_no})"


def main() -> int:
    print("=" * 74)
    print("  v3.4.3 universal segfault fix")
    print("=" * 74)
    ok = skip = err = 0
    for fname in FILES:
        msg = patch_file(fname)
        print(f"  {msg}")
        if msg.startswith("[OK]"):
            ok += 1
        elif msg.startswith("[SKIP]"):
            skip += 1
        else:
            err += 1
    print()
    print(f"  OK: {ok}   SKIP: {skip}   ERR/WARN: {err}")
    print("=" * 74)
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())