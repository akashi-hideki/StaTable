#!/usr/bin/env python3
"""verify_comm_monitor_output.py - Verify comm_monitor generated code.

Checks:
  1. Required statable_comm_* files exist.
  2. statable_comm_registry.h uses `const volatile void *ptr`.
  3. statable_comm_registry.c uses volatile-preserving casts.
  4. If by_layer, statable_types.h aggregator exists and is well-formed.
  5. All .c files compile with gcc -std=c99 -Wall -Wextra -Werror
     (using an ASCII tempdir to avoid MinGW CP932 path bugs).

Usage:
    python code/tools/verify_comm_monitor_output.py --root output
    python code/tools/verify_comm_monitor_output.py --root output --compiler both
    python code/tools/verify_comm_monitor_output.py --root output --no-strict
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REQUIRED = [
    "statable_comm_config.h",
    "statable_comm_monitor.c",
    "statable_comm_monitor.h",
    "statable_comm_registry.c",
    "statable_comm_registry.h",
    "statable_comm_ring.c",
    "statable_comm_ring.h",
]


def _find_one(root: Path, name: str) -> Path | None:
    hits = list(root.rglob(name))
    return hits[0] if hits else None


def check_files(root: Path) -> list[str]:
    errs: list[str] = []
    print("[1] Required comm_monitor files")
    for name in REQUIRED:
        p = _find_one(root, name)
        if p is None:
            errs.append(f"missing: {name}")
            print(f"  FAIL  {name}")
        else:
            print(f"  OK    {p.relative_to(root)}")
    return errs


def check_volatile(root: Path) -> list[str]:
    errs: list[str] = []
    print("\n[2] volatile preservation in registry")
    h = _find_one(root, "statable_comm_registry.h")
    c = _find_one(root, "statable_comm_registry.c")
    if h is None or c is None:
        return ["registry.h/.c not found"]

    h_text = h.read_text(encoding="utf-8")
    if "const volatile void *ptr" in h_text:
        print("  OK    registry.h: const volatile void *ptr")
    else:
        errs.append("registry.h: missing const volatile void *ptr")
        print("  FAIL  registry.h: ptr is not volatile")

    c_text = c.read_text(encoding="utf-8")
    for t in ("uint8_t", "uint16_t", "uint32_t"):
        if re.search(rf"const\s+volatile\s+{t}\s*\*", c_text):
            print(f"  OK    registry.c: const volatile {t} *")
        else:
            errs.append(f"registry.c: missing const volatile {t} *")
            print(f"  FAIL  registry.c: missing const volatile {t} *")
    return errs


def check_types_aggregator(root: Path) -> list[str]:
    errs: list[str] = []
    print("\n[3] statable_types.h aggregator (by_layer only)")
    common = _find_one(root, "statable_types_common.h")
    types_h = _find_one(root, "statable_types.h")
    is_by_layer = common is not None and len(list(root.rglob("statable_types_*.h"))) > 1

    if not is_by_layer:
        print("  SKIP  flat mode (no aggregator required)")
        return errs
    if types_h is None:
        errs.append("by_layer mode but statable_types.h missing")
        print("  FAIL  statable_types.h not found")
        return errs
    txt = types_h.read_text(encoding="utf-8")
    if "#pragma once" in txt and "statable_types_common.h" in txt \
            and "extern SystemContext_t g_ctx;" in txt:
        print("  OK    statable_types.h aggregator well-formed")
    else:
        errs.append("statable_types.h aggregator malformed")
        print("  FAIL  statable_types.h missing #pragma once / common include / g_ctx extern")
    return errs


def _include_dirs(root: Path) -> list[Path]:
    dirs = [root] + [p for p in root.rglob("*") if p.is_dir()]
    return dirs


def check_compile(root: Path, compilers: list[str], strict: bool) -> list[str]:
    errs: list[str] = []
    print(f"\n[4] compile .c files ({', '.join(compilers)}{', -Werror' if strict else ''})")

    # Copy to ASCII tempdir to avoid MinGW CP932 path issues
    tmp = Path(tempfile.mkdtemp(prefix="cm_verify_"))
    try:
        for item in root.rglob("*"):
            if item.is_file():
                rel = item.relative_to(root)
                dst = tmp / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst)

        inc = [f"-I{d}" for d in _include_dirs(tmp)]
        c_files = sorted(tmp.rglob("*.c"))
        if not c_files:
            errs.append("no .c files found")
            return errs

        for cc in compilers:
            if shutil.which(cc) is None:
                print(f"  SKIP  {cc} not in PATH")
                continue
            flags = [cc, "-std=c99", "-Wall", "-Wextra"]
            if strict:
                flags += ["-Werror", "-Wno-error=unused-parameter"]
            fail = 0
            for src in c_files:
                obj = src.with_suffix(".o")
                r = subprocess.run(
                    flags + inc + ["-c", str(src), "-o", str(obj)],
                    capture_output=True, text=True,
                )
                if r.returncode != 0:
                    fail += 1
                    print(f"  FAIL  [{cc}] {src.relative_to(tmp)}")
                    print("        " + r.stderr.strip().replace("\n", "\n        "))
            if fail == 0:
                print(f"  OK    [{cc}] {len(c_files)}/{len(c_files)} compiled")
            else:
                errs.append(f"{cc}: {fail}/{len(c_files)} failed")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="output", help="generation root (default: output)")
    ap.add_argument("--compiler", choices=["gcc", "arm", "both"], default="gcc")
    ap.add_argument("--no-strict", action="store_true", help="disable -Werror")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"ERROR: {root} is not a directory", file=sys.stderr)
        return 2

    compilers = {
        "gcc": ["gcc"],
        "arm": ["arm-none-eabi-gcc"],
        "both": ["gcc", "arm-none-eabi-gcc"],
    }[args.compiler]

    print("=" * 72)
    print(f"verify_comm_monitor_output  root={root}")
    print("=" * 72)

    errs: list[str] = []
    errs += check_files(root)
    errs += check_volatile(root)
    errs += check_types_aggregator(root)
    errs += check_compile(root, compilers, strict=not args.no_strict)

    print("\n" + "=" * 72)
    if errs:
        print(f"RESULT: FAIL ({len(errs)} issue(s))")
        for e in errs:
            print(f"  - {e}")
        print("=" * 72)
        return 1
    print("RESULT: ALL PASS")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())