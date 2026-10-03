#!/usr/bin/env python3
"""Frozen EXE smoke test launcher.

Builds StaTable via PyInstaller and runs the packaged StaTable.exe
with --smoke-test to verify that the frozen application starts and
exits cleanly without hanging.

Exit codes:
    0 = PASS
    1 = PyInstaller build failed
    2 = exe not found
    3 = smoke test timed out (hang detected)
    4 = smoke test returned non-zero exit code
    5 = unexpected error

Usage:
    cd code
    python tools/smoke_frozen.py                 # build + smoke
    python tools/smoke_frozen.py --skip-build    # use existing exe
    python tools/smoke_frozen.py --timeout 120
    python tools/smoke_frozen.py --exe path/to/exe
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "StaTable.spec"
DEFAULT_EXE = ROOT / "dist" / "StaTable" / "StaTable.exe"

EXIT_PASS = 0
EXIT_BUILD_FAILED = 1
EXIT_EXE_MISSING = 2
EXIT_TIMEOUT = 3
EXIT_NONZERO = 4
EXIT_UNEXPECTED = 5


def _force_rmtree(path: Path, retries: int = 3, delay: float = 2.0) -> bool:
    """Remove a directory tree, with Windows-friendly fallback."""
    import shutil, time
    if not path.exists():
        return True
    for attempt in range(1, retries + 1):
        try:
            shutil.rmtree(path)
            return True
        except PermissionError:
            pass
        except OSError:
            pass
        # Fallback: cmd rd /s /q (more resilient on Windows)
        try:
            subprocess.run(
                ["cmd", "/c", "rd", "/s", "/q", str(path)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
        if not path.exists():
            return True
        if attempt < retries:
            print(f"      [retry {attempt}/{retries}] waiting {delay}s for lock release ...")
            time.sleep(delay)
    return not path.exists()


def run_pyinstaller() -> bool:
    print("[1/3] Running PyInstaller build ...")
    print(f"      spec: {SPEC}")

    # Pre-build cleanup (OneDrive/AV may hold handles on build/ and dist/StaTable/)
    for target_dir in (ROOT / "build", ROOT / "dist" / "StaTable"):
        print(f"      cleaning {target_dir} ...")
        if not _force_rmtree(target_dir):
            print(f"[FAIL] could not remove {target_dir}")
            print("       hint: pause OneDrive sync and retry, or use --skip-build")
            return False

    t0 = time.time()
    try:
        r = subprocess.run(
            ["pyinstaller", "--noconfirm", str(SPEC)],
            cwd=str(ROOT),
        )
    except FileNotFoundError:
        print("[FAIL] pyinstaller not found in PATH")
        return False
    except Exception as e:
        print(f"[FAIL] build error: {e!r}")
        return False
    elapsed = time.time() - t0
    if r.returncode != 0:
        print(f"[FAIL] PyInstaller exited with code {r.returncode}")
        return False
    print(f"[OK]   build complete in {elapsed:.1f}s")
    return True


def run_smoke(exe: Path, timeout: int) -> int:
    print(f"[2/3] Launching frozen EXE: {exe}")
    print(f"      timeout: {timeout}s")
    t0 = time.time()
    try:
        proc = subprocess.Popen(
            [str(exe), "--smoke-test"],
            cwd=str(exe.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as e:
        print(f"[FAIL] failed to launch: {e!r}")
        return EXIT_EXE_MISSING

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        print(f"[FAIL] timeout after {elapsed:.1f}s - killing process")
        proc.kill()
        try:
            proc.communicate(timeout=5)
        except Exception:
            pass
        return EXIT_TIMEOUT

    elapsed = time.time() - t0
    code = proc.returncode
    print(f"[3/3] exe exited with code {code} in {elapsed:.1f}s")
    if code != 0:
        if stderr:
            print("--- stderr ---")
            try:
                print(stderr.decode("utf-8", errors="replace"))
            except Exception:
                print(repr(stderr))
        return EXIT_NONZERO
    return EXIT_PASS


def main() -> int:
    ap = argparse.ArgumentParser(
        description="StaTable frozen EXE smoke test launcher")
    ap.add_argument("--skip-build", action="store_true",
                    help="use existing dist/StaTable/StaTable.exe")
    ap.add_argument("--timeout", type=int, default=60,
                    help="smoke test timeout in seconds (default 60)")
    ap.add_argument("--exe", type=Path, default=None,
                    help="override exe path")
    args = ap.parse_args()

    exe = args.exe.resolve() if args.exe else DEFAULT_EXE

    print("=" * 70)
    print("  StaTable frozen EXE smoke test")
    print("=" * 70)
    print(f"  code/:    {ROOT}")
    print(f"  exe:      {exe}")
    print(f"  timeout:  {args.timeout}s")
    print()

    if not args.skip_build:
        if not SPEC.exists():
            print(f"[FAIL] spec not found: {SPEC}")
            return EXIT_BUILD_FAILED
        if not run_pyinstaller():
            return EXIT_BUILD_FAILED
    else:
        print("[1/3] Skipping PyInstaller build (--skip-build)")

    if not exe.exists():
        print(f"[FAIL] exe not found: {exe}")
        return EXIT_EXE_MISSING

    result = run_smoke(exe, args.timeout)
    print()
    if result == EXIT_PASS:
        print("[PASS] frozen EXE smoke test")
    else:
        print(f"[FAIL] exit code = {result}")
    return result


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
        sys.exit(EXIT_UNEXPECTED)
    except Exception as e:
        print(f"[ERROR] unexpected: {e!r}")
        sys.exit(EXIT_UNEXPECTED)