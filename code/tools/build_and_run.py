"""build_and_run.py

Build & run helper for eclipse_installer projects (no make required).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CC = "arm-none-eabi-gcc"
OBJCOPY = "arm-none-eabi-objcopy"
QEMU = r"C:\Program Files\qemu\qemu-system-arm.exe"

CPU = ["-mcpu=cortex-m4", "-mthumb"]
CFLAGS_COMMON = CPU + ["-ffunction-sections", "-fdata-sections",
                       "-Og", "-g3", "-std=c99"]


def build(project: Path) -> Path:
    build_dir = project / "build"
    build_dir.mkdir(exist_ok=True)
    obj_dir = build_dir / "obj"
    obj_dir.mkdir(exist_ok=True)

    # Include paths: project root + every directory under project
    inc_dirs = [project]
    for p in project.rglob("*"):
        if p.is_dir() and "build" not in p.parts:
            inc_dirs.append(p)
    inc_flags = [f"-I{d}" for d in inc_dirs]

    # Collect sources
    c_files = [p for p in project.rglob("*.c")
               if "build" not in p.parts]
    s_files = [p for p in project.rglob("*.s")
               if "build" not in p.parts]

    objs = []
    for src in c_files + s_files:
        rel = src.relative_to(project)
        obj = obj_dir / (str(rel).replace("\\", "_").replace("/", "_") + ".o")
        if src.suffix.lower() == ".s":
            cmd = ([CC, "-x", "assembler-with-cpp"]
                   + CPU + inc_flags
                   + ["-c", str(src), "-o", str(obj)])
        else:
            cmd = ([CC] + CFLAGS_COMMON + inc_flags
                   + ["-c", str(src), "-o", str(obj)])
        print(f"[CC] {rel}")
        r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print(r.stderr)
            raise SystemExit(f"[FAIL] compile: {src}")
        objs.append(str(obj))

    elf = build_dir / "firmware.elf"
    bin_ = build_dir / "firmware.bin"
    link_cmd = (
        [CC] + CPU
        + ["-specs=nano.specs"]
        + ["-T", str(project / "linker_stm32f405.ld")]
        + ["-Wl,--gc-sections", "-Wl,--print-memory-usage",
           f"-Wl,-Map={build_dir}/firmware.map"]
        + objs
        + ["-lc", "-lm", "-lgcc", "-o", str(elf)]
    )
    print("[LD] firmware.elf")
    r = subprocess.run(link_cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
        raise SystemExit("[FAIL] link")

    subprocess.run([OBJCOPY, "-O", "binary", str(elf), str(bin_)],
                   check=True)
    print(f"[OK] {elf}  ({elf.stat().st_size} bytes)")
    print(f"[OK] {bin_}  ({bin_.stat().st_size} bytes)")
    return elf


def run_qemu(elf: Path, timeout: int = 5) -> None:
    cmd = [
        QEMU,
        "-M", "netduinoplus2",
        "-cpu", "cortex-m4",
        "-nographic",
        "-kernel", str(elf),
        "-serial", f"file:{Path(str(elf)).parent / 'uart.log'}",
    ]
    print(f"\n[QEMU] {' '.join(cmd)}")
    print("[QEMU] Press Ctrl+C to stop.")
    try:
        subprocess.run(cmd, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"\n[QEMU] stopped after {timeout}s (expected)")


if __name__ == "__main__":
    proj = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    elf = build(proj)
    if len(sys.argv) > 2 and sys.argv[2] == "--run":
        run_qemu(elf)
