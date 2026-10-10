"""Stage B-3a: extract §3.7-§3.13 (remaining Driver roles) + §4 header."""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "ROLE_FUNCTIONS_zh.md")
OUT = (Path(__file__).resolve().parent.parent.parent
       / "b3a_output.txt")


def extract(text: str, start: str, end: str, out: list) -> None:
    s = text.find(start)
    e = text.find(end)
    if s == -1 or e == -1 or e <= s:
        out.append(f"[ERR] {start!r} / {end!r} (s={s}, e={e})")
        return
    section = text[s:e]
    out.append("")
    out.append("=" * 74)
    out.append(f"  {start}  ({len(section)} chars)")
    out.append("=" * 74)
    for line in section.splitlines():
        out.append(f"  {line}")


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")
    out: list = []

    # §3.7 - §4.1 (Driver roles output side + next chapter start)
    extract(text, "### 3.7 SetHeaterPwm", "## 4.", out)

    # Also find what comes after §3
    import re
    m = re.search(r"^## 4\. .*$", text, re.MULTILINE)
    if m:
        out.append("")
        out.append("=" * 74)
        out.append(f"  Next section (## 4.): {m.group(0)}")
        out.append(f"  at line {text[:m.start()].count(chr(10)) + 1}")
        out.append("=" * 74)

    OUT.write_text("\n".join(out), encoding="utf-8", newline="\n")
    print(f"[OK] written to: {OUT}")
    print(f"     size: {OUT.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())