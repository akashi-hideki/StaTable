#!/usr/bin/env python3
"""Round-trip + compile + link test for user code markers.

Flow:
  [1/6] Generate C from XML (no merge) -> tmp/output
  [2/6] Inject user #include into file-level marker
  [3/6] Regenerate WITH merge -> user code preserved?
  [4/6] Verify user #include is still present
  [5/6] Compile with verify_c_syntax.py (--compiler gcc|both --strict)
  [6/6] Link with verify_arm_link.py (ARM Cortex-M, optional)

Exit codes:
    0 = PASS
    1 = generation failed
    2 = injection failed (marker not found)
    3 = preservation failed (user code lost after merge)
    4 = compile verification failed
    5 = link verification failed
    6 = unexpected error

Usage:
    cd code
    python tools/test_user_code_roundtrip.py
    python tools/test_user_code_roundtrip.py --skip-link
    python tools/test_user_code_roundtrip.py --compiler both --keep-tmp
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
sys.path.insert(0, str(CODE))

VERIFY_C = CODE / "tools" / "verify_c_syntax.py"
VERIFY_LINK = CODE / "tools" / "verify_arm_link.py"
DEFAULT_XML = "docs/tutorial/vending_machine.xml"
DEFAULT_TARGET = "Driver/statable_role_functions_Driver.c"
USER_INCLUDE_LINE = '#include "user_roundtrip_test.h"'


def _import_gen_helpers():
    """Import helpers from gen_output_from_xml.py."""
    from statable.xml_io import project_from_xml
    from codegen.c_code_generator import CCodeGenerator
    sys.path.insert(0, str(CODE / "tools"))
    from gen_output_from_xml import normalize_tabs, build_config
    return project_from_xml, CCodeGenerator, normalize_tabs, build_config


def generate(xml: Path, out: Path, merge: bool) -> int:
    project_from_xml, CCodeGenerator, normalize_tabs, build_config = \
        _import_gen_helpers()
    tabs, gd, role_lib, _cond, _lit, settings = \
        project_from_xml(str(xml))
    layers = normalize_tabs(tabs)
    config = build_config(settings)
    gen = CCodeGenerator(config=config)
    files = gen.generate_all_layers(layers, gd, role_lib)
    if merge:
        gen.save_generated_code_with_merge(files, str(out))
    else:
        gen.save_generated_code(files, str(out))
    return 0


def create_user_header(out_dir: Path) -> Path:
    """Create a minimal user-owned header at the output root.

    Simulates a user adding their own abstraction header that the
    generated .c file can include from the file-level marker.
    """
    header = out_dir / "user_roundtrip_test.h"
    content = (
        "#ifndef USER_ROUNDTRIP_TEST_H\n"
        "#define USER_ROUNDTRIP_TEST_H\n"
        "\n"
        "/* Simulated user-owned header for round-trip testing. */\n"
        "static inline unsigned long user_roundtrip_marker(void) {\n"
        "    return 0x5A17u;\n"
        "}\n"
        "\n"
        "#endif /* USER_ROUNDTRIP_TEST_H */\n"
    )
    header.write_text(content, encoding="utf-8", newline="\n")
    print(f"[OK]   created {header.name} in output root")
    return header


def inject_user_include(src: Path, marker_target: str) -> bool:
    """Insert USER_INCLUDE_LINE between file-level START/END markers."""
    if not src.exists():
        print(f"[FAIL] target not found: {src}")
        return False
    text = src.read_text(encoding="utf-8")
    start = "/* [[STABLE_USER_CODE_START]] */"
    end = "/* [[STABLE_USER_CODE_END]] */"
    if start not in text or end not in text:
        print(f"[FAIL] file-level markers not found in {src.name}")
        return False
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL,
    )
    replacement = f"{start}\n{USER_INCLUDE_LINE}\n{end}"
    new_text, n = pattern.subn(replacement, text, count=1)
    if n == 0:
        print("[FAIL] marker regex did not match (empty block?)")
        return False
    src.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK]   injected {USER_INCLUDE_LINE!r} into {src.name}")
    return True


def check_preserved(src: Path) -> bool:
    """Confirm USER_INCLUDE_LINE remains after merge."""
    text = src.read_text(encoding="utf-8")
    if USER_INCLUDE_LINE not in text:
        print(f"[FAIL] user include lost after merge in {src.name}")
        return False
    print(f"[OK]   user include preserved in {src.name}")
    return True


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print(f"$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(
        cmd, cwd=str(cwd) if cwd else None
    ).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml", default=DEFAULT_XML)
    ap.add_argument("--target", default=DEFAULT_TARGET)
    ap.add_argument("--compiler", default="gcc",
                    choices=["gcc", "arm", "both"])
    ap.add_argument("--std", default="c99")
    ap.add_argument("--skip-link", action="store_true",
                    help="skip ARM link verification")
    ap.add_argument("--keep-tmp", action="store_true")
    args = ap.parse_args()

    print("=" * 70)
    print("  User code round-trip + compile + link test")
    print("=" * 70)

    xml = Path(args.xml)
    if not xml.is_absolute():
        xml = (CODE / xml).resolve()
    if not xml.exists():
        print(f"[FAIL] xml not found: {xml}")
        return 1

    tmp = Path(tempfile.mkdtemp(prefix="statable_roundtrip_"))
    out = tmp / "output"

    print(f"  xml:      {xml}")
    print(f"  out:      {out}")
    print(f"  target:   {args.target}")
    print(f"  compiler: {args.compiler}")
    print(f"  skip-link: {args.skip_link}")
    print()

    try:
        # [1/6] generate
        print("[1/6] Generating C code (no merge) ...")
        if generate(xml, out, merge=False) != 0:
            return 1

        target = out / args.target
        if not target.exists():
            print(f"[FAIL] target not generated: {target}")
            return 1

        # [2/6] inject + create user header
        print()
        print("[2/6] Injecting user include into file-level marker ...")
        if not inject_user_include(target, args.target):
            return 2
        create_user_header(out)

        # [3/6] regenerate with merge
        print()
        print("[3/6] Regenerating WITH merge ...")
        if generate(xml, out, merge=True) != 0:
            return 1

        # [4/6] verify preservation
        print()
        print("[4/6] Verifying user code preservation ...")
        if not check_preserved(target):
            return 3

        # [5/6] compile verify
        print()
        print("[5/6] Compile-verifying (verify_c_syntax.py) ...")
        rc = run([
            sys.executable, str(VERIFY_C),
            "--root", str(out),
            "--compiler", args.compiler,
            "--std", args.std,
            "--strict",
            "--no-log",
        ])
        if rc != 0:
            print(f"[FAIL] compile verification returned {rc}")
            return 4

        # [6/6] link verify
        if args.skip_link:
            print()
            print("[6/6] Link verification skipped (--skip-link)")
        else:
            print()
            print("[6/6] Link-verifying (verify_arm_link.py) ...")
            link_out = tmp / "arm_link"
            rc = run([
                sys.executable, str(VERIFY_LINK),
                "--root", str(out),
                "--out", str(link_out),
            ])
            if rc != 0:
                print(f"[FAIL] link verification returned {rc}")
                return 5

        print()
        print("[PASS] user code round-trip + compile + link test")
        return 0

    except Exception as e:
        print(f"[ERROR] unexpected: {e!r}")
        import traceback
        traceback.print_exc()
        return 6

    finally:
        if args.keep_tmp:
            print(f"\n[i] tmp directory kept: {tmp}")
        else:
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())