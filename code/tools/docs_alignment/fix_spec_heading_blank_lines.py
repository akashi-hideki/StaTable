"""Ensure blank line before every markdown heading (# ~ ######).

Does NOT touch inside code blocks.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent.parent / "docs"

HEADING_RE = re.compile(r"^#{1,6}\s")


def fix_headings(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    out: list[str] = []
    in_code = False

    for i, line in enumerate(lines):
        # Code fence toggle
        if line.lstrip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue

        if in_code:
            out.append(line)
            continue

        # Heading: ensure blank line before
        if HEADING_RE.match(line):
            if out and out[-1].strip() != "":
                out.append("")
            out.append(line)
            continue

        out.append(line)

    # Collapse 3+ consecutive blanks to 2
    result: list[str] = []
    for ln in out:
        if ln.strip() == "" and result and result[-1].strip() == "":
            continue
        result.append(ln)

    text_out = "\n".join(result).rstrip() + "\n"
    path.write_text(text_out, encoding="utf-8", newline="\n")
    print(f"[OK] {path.name}: {path.stat().st_size} bytes, {len(text_out.splitlines())} lines")


def main() -> int:
    for name in ("SPEC_STATE_ACTIONS_v1_en.md", "SPEC_STATE_ACTIONS_v1_zh.md"):
        p = DOCS / name
        if p.exists():
            fix_headings(p)
        else:
            print(f"[MISS] {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())