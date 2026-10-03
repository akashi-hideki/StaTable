#!/usr/bin/env python3
"""Compile-verify user code injection into generated C code.

Flow:
  1. Generate C from XML into a temp output directory
  2. Inject user logic between [[STABLE_USER_CODE_START:<name>]] / END
     markers in a target .c file
  3. Run tools/verify_c_syntax.py --root <tmp> to compile-check
  4. Report PASS / FAIL

Usage:
    cd code
    python tools/test_user_code_compile.py
    python tools/test_user_code_compile.py --compiler both
    python tools/test_user_code_compile.py --keep-tmp
    python tools/test_user_code_compile.py --marker Driver_ReadButton

Exit codes:
    0 = PASS
    1 = generation failed
    2 = target not found
    3 = injection failed
    4 = compile verification failed
    5 = unexpected error
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent
GEN = CODE / "tools" / "gen_output_from_xml.py"
VERIFY = CODE / "tools" / "verify_c_syntax.py"
DEFAULT_XML = "docs/tutorial/vending_machine.xml"
DEFAULT_TARGET_GLOB = "statable_role_functions_Driver.c"
DEFAULT_MARKER = "Driver_ReadCoinSensor"

# Injected between START/END markers (replaces the (void) suppression block)
USER_CODE_BLOCK = """\
    /* --- auto-generated: unused-variable suppression ---
     *     Delete each (void) line once you start using the
     *     corresponding variable. Keeping them all is
     *     harmless (no-op).                                   */
    (void)from_state;   /* suppress unused warning */
    (void)event;        /* suppress unused warning */
    (void)transition_id;   /* suppress unused warning */
    (void)change;   /* suppress unused warning */
    (void)stock;   /* suppress unused warning */
    (void)item_id;   /* suppress unused warning */
    (void)error_code;   /* suppress unused warning */
    (void)g_system_tick;   /* suppress unused warning */

    /* === user logic (injected by test_user_code_compile) === */
    {
        uint32_t coin_in = 100;   /* local var (C99: mid-block OK) */
        *coin_value = coin_in;
        *balance += coin_in;
        if (*balance >= *price) {
            ret = 1;
        }
    }
"""


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None)


def inject(src: Path, marker: str, block: str) -> bool:
    text = src.read_text(encoding="utf-8")
    start = f"/* [[STABLE_USER_CODE_START:{marker}]] */"
    end = f"/* [[STABLE_USER_CODE_END:{marker}]] */"
    if start not in text or end not in text:
        print(f"[FAIL] markers not found in {src.name}")
        print(f"       searching START: {start}")
        print(f"                 END:   {end}")
        return False
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    replacement = start + "\n" + block + end
    new_text, n = pattern.subn(replacement, text, count=1)
    if n == 0:
        print("[FAIL] pattern did not match")
        return False
    src.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK]   injected user code into {src.name} (marker={marker})")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml", default=DEFAULT_XML)
    ap.add_argument("--target-glob", default=DEFAULT_TARGET_GLOB,
                    help="glob for target .c (searched recursively)")
    ap.add_argument("--marker", default=DEFAULT_MARKER)
    ap.add_argument("--compiler", default="gcc",
                    choices=["gcc", "arm", "both"])
    ap.add_argument("--std", default="c99")
    ap.add_argument("--keep-tmp", action="store_true",
                    help="do not delete the temp output directory")
    args = ap.parse_args()

    print("=" * 70)
    print("  User code compile test")
    print("=" * 70)

    xml = Path(args.xml)
    if not xml.is_absolute():
        xml = (CODE / xml).resolve()
    if not xml.exists():
        print(f"[FAIL] xml not found: {xml}")
        return 1

    tmp = Path(tempfile.mkdtemp(prefix="statable_user_code_"))
    out = tmp / "output"

    print(f"  xml:       {xml}")
    print(f"  out:       {out}")
    print(f"  target:    {args.target_glob}")
    print(f"  marker:    {args.marker}")
    print(f"  compiler:  {args.compiler}")
    print(f"  std:       {args.std}")
    print()

    try:
        # [1] generate
        print("[1/4] Generating C code ...")
        r = run([sys.executable, str(GEN),
                 "--xml", str(xml), "--out", str(out)])
        if r.returncode != 0:
            print(f"[FAIL] generation returned {r.returncode}")
            return 1

        # [2] locate target
        print()
        print("[2/4] Locating target file ...")
        matches = list(out.rglob(args.target_glob))
        if not matches:
            print(f"[FAIL] no match for {args.target_glob}")
            print("       candidates:")
            for p in sorted(out.rglob("*.c")):
                print(f"         {p.relative_to(out)}")
            return 2
        target = matches[0]
        print(f"[OK]   target: {target.relative_to(out)}")

        # [3] inject
        print()
        print("[3/4] Injecting user code ...")
        if not inject(target, args.marker, USER_CODE_BLOCK):
            return 3

        # [4] verify
        print()
        print("[4/4] Compile-verifying ...")
        r = run([sys.executable, str(VERIFY),
                 "--root", str(out),
                 "--compiler", args.compiler,
                 "--std", args.std,
                 "--strict",
                 "--no-log"])
        if r.returncode != 0:
            print(f"[FAIL] verify returned {r.returncode}")
            if args.keep_tmp:
                print(f"       tmp kept at: {tmp}")
            return 4

        print()
        print("[PASS] user code compile test")
        return 0

    except Exception as e:
        print(f"[ERROR] unexpected: {e!r}")
        return 5

    finally:
        if args.keep_tmp:
            print(f"\n[i] tmp directory kept: {tmp}")
        else:
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())