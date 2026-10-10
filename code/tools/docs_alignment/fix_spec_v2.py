"""Fix SPEC_STATE_ACTIONS EN/ZH formatting issues (v2).

Root cause:
  1. Section 6.5: chunk boundary inserted an extra ``` closing
     fence in the middle of a C code block.
  2. Section 9.1: an orphan ``` after the `State.do` table row
     put the rest of the document (9.2 ~ 14) into code-block state.

Fix:
  A. Merge split code block at section 6.5.
  B. Remove the orphan ``` at section 9.1.
  C. Re-run blank-line normalization around headings / hr / tables.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent.parent / "docs"

HEADING_RE = re.compile(r"^#{1,6}\s")
HR_RE = re.compile(r"^-{3,}\s*$")
LIST_RE = re.compile(r"^([-*+]\s|\d+\.\s)")


def is_table_row(s: str) -> bool:
    return s.lstrip().startswith("|")


def is_code_fence(s: str) -> bool:
    return s.lstrip().startswith("```")


def fix_split_code_block_65(text: str) -> str:
    """Merge: `<indent>{` / blank / ``` / blank / `EVENT_Driver_t ...`."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # detect: current line ends with `{`, followed by blank + ``` + blank
        # then code (not a fence)
        if (line.rstrip().endswith("{")
                and not is_code_fence(line)
                and i + 4 < len(lines)
                and lines[i + 1].strip() == ""
                and lines[i + 2].strip() == "```"
                and lines[i + 3].strip() == ""
                and not is_code_fence(lines[i + 4])):
            # drop: blank, ```, blank
            out.append(line)
            i += 4
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def fix_orphan_fence_91(text: str) -> str:
    """Remove orphan ``` right after the `State.do` table row in 9.1."""
    lines = text.split("\n")
    out: list[str] = []
    for i, line in enumerate(lines):
        if (line.strip() == "```"
                and out
                and out[-1].lstrip().startswith("|")
                and "State.do" in out[-1]):
            # skip this fence
            continue
        out.append(line)
    return "\n".join(out)


def normalize_blank_lines(text: str) -> str:
    """Single pass:
       - ensure blank before headings, hr, code fences
       - ensure blank after tables / code fences / hr
       - remove blank between table rows / list items
    """
    lines = text.split("\n")
    out: list[str] = []
    in_code = False

    for i, line in enumerate(lines):
        ls = line.lstrip()

        # Code fence
        if is_code_fence(line):
            in_code = not in_code
            if in_code:
                if out and out[-1].strip() != "":
                    out.append("")
                out.append(line)
                continue
            else:
                out.append(line)
                # blank after closing fence (unless next is fence / blank / hr)
                nxt = ""
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        nxt = lines[j]
                        break
                if nxt and not is_code_fence(nxt) and not HR_RE.match(nxt.lstrip()):
                    out.append("")
                continue

        if in_code:
            out.append(line)
            continue

        # Blank line: decide by context
        if line.strip() == "":
            if not out:
                continue
            prev = out[-1]
            nxt = ""
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    nxt = lines[j]
                    break
            if (is_table_row(prev) and is_table_row(nxt)):
                continue  # keep table compact
            if (LIST_RE.match(prev.lstrip()) and LIST_RE.match(nxt.lstrip())):
                continue
            if out[-1].strip() == "":
                continue
            out.append("")
            continue

        # Heading: blank before
        if HEADING_RE.match(ls):
            if out and out[-1].strip() != "":
                out.append("")
            out.append(line)
            continue

        # HR: blank before + after
        if HR_RE.match(line):
            if out and out[-1].strip() != "":
                out.append("")
            out.append(line)
            nxt = ""
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    nxt = lines[j]
                    break
            if nxt and nxt.strip() != "":
                out.append("")
            continue

        # Non-blank regular line: if previous was a table row and this is not,
        # insert blank before this line
        if out and is_table_row(out[-1]) and not is_table_row(line):
            out.append("")

        out.append(line)

    return "\n".join(out)


def fix_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = fix_split_code_block_65(text)
    text = fix_orphan_fence_91(text)
    text = normalize_blank_lines(text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)  # max 2 blank lines
    text = text.rstrip() + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] {path.name}: {path.stat().st_size} bytes, "
          f"{len(text.splitlines())} lines")


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