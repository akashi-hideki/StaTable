#!/usr/bin/env python3
"""Fix issues from the first pass of update_spec_docs.py.

Issues addressed:
  1. SPEC_SCREENS: §5.4 was inserted INSIDE a ```python code fence.
     Move it OUTSIDE the fence (before the closing ```).
  2. Update the top-level title header from v2.3 to v2.4 in all 4 files.
  3. Ensure a blank line before the new "| 2.4 |" revision row.
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import sys
from pathlib import Path


FILES = [
    "docs/SPEC_OVERVIEW_ja.md",
    "docs/SPEC_OVERVIEW_en.md",
    "docs/SPEC_SCREENS_ja.md",
    "docs/SPEC_SCREENS_en.md",
]


# ----------------------------------------------------------------------
# Fix 1: SPEC_SCREENS - move §5.4 out of the code fence
# ----------------------------------------------------------------------
def fix_screens_section_5_4(text: str) -> tuple[str, str]:
    """If '### 5.4' appears between ```python and ```, move it after ```.

    Returns (new_text, message).
    """
    lines = text.splitlines(keepends=True)

    # Find the ```python ... ``` block that contains "### 5.4"
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("```python"):
            start = i
            break
    if start is None:
        return text, "no ```python block found"

    # Find the closing ```
    end = None
    for j in range(start + 1, len(lines)):
        if lines[j].strip() == "```":
            end = j
            break
    if end is None:
        return text, "no closing ``` found"

    block = lines[start:end + 1]
    block_text = "".join(block)

    # Search for "### 5.4" inside the block
    if "### 5.4" not in block_text:
        return text, "### 5.4 not in code block (no change needed)"

    # Find where §5.4 starts within the block
    m = re.search(r"\n(###\s*5\.4.*?)\n?(```\s*)$",
                  block_text, re.DOTALL)
    if not m:
        return text, "could not parse §5.4 inside block"

    section_text = m.group(1)
    # Remove §5.4 from inside the code block
    block_text_clean = block_text[:m.start()] + "\n```\n"
    # Rebuild: cleaned block + §5.4 after the closing fence
    new_block = block_text_clean.rstrip("\n") + "\n\n" + section_text + "\n"

    new_lines = lines[:start] + [new_block] + lines[end + 1:]
    return "".join(new_lines), "moved §5.4 outside code fence"


# ----------------------------------------------------------------------
# Fix 2: top-level title v2.3 -> v2.4
# ----------------------------------------------------------------------
# Compile patterns WITH re.MULTILINE (so ^ matches inside the code fence)
TITLE_PATTERNS = [
    (re.compile(r"^(#\s+StaTable Overall Specification\s+)v2\.3",
                re.MULTILINE),
     r"\g<1>v2.4"),
    (re.compile(r"^(#\s+StaTable 全体仕様書\s+)v2\.3",
                re.MULTILINE),
     r"\g<1>v2.4"),
    (re.compile(r"^(#\s+StaTable Screen Specification\s+)v2\.3",
                re.MULTILINE),
     r"\g<1>v2.4"),
    (re.compile(r"^(#\s+StaTable 画面仕様書\s+)v2\.3",
                re.MULTILINE),
     r"\g<1>v2.4"),
]


def fix_title(text: str) -> tuple[str, str]:
    for pat, repl in TITLE_PATTERNS:
        # NOTE: patterns already compiled with MULTILINE; no flags kwarg.
        new_text, n = pat.subn(repl, text, count=1)
        if n:
            return new_text, "title v2.3 -> v2.4"
    return text, "title pattern not found"


# ----------------------------------------------------------------------
# Fix 3: blank line before the new "| 2.4 |" revision row
# ----------------------------------------------------------------------
def fix_revision_blank_line(text: str) -> tuple[str, str]:
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.lstrip().startswith("| 2.4 |"):
            if i > 0 and lines[i - 1].strip() != "":
                lines.insert(i, "\n")
                return "".join(lines), "inserted blank line before | 2.4 |"
            return text, "blank line already present (no change needed)"
    return text, "no | 2.4 | row found"


# ----------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------
def process(path: Path, apply: bool, backup: bool) -> bool:
    print()
    print("=" * 78)
    print(f"  {path.name}")
    print("=" * 78)

    if not path.exists():
        print(f"  [SKIP] not found: {path}")
        return True

    original = path.read_text(encoding="utf-8")
    text = original
    messages = []

    # Fix 1 (only for SPEC_SCREENS)
    if "SPEC_SCREENS" in path.name:
        text, msg = fix_screens_section_5_4(text)
        messages.append(("§5.4 out of code fence", msg))

    # Fix 2: title
    text, msg = fix_title(text)
    messages.append(("title header", msg))

    # Fix 3: blank line
    text, msg = fix_revision_blank_line(text)
    messages.append(("revision blank line", msg))

    for label, msg in messages:
        print(f"  [INFO] {label}: {msg}")

    if text == original:
        print("  [INFO] no changes")
        return True

    print()
    print("  --- diff preview ---")
    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        text.splitlines(keepends=True),
        fromfile="before", tofile="after", n=1,
    ))
    for line in diff[:40]:
        sys.stdout.write("    " + line if line.endswith("\n")
                         else "    " + line + "\n")
    if len(diff) > 40:
        print(f"    ... ({len(diff) - 40} more lines)")

    if not apply:
        print()
        print("  [DRY-RUN] not written (use --apply)")
        return True

    if backup:
        bak = path.with_suffix(path.suffix + ".bak2")
        shutil.copy2(path, bak)
        print(f"  [BACKUP] {bak}")

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"  [WRITTEN] {path}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    ap.add_argument("--file", default=None)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    apply = args.apply
    backup = not args.no_backup

    print("=" * 78)
    print("  SPEC docs fix-up (post v2.4 apply)")
    print("=" * 78)
    print(f"  Root  : {root}")
    print(f"  Mode  : {'APPLY' if apply else 'DRY-RUN'}")

    for fname in FILES:
        if args.file and Path(fname).name != args.file:
            continue
        process(root / fname, apply, backup)

    print()
    print("=" * 78)
    print("  Done.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())