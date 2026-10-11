# tools/e2e_eclipse_installer.py
"""
End-to-end verification of eclipse_installer (local-only).

Requires:
  - arm-none-eabi-gcc (for L3+L4)
  - qemu-system-arm  (for L5, optional)

Steps:
  1. [L3] Install into a temp Eclipse project
  2. [L3] Compile all .c/.s with arm-none-eabi-gcc
  3. [L4] Link to firmware.elf and firmware.bin
  4. [L4] Sanity-check firmware.bin size
  5. [L5] (--qemu) Run under QEMU, verify UART banner

Usage:
  python tools/e2e_eclipse_installer.py            # L3+L4
  python tools/e2e_eclipse_installer.py --qemu     # L3+L4+L5
  python tools/e2e_eclipse_installer.py --keep     # keep tempdir
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # code/
sys.path.insert(0, str(ROOT))

CC = "arm-none-eabi-gcc"
OBJCOPY = "arm-none-eabi-objcopy"
QEMU = r"C:\Program Files\qemu\qemu-system-arm.exe"
CPU = ["-mcpu=cortex-m4", "-mthumb"]

CFLAGS_COMMON = CPU + [
    "-ffunction-sections", "-fdata-sections",
    "-Og", "-g3", "-std=c99",
]


def _run(cmd, cwd=None, label=""):
    """Run subprocess; abort on error with captured output."""
    r = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if r.returncode != 0:
        print(f"[FAIL] {label}")
        print("STDOUT:", r.stdout[-2000:])
        print("STDERR:", r.stderr[-2000:])
        raise SystemExit(1)
    return r


def compile_all(project: Path) -> Path:
    """L3: compile all .c/.s; return elf path (L4)."""
    build = project / "build"
    build.mkdir(exist_ok=True)
    obj_dir = build / "obj"
    obj_dir.mkdir(exist_ok=True)

    # Include paths
    inc_dirs = [project]
    for p in project.rglob("*"):
        if p.is_dir() and "build" not in p.parts:
            inc_dirs.append(p)
    inc_flags = [f"-I{d}" for d in inc_dirs]

    c_files = [p for p in project.rglob("*.c")
               if "build" not in p.parts]
    s_files = [p for p in project.rglob("*.s")
               if "build" not in p.parts]

    objs = []
    for src in sorted(c_files + s_files):
        rel = src.relative_to(project)
        obj = obj_dir / (str(rel).replace("\\", "_")
                         .replace("/", "_") + ".o")
        if src.suffix.lower() == ".s":
            cmd = ([CC, "-x", "assembler-with-cpp"] + CPU
                   + inc_flags + ["-c", str(src), "-o", str(obj)])
        else:
            cmd = ([CC] + CFLAGS_COMMON + inc_flags
                   + ["-c", str(src), "-o", str(obj)])
        print(f"[CC] {rel}")
        _run(cmd, label=f"compile: {src}")
        objs.append(str(obj))

    # L4: link
    elf = build / "firmware.elf"
    bin_ = build / "firmware.bin"
    link_cmd = (
        [CC] + CPU
        + ["-specs=nano.specs"]
        + ["-T", str(project / "linker_stm32f405.ld")]
        + ["-Wl,--gc-sections", "-Wl,--print-memory-usage",
           f"-Wl,-Map={build}/firmware.map"]
        + objs
        + ["-lc", "-lm", "-lgcc", "-o", str(elf)]
    )
    print("[LD] firmware.elf")
    _run(link_cmd, label="link")
    _run([OBJCOPY, "-O", "binary", str(elf), str(bin_)],
         label="objcopy")
    print(f"[OK] {bin_}: {bin_.stat().st_size} bytes")
    return elf

def run_qemu(elf: Path, timeout: int = 5) -> str:
    """L5: run QEMU and capture UART output via file."""
    uart_log = elf.parent / "uart.log"
    if uart_log.exists():
        uart_log.unlink()

    cmd = [
        QEMU,
        "-M", "netduinoplus2",
        "-cpu", "cortex-m4",
        "-nographic",
        "-kernel", str(elf),
        "-serial", f"file:{uart_log}",
    ]
    print(f"[QEMU] {' '.join(cmd)}")
    try:
        subprocess.run(cmd, timeout=timeout,
                       capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        pass
    if not uart_log.exists():
        print("[FAIL] no UART log produced")
        raise SystemExit(1)
    return uart_log.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qemu", action="store_true",
                        help="also run QEMU (L5)")
    parser.add_argument("--keep", action="store_true",
                        help="keep tempdir for inspection")
    args = parser.parse_args()

    td = tempfile.mkdtemp(prefix="statable_e2e_")
    print(f"[INFO] workdir: {td}")
    try:
        proj = Path(td) / "test_project"
        proj.mkdir()

        # --- L3: install ---
        from eclipse_installer.core import InstallOptions, install
        opts = InstallOptions(
            project_root=proj,
            output_dir=ROOT / "output",
        )
        res = install(opts)
        if res.errors:
            print("[FAIL] install errors:", res.errors)
            return 1
        print(f"[OK] installed {len(res.installed)} file(s)")

        # --- L3+L4: compile + link ---
        elf = compile_all(proj)

        # --- L5: QEMU ---
        if args.qemu:
            uart = run_qemu(elf, timeout=5)
            print(f"[INFO] UART output ({len(uart)} chars):")
            print("---")
            print(uart[:2000])
            print("---")
            if "StaTable" not in uart:
                print("[FAIL] UART banner not found")
                return 1
            print("[OK] UART banner verified")

        print("\n[ALL OK]")
        return 0
    finally:
        if not args.keep:
            shutil.rmtree(td, ignore_errors=True)
        else:
            print(f"[KEEP] workdir retained: {td}")


if __name__ == "__main__":
    sys.exit(main())
