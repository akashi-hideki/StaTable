"""Stage B-2h1: extract §4.3 MwMicrowave and §4.6 MwSteam."""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "LAYER_DESIGN_zh.md")
# Output to StaTable root (3 parents up)
OUT = (Path(__file__).resolve().parent.parent.parent
       / "b2h1_output.txt")


def extract(text: str, start: str, end: str, out: list) -> None:
    s = text.find(start)
    e = text.find(end)
    if s == -1 or e == -1 or e <= s:
        out.append(f"[ERR] {start!r} / {end!r} (s={s}, e={e})")
        return
    section = text[s:e]
    out.append("")
    out.append("=" * 74)
    out.append(f"  {start}")
    out.append("=" * 74)
    for line in section.splitlines():
        out.append(f"  {line}")


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")
    out: list = []

    extract(text, "### 4.3 MwMicrowave 层", "### 4.4 MwOven 层", out)
    extract(text, "### 4.6 MwSteam 层", "### 4.7 Application 层", out)

    OUT.write_text("\n".join(out), encoding="utf-8", newline="\n")
    print(f"[OK] written to: {OUT}")
    print(f"     size: {OUT.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())