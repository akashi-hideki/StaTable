# code/tools/i18n_compile.py
"""Compile .ts files into .qm binaries using lrelease.

Usage:
    cd code
    python tools/i18n_compile.py           # all .ts in i18n/
    python tools/i18n_compile.py zh_CN
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent
I18N = CODE / "statable_gui" / "i18n"


def find_lrelease() -> str | None:
    import PySide6
    base = Path(PySide6.__file__).parent
    for name in ("lrelease.exe", "lrelease"):
        p = base / name
        if p.exists():
            return str(p)
    return None


def find_ts_files(argv: list[str]) -> list[Path]:
    all_ts = sorted(I18N.glob("statable_*.ts"))
    if not argv:
        return all_ts
    wanted = {f"statable_{a}.ts" for a in argv}
    return [p for p in all_ts if p.name in wanted]


def run_lrelease(ts: Path, lrelease: str) -> int:
    qm = ts.with_suffix(".qm")
    cmd = [lrelease, str(ts), "-qm", str(qm)]
    print(f"[lrelease] {ts.name} -> {qm.name}")
    r = subprocess.run(cmd)
    return r.returncode


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    lrelease = find_lrelease()
    if lrelease is None:
        print("[FAIL] lrelease not found (expected in PySide6 dir)")
        return 1

    ts_files = find_ts_files(argv)
    if not ts_files:
        print("[FAIL] no .ts files found. Run i18n_extract.py first.")
        return 1

    rc = 0
    for ts in ts_files:
        rc |= run_lrelease(ts, lrelease)

    if rc == 0:
        print()
        print(f"[DONE] compiled {len(ts_files)} translation(s)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
