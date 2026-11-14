# code/tools/patches/patch_v3_1_i18n_fix_nojapanese.py
r"""
v3.1 fix: remove Japanese comments from i18n/__init__.py.

CI's find_all_japanese.py rejects any line with Japanese chars.
The LANG_DISPLAY dict uses \uXXXX escapes for display names, but
the inline comments contained actual Japanese/Chinese characters.

This patch removes those comments (display strings unchanged).

Usage:
    cd code
    python tools\patches\patch_v3_1_i18n_fix_nojapanese.py
    python tools\patches\patch_v3_1_i18n_fix_nojapanese.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "statable_gui" / "i18n" / "__init__.py"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_i18n_fix_nojapanese  [{mode}]")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] not found: {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8")

    # Find line-by-line and strip trailing JP comments
    changed = False
    lines = text.splitlines(keepends=True)
    out_lines = []
    for i, line in enumerate(lines, 1):
        stripped = line.rstrip("\r\n")
        eol = line[len(stripped):]
        # Remove trailing "# ..." if it contains non-ASCII
        if "#" in stripped:
            head, _, tail = stripped.partition("#")
            if any(ord(c) > 127 for c in tail):
                new_line = head.rstrip() + eol
                print(f"[APPLY] L{i}: {stripped[:60]!r} -> {new_line.rstrip()[:60]!r}")
                out_lines.append(new_line)
                changed = True
                continue
        out_lines.append(line)

    if not changed:
        print("[SKIP] no JP/CN comments found")
        return 0

    new_text = "".join(out_lines)

    # Safety: verify it still parses
    import ast
    try:
        ast.parse(new_text)
    except SyntaxError as e:
        print(f"[FAIL] patch would break syntax: {e}")
        return 1

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply")
        return 0

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_nojp")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    TARGET.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {TARGET.name} updated ({len(text)} -> {len(new_text)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())