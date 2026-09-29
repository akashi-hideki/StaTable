# code/tools/patches/patch_v3_1_i18n_tools.py
r"""
Phase v3.1 i18n: create i18n tool scripts.

New files:
  - code/tools/i18n_extract.py  (lupdate wrapper)
  - code/tools/i18n_compile.py  (lrelease wrapper)
  - code/tools/i18n_status.py   (translation progress)

Safety: idempotent.

Usage:
    cd code
    python tools\patches\patch_v3_1_i18n_tools.py
    python tools\patches\patch_v3_1_i18n_tools.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent

EXTRACT_PY = '''# code/tools/i18n_extract.py
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
'''

COMPILE_PY = '''# code/tools/i18n_compile.py
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
'''

STATUS_PY = '''# code/tools/i18n_status.py
"""Show translation progress by parsing .ts files.

Usage:
    cd code
    python tools/i18n_status.py
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent
I18N = CODE / "statable_gui" / "i18n"


def scan_ts(ts: Path) -> dict:
    tree = ET.parse(ts)
    root = tree.getroot()
    total = 0
    done = 0
    unfinished = 0
    vanished = 0
    for ctx in root.findall("context"):
        for msg in ctx.findall("message"):
            total += 1
            tr = msg.find("translation")
            if tr is None:
                unfinished += 1
                continue
            ttype = tr.get("type", "")
            text = (tr.text or "").strip()
            if ttype == "unfinished" or not text:
                unfinished += 1
            elif ttype == "vanished":
                vanished += 1
            else:
                done += 1
    return {
        "file": ts.name,
        "total": total,
        "done": done,
        "unfinished": unfinished,
        "vanished": vanished,
    }


def bar(done: int, total: int, width: int = 30) -> str:
    if total == 0:
        return "[" + " " * width + "]   0.0%"
    pct = done / total
    filled = int(width * pct)
    return "[" + "#" * filled + "." * (width - filled) + f"]  {pct*100:5.1f}%"


def main() -> int:
    ts_files = sorted(I18N.glob("statable_*.ts"))
    print("=" * 70)
    print("  StaTable i18n status")
    print("=" * 70)

    if not ts_files:
        print()
        print("No .ts files found.")
        print("Run: python tools/i18n_extract.py")
        return 0

    for ts in ts_files:
        try:
            s = scan_ts(ts)
        except Exception as e:
            print(f"  {ts.name}: ERROR {e!r}")
            continue
        print()
        print(f"  {s['file']}")
        print(f"    {bar(s['done'], s['total'])}")
        print(f"    done={s['done']}  unfinished={s['unfinished']}"
              f"  vanished={s['vanished']}  total={s['total']}")

    print()
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

TOOLS = [
    (CODE / "tools" / "i18n_extract.py", EXTRACT_PY),
    (CODE / "tools" / "i18n_compile.py", COMPILE_PY),
    (CODE / "tools" / "i18n_status.py", STATUS_PY),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_i18n_tools  [{mode}]")
    print("=" * 70)

    for path, content in TOOLS:
        rel = path.relative_to(CODE.parent)
        if path.exists():
            print(f"[SKIP] {rel} already exists")
            continue
        print(f"[APPLY] create {rel} ({len(content)} chars)")
        if not args.apply:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"[DONE] {rel}")

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
    return 0


if __name__ == "__main__":
    sys.exit(main())