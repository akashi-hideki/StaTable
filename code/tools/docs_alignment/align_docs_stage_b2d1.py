"""v3.4.3 doc alignment — Stage B-2d1: extract §2.1-2.3 (file output)."""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "LAYER_DESIGN_zh.md")
OUT = Path(__file__).resolve().parent.parent.parent.parent / "b2d1_output.txt"


def extract(text: str, start: str, end: str, out_lines: list) -> None:
    s = text.find(start)
    e = text.find(end)
    if s == -1:
        out_lines.append(f"[ERR] start not found: {start!r}")
        return
    if e == -1:
        out_lines.append(f"[ERR] end not found: {end!r}")
        return
    if e <= s:
        out_lines.append(f"[ERR] start/end out of order")
        return
    section = text[s:e]
    lines = section.splitlines()
    out_lines.append("")
    out_lines.append("=" * 74)
    out_lines.append(f"  {start}  ({len(lines)} lines)")
    out_lines.append("=" * 74)
    for line in lines:
        out_lines.append(f"  {line}")


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")
    out_lines = []

    extract(text, "### 2.1 整体结构", "### 2.2 层一览", out_lines)
    extract(text, "### 2.2 层一览", "### 2.3 命名空间", out_lines)
    extract(text, "### 2.3 命名空间", "## 3. 设计理论", out_lines)

    OUT.write_text("\n".join(out_lines), encoding="utf-8", newline="\n")
    print(f"[OK] written to: {OUT}")
    print(f"     size: {OUT.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())