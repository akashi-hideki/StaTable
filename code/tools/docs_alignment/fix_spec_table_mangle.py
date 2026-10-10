"""Fix mangled SPEC_STATE_ACTIONS_v1_{en,zh}.md:
   1. Unescape &#x20; -> space
   2. Remove blank lines between table rows
   3. Remove blank lines between list items
   4. Remove blank lines between flow arrow sequences
   5. Remove blank lines inside code blocks
   6. Collapse consecutive blank lines
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent.parent / "docs"


def is_list_item(s: str) -> bool:
    return bool(re.match(r"^([-*+]\s|\d+\.\s)", s))


def is_flow_arrow(s: str) -> bool:
    return s.strip() in ("↓", "→", "↑", "←")


def ends_with_punct(s: str) -> bool:
    return bool(re.search(r"[.!?。！？:：]\s*$", s.rstrip()))


def fix_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    # Pass 1: unescape HTML entity for space
    text = text.replace("&#x20;", " ")

    lines = text.split("\n")
    out: list[str] = []
    in_code = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Code fence toggle
        if line.lstrip().startswith("```"):
            in_code = not in_code
            out.append(line)
            i += 1
            continue

        # Inside code: skip blanks
        if in_code:
            if line.strip() == "":
                i += 1
                continue
            out.append(line)
            i += 1
            continue

        # Blank line
        if line.strip() == "":
            # skip consecutive blanks
            if not out or out[-1].strip() == "":
                i += 1
                continue

            # find next non-blank
            nxt = None
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    nxt = lines[j]
                    break
            if nxt is None:
                i += 1
                continue

            prev = out[-1]
            ps = prev.lstrip()
            ns = nxt.lstrip()

            keep = True

            # code fence boundaries
            if ps.startswith("```") or ns.startswith("```"):
                keep = True
            # table row -> table row
            elif ps.startswith("|") and ns.startswith("|"):
                keep = False
            # list item -> list item
            elif is_list_item(ps) and is_list_item(ns):
                keep = False
            # flow arrow context
            elif is_flow_arrow(ps) or is_flow_arrow(ns):
                keep = False
            # paragraph continuation (prev has no sentence ending)
            elif (not ends_with_punct(prev)
                  and not re.match(r"^#{1,6}\s", ps)
                  and not re.match(r"^---+\s*$", ps)):
                keep = False

            if keep:
                out.append(line)
            i += 1
            continue

        out.append(line)
        i += 1

    result = "\n".join(out).rstrip() + "\n"
    path.write_text(result, encoding="utf-8", newline="\n")
    print(f"[OK] {path.name}: {path.stat().st_size} bytes, {len(result.splitlines())} lines")


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