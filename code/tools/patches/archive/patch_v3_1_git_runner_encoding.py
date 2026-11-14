# code/tools/patches/patch_v3_1_git_runner_encoding.py
r"""
v3.1 fix: git_runner.py UnicodeDecodeError on Windows (cp932).

Problem:
    subprocess.run(..., text=True) uses locale default encoding
    (cp932 on Japanese Windows). git output containing UTF-8
    characters (em dash, Chinese) triggers UnicodeDecodeError.

Fix:
    Add encoding="utf-8", errors="replace" to all subprocess.run
    calls that decode text.

Usage:
    cd code
    python tools\patches\patch_v3_1_git_runner_encoding.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "tools" / "git_runner.py"

# All variants of the kwargs block that need fixing
REPLACEMENTS = [
    # (old, new)
    (
        '        cwd=str(REPO),\n'
        '        capture_output=True,\n'
        '        text=True,\n'
        '    )\n'
        '    return bool(r.stdout.strip())',
        '        cwd=str(REPO),\n'
        '        capture_output=True,\n'
        '        text=True,\n'
        '        encoding="utf-8",\n'
        '        errors="replace",\n'
        '    )\n'
        '    return bool(r.stdout.strip())',
    ),
    (
        '        cwd=str(REPO),\n'
        '        capture_output=True,\n'
        '        text=True,\n'
        '    )\n'
        '    # exit 0 = no diff; exit 1 = has diff\n'
        '    return r.returncode == 1',
        '        cwd=str(REPO),\n'
        '        capture_output=True,\n'
        '        text=True,\n'
        '        encoding="utf-8",\n'
        '        errors="replace",\n'
        '    )\n'
        '    # exit 0 = no diff; exit 1 = has diff\n'
        '    return r.returncode == 1',
    ),
]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_git_runner_encoding  [{mode}]")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] not found: {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8")
    if 'encoding="utf-8"' in text:
        print("[SKIP] already has encoding fix")
        return 0

    patched = text
    applied = 0
    for i, (old, new) in enumerate(REPLACEMENTS, 1):
        n = patched.count(old)
        if n == 0:
            print(f"[WARN] R{i}: anchor not found (may already be fixed)")
            continue
        if n > 1:
            print(f"[FAIL] R{i}: anchor found {n} times")
            return 1
        patched = patched.replace(old, new, 1)
        print(f"[APPLY] R{i}")
        applied += 1

    if applied == 0:
        print("[SKIP] no changes needed")
        return 0

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply")
        return 0

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_enc")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    TARGET.write_text(patched, encoding="utf-8")
    print(f"[DONE] {TARGET.relative_to(CODE.parent)} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())