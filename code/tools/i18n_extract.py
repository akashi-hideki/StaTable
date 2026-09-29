# code/tools/i18n_extract.py
"""Extract translatable strings from GUI source into .ts files.

Wraps lupdate (shipped with PySide6).

Usage:
    cd code
    python tools/i18n_extract.py           # all languages
    python tools/i18n_extract.py ja        # only ja
    python tools/i18n_extract.py zh_CN
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent
GUI = CODE / "statable_gui"
I18N = GUI / "i18n"

LANGS = ["ja", "zh_CN"]


def find_lupdate() -> str | None:
    import PySide6
    base = Path(PySide6.__file__).parent
    for name in ("lupdate.exe", "lupdate"):
        p = base / name
        if p.exists():
            return str(p)
    return None


def gui_sources() -> list[Path]:
    return sorted(GUI.rglob("*.py"))


def run_lupdate(lang: str, lupdate: str) -> int:
    ts = I18N / f"statable_{lang}.ts"
    srcs = [str(p.relative_to(CODE)) for p in gui_sources()]
    cmd = [lupdate, "-no-obsolete", "-locations", "relative",
           *srcs, "-ts", str(ts.relative_to(CODE))]
    print(f"[lupdate] {lang}: -> {ts.name}")
    print(f"  cmd: {' '.join(cmd[:5])} ... ({len(srcs)} sources)")
    r = subprocess.run(cmd, cwd=str(CODE))
    return r.returncode


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    lupdate = find_lupdate()
    if lupdate is None:
        print("[FAIL] lupdate not found (expected in PySide6 dir)")
        return 1

    I18N.mkdir(parents=True, exist_ok=True)
    langs = argv if argv else LANGS

    rc = 0
    for lang in langs:
        rc |= run_lupdate(lang, lupdate)

    if rc == 0:
        print()
        print("[DONE] .ts files updated. Next: translate and run")
        print("       python tools/i18n_compile.py")
    return rc


if __name__ == "__main__":
    sys.exit(main())
