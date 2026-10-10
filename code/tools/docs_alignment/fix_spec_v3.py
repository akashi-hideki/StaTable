"""Fix SPEC_STATE_ACTIONS EN/ZH formatting (v3 — targeted).

Fixes:
  1. Section 6.5: remove the artificial fence pair inserted between
     `        {` and the following `EVENT_Driver_t evt = ...` line.
  2. Section 9.1: remove orphan ``` right after `State.do` table row.
  3. Re-ensure blank line before headings.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent.parent / "docs"
HEADING_RE = re.compile(r"^#{1,6}\s")


def fix_65_split(text: str) -> tuple[str, int]:
    # Pattern: <indent>{ <blank> ``` <blank> <indent>CODE
    pat = re.compile(
        r"(?m)^(\s+\{\s*)\n\n```\n\n(\s+\S)",
    )
    text, n = pat.subn(r"\1\n\2", text)
    return text, n


def fix_91_orphan(text: str) -> tuple[str, int]:
    # Pattern: table row containing State.do, then blank(s), then ```
    pat = re.compile(
        r"(?m)^(\| `State\.do` [^\n]+)\n\n```\n\n+",
    )
    text, n = pat.subn(r"\1\n\n", text)
    return text, n


def ensure_heading_blank(text: str) -> tuple[str, int]:
    lines = text.split("\n")
    out: list[str] = []
    in_code = False
    n = 0
    for line in lines:
        if line.lstrip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        if not in_code and HEADING_RE.match(line):
            if out and out[-1].strip() != "":
                out.append("")
                n += 1
            out.append(line)
            continue
        out.append(line)
    return "\n".join(out), n


def collapse_blanks(text: str) -> str:
    return re.sub(r"\n{4,}", "\n\n\n", text)


def fix_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text, n1 = fix_65_split(text)
    text, n2 = fix_91_orphan(text)
    text, n3 = ensure_heading_blank(text)
    text = collapse_blanks(text)
    text = text.rstrip() + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] {path.name}: 6.5={n1}, 9.1={n2}, headings={n3}, "
          f"{path.stat().st_size} bytes, {len(text.splitlines())} lines")


def main() -> int:
    for name in ("SPEC_STATE_ACTIONS_v1_en.md", "SPEC_STATE_ACTIONS_v1_zh.md"):
        p = DOCS / name
        if p.exists():
            fix_file(p)
        else:
            print(f"[MISS] {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())