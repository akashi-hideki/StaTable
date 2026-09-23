#!/usr/bin/env python3
# code/tools/verify_arm_link.py
"""Verify the generated framework can be LINKED for ARM Cortex-M.

Complements verify_c_syntax.py (-fsyntax-only) by performing an
actual link step:

  1. Compiles every .c under --root to .o (arm-none-eabi-gcc)
  2. Compiles tools/arm_template/startup.s and stub_main.c
  3. Links all .o with tools/arm_template/linker.ld
  4. Produces <out>.elf and <out>.bin
  5. Reports unresolved symbols

This catches link-time issues that a syntax-only check misses,
e.g. a role function referenced by the transition table but never
generated.

The stub main and generic linker script are NOT for production;
the "user provides main / startup / linker script" contract is
documented in docs/OSAL_PORTING_GUIDE_ja.md.

Usage:
    python tools/verify_arm_link.py --root output
    python tools/verify_arm_link.py --root output --out verify_report/arm_link
"""

from __future__ import annotations

import argparse
import datetime as _dt
import shutil
import subprocess
import sys
from pathlib import Path

CC = "arm-none-eabi-gcc"
OBJCOPY = "arm-none-eabi-objcopy"
TEMPLATE_DIR = Path("tools/arm_template")
STD = "c99"
CPU_FLAGS = ["-mcpu=cortex-m4", "-mthumb"]
LINK_SPECS = ["-specs=nano.specs", "-specs=nosys.specs"]


class Logger:
    def __init__(self, log_path: Path | None):
        self._fh = None
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(log_path, "w", encoding="utf-8", newline="\n")

    def write(self, text: str = "") -> None:
        print(text)
        if self._fh is not None:
            self._fh.write(text + "\n")

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()


def discover_layout(root: Path) -> dict:
    include_dirs = set()
    for h in root.rglob("*.h"):
        include_dirs.add(h.parent)
    return {
        "include_dirs": sorted(include_dirs),
        "c_files": sorted(root.rglob("*.c")),
    }


def run(cmd, log: Logger, capture: bool = True):
    log.write(f"  $ {' '.join(str(x) for x in cmd)}")
    p = subprocess.run(
        cmd, capture_output=capture, text=True,
        encoding="utf-8", errors="replace",
    )
    if p.returncode != 0:
        if p.stdout:
            log.write(p.stdout.rstrip())
        if p.stderr:
            log.write(p.stderr.rstrip())
    return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default=None,
                    help="output dir (default: verify_report/arm_link)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"ERROR: {root} not found", file=sys.stderr)
        return 1

    if shutil.which(CC) is None:
        print(f"ERROR: {CC} not found in PATH", file=sys.stderr)
        return 2

    if not TEMPLATE_DIR.is_dir():
        print(f"ERROR: {TEMPLATE_DIR} not found (run from code/)",
              file=sys.stderr)
        return 2

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out) if args.out else Path("verify_report/arm_link")
    out_dir.mkdir(parents=True, exist_ok=True)
    build_dir = out_dir / "obj"
    build_dir.mkdir(parents=True, exist_ok=True)

    log_path = Path("verify_report") / f"verify_arm_link_{ts}.log"
    log = Logger(log_path)

    try:
        log.write("=" * 78)
        log.write("  ARM Link Verification Report")
        log.write("=" * 78)
        log.write(f"  Timestamp:  {_dt.datetime.now().astimezone()}")
        log.write(f"  Root:       {root.resolve()}")
        log.write(f"  Output:     {out_dir.resolve()}")
        log.write(f"  Compiler:   {CC}")
        log.write("")

        layout = discover_layout(root)
        if not layout["c_files"]:
            log.write(f"  ERROR: no .c files under {root}")
            return 1
        log.write(f"  C files:    {len(layout['c_files'])}")
        log.write(f"  Include:    {len(layout['include_dirs'])} dirs")
        log.write("")

        # --- 1. Compile generated .c to .o ---
        log.write("-" * 78)
        log.write("  Step 1: Compile generated C to object files")
        log.write("-" * 78)
        objs = []
        for src in layout["c_files"]:
            rel = src.relative_to(root)
            obj = build_dir / (str(rel).replace("/", "_").replace("\\", "_")
                               + ".o")
            cmd = [CC, f"-std={STD}", *CPU_FLAGS,
                   "-ffunction-sections", "-fdata-sections",
                   "-Wall", "-Wextra"]
            for inc in layout["include_dirs"]:
                cmd += ["-I", str(inc)]
            cmd += ["-c", str(src), "-o", str(obj)]
            rc = run(cmd, log)
            if rc != 0:
                log.write(f"  [FAIL] compile: {rel}")
                return 1
            objs.append(obj)
        log.write(f"  [OK]   compiled {len(objs)} object file(s)")
        log.write("")

        # --- 2. Compile template files ---
        log.write("-" * 78)
        log.write("  Step 2: Compile startup.s and stub_main.c")
        log.write("-" * 78)
        startup_s = TEMPLATE_DIR / "startup.s"
        stub_main = TEMPLATE_DIR / "stub_main.c"
        startup_o = build_dir / "startup.o"
        stub_main_o = build_dir / "stub_main.o"

        rc = run([CC, *CPU_FLAGS, "-c", str(startup_s),
                  "-o", str(startup_o)], log)
        if rc != 0:
            log.write("  [FAIL] startup.s")
            return 1
        rc = run([CC, f"-std={STD}", *CPU_FLAGS, "-c", str(stub_main),
                  "-o", str(stub_main_o)], log)
        if rc != 0:
            log.write("  [FAIL] stub_main.c")
            return 1
        log.write("  [OK]   template objects compiled")
        log.write("")

        # --- 3. Link ---
        log.write("-" * 78)
        log.write("  Step 3: Link all objects with linker.ld")
        log.write("-" * 78)
        linker_ld = TEMPLATE_DIR / "linker.ld"
        elf = out_dir / "firmware.elf"
        bin_ = out_dir / "firmware.bin"
        map_ = out_dir / "firmware.map"

        cmd = [CC, *CPU_FLAGS,
               "-nostartfiles", *LINK_SPECS,
               f"-T{linker_ld}",
               f"-Wl,-Map={map_}",
               "-o", str(elf),
               str(startup_o), str(stub_main_o)]
        cmd += [str(o) for o in objs]
        rc = run(cmd, log)
        if rc != 0:
            log.write("")
            log.write("  [FAIL] link failed (see messages above)")
            log.write("         ^ unresolved symbols are reported here")
            return 1

        if not elf.exists():
            log.write("  [FAIL] firmware.elf not produced")
            return 1
        log.write(f"  [OK]   {elf.name} ({elf.stat().st_size} bytes)")
        log.write("")

        # --- 4. objcopy to .bin ---
        log.write("-" * 78)
        log.write("  Step 4: Convert ELF to binary")
        log.write("-" * 78)
        rc = run([OBJCOPY, "-O", "binary", str(elf), str(bin_)], log)
        if rc != 0 or not bin_.exists():
            log.write("  [FAIL] objcopy failed")
            return 1
        log.write(f"  [OK]   {bin_.name} ({bin_.stat().st_size} bytes)")
        log.write("")

        log.write("=" * 78)
        log.write("  RESULT: LINK PASS")
        log.write("=" * 78)
        log.write(f"  Log: {log_path.resolve()}")
        return 0

    finally:
        log.close()


if __name__ == "__main__":
    sys.exit(main())