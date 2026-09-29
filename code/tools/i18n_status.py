# code/tools/i18n_status.py
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
