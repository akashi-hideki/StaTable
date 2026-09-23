#!/usr/bin/env python3
"""StaTable R-13(B) test suite: ARM link verification.

Verifies that verify_arm_link.py:
  - produces firmware.elf / firmware.bin for generated output
  - uses the template files (linker.ld / startup.s / stub_main.c)
  - fails cleanly when a symbol is missing

Run:
  python tests/test_v2_5_p8.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  [PASS] {name}")

    def fail(self, name, msg=""):
        self.failed += 1
        self.errors.append((name, msg))
        print(f"  [FAIL] {name}")
        if msg:
            print(f"         {msg}")

    def summary(self):
        total = self.passed + self.failed
        print()
        print("=" * 70)
        print(f"  TOTAL: {total}  PASSED: {self.passed}  FAILED: {self.failed}")
        print("=" * 70)
        return self.failed == 0


R = TestResult()


def check(name, cond, msg=""):
    if cond:
        R.ok(name)
    else:
        R.fail(name, msg)
    return cond


def _has_arm_toolchain() -> bool:
    return shutil.which("arm-none-eabi-gcc") is not None


# ======================================================================
# Fixtures
# ======================================================================
def _generate_output_vending() -> Path | None:
    """Generate output_vending from the tutorial XML."""
    xml = PROJECT_ROOT / "docs" / "tutorial" / "vending_machine.xml"
    if not xml.exists():
        return None
    out = PROJECT_ROOT / "output_vending"
    subprocess.run(
        [sys.executable, "tools/gen_output_from_xml.py",
         "--xml", str(xml), "--out", str(out)],
        cwd=str(PROJECT_ROOT), check=True, capture_output=True,
    )
    return out


# ======================================================================
# [1] Template files exist
# ======================================================================
def test_templates_present():
    print("\n[1] arm_template files present")
    tdir = PROJECT_ROOT / "tools" / "arm_template"
    check("linker.ld exists", (tdir / "linker.ld").is_file())
    check("startup.s exists", (tdir / "startup.s").is_file())
    check("stub_main.c exists", (tdir / "stub_main.c").is_file())


# ======================================================================
# [2] verify_arm_link.py exists & --help works
# ======================================================================
def test_script_help():
    print("\n[2] verify_arm_link.py --help")
    script = PROJECT_ROOT / "tools" / "verify_arm_link.py"
    check("script exists", script.is_file())
    if not script.is_file():
        return
    p = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    check("--help exit 0", p.returncode == 0)
    check("--root documented", "--root" in p.stdout)


# ======================================================================
# [3] Link test (requires arm-none-eabi-gcc)
# ======================================================================
def test_link_success():
    print("\n[3] Link verification on output_vending")
    if not _has_arm_toolchain():
        print("  [SKIP] arm-none-eabi-gcc not in PATH")
        return

    out_v = _generate_output_vending()
    if out_v is None:
        print("  [SKIP] vending_machine.xml not found")
        return

    p = subprocess.run(
        [sys.executable, "tools/verify_arm_link.py",
         "--root", str(out_v),
         "--out", str(PROJECT_ROOT / "verify_report" / "arm_link")],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    check("link exit 0", p.returncode == 0,
          f"stderr:\n{p.stderr[-500:]}")
    elf = PROJECT_ROOT / "verify_report" / "arm_link" / "firmware.elf"
    bin_ = PROJECT_ROOT / "verify_report" / "arm_link" / "firmware.bin"
    check("firmware.elf produced", elf.is_file())
    check("firmware.bin produced", bin_.is_file())


# ======================================================================
# [4] Link fails on missing symbol (negative test)
# ======================================================================
def test_link_detects_missing_symbol():
    print("\n[4] Link detects unresolved symbols (negative)")
    if not _has_arm_toolchain():
        print("  [SKIP] arm-none-eabi-gcc not in PATH")
        return

    # Build a tiny project with an unresolved symbol
    tmp = PROJECT_ROOT / "verify_report" / "arm_link_bad"
    if tmp.exists():
        # [Windows] rmtree can fail with PermissionError if a
        # file is locked (antivirus / editor / OS).  Ignore the
        # error: bad.c is overwritten below, and stale .o files
        # are harmless (regenerated each run).
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "bad.c").write_text(
        "extern void undefined_function(void);\n"
        "int bad_entry(void) { undefined_function(); return 0; }\n",
        encoding="utf-8",
    )

    p = subprocess.run(
        [sys.executable, "tools/verify_arm_link.py",
         "--root", str(tmp),
         "--out", str(PROJECT_ROOT / "verify_report" / "arm_link_bad_out")],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
    )
    check("link exit != 0", p.returncode != 0)

    combined = (p.stdout or "") + (p.stderr or "")
    # The exact wording depends on the toolchain ("FAIL", "error",
    # "undefined reference", ...). Accept any of them.
    has_error = (
        "FAIL" in combined
        or "error" in combined.lower()
        or "undefined" in combined.lower()
    )
    check("error message present", has_error,
          f"stdout+stderr tail:\n{combined[-600:]}")


# ======================================================================
# Main
# ======================================================================
def main():
    print("=" * 70)
    print("  StaTable R-13(B) (ARM link verification)")
    print("=" * 70)

    test_templates_present()
    test_script_help()
    test_link_success()
    test_link_detects_missing_symbol()

    ok = R.summary()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()