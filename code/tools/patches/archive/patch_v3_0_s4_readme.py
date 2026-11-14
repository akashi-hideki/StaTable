# code/tools/patches/patch_v3_0_s4_readme.py
r"""
Phase S-4 patch (E): update README v3.0 section.

Targets:
  - README.md (repo root)

Edits:
  E1. v3.0 header: "Planned" -> "In Progress"
  E2. Python SDK: sandglass -> check, "pip installable" -> "pip install statable"
  E3. Headless CLI: sandglass -> check, CLI actual syntax

Safety:
  - Idempotent
  - Unicode escape sequences for emoji (avoids encoding issues)

Usage:
    cd code
    python tools\patches\patch_v3_0_s4_readme.py
    python tools\patches\patch_v3_0_s4_readme.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
README = REPO / "README.md"

# Unicode escape sequences (encoding-safe)
SANDGLASS = "\u23f3"   # hourglass
CHECK = "\u2705"       # check mark
EMDASH = "\u2014"      # em dash
GRAVE = "`"

REPLACEMENTS = [
    (
        "### v3.0 (Planned " + EMDASH + " SDK Foundation)",
        "### v3.0 (In Progress " + EMDASH + " SDK Foundation)",
    ),
    (
        "- " + SANDGLASS + " **Python SDK** (pip installable)",
        "- " + CHECK + " **Python SDK** (pip install statable)",
    ),
    (
        "- " + SANDGLASS + " **Headless CLI** ("
        + GRAVE + "statable build project.xml" + GRAVE + ")",
        "- " + CHECK + " **CLI** ("
        + GRAVE + "statable-cli generate --xml ..." + GRAVE + ")",
    ),
]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_0_s4_readme  [{mode}]")
    print("=" * 70)

    if not README.exists():
        print(f"[FAIL] not found: {README}")
        return 1

    text = README.read_text(encoding="utf-8")
    patched = text
    rc = 0

    for i, (old, new) in enumerate(REPLACEMENTS, start=1):
        n = patched.count(old)
        if n == 0:
            if new in patched:
                print(f"[SKIP] E{i}: already updated")
                continue
            print(f"[FAIL] E{i}: anchor not found")
            print(f"        old = {old!r}")
            rc = 1
            continue
        if n > 1:
            print(f"[FAIL] E{i}: anchor found {n} times")
            rc = 1
            continue
        print(f"[APPLY] E{i}")
        patched = patched.replace(old, new, 1)

    if rc != 0:
        print()
        print("[ABORT] one or more anchors failed; no file written.")
        return 1

    if patched == text:
        print()
        print("[SKIP] README.md already up to date")
        return 0

    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    bak = README.with_suffix(README.suffix + ".bak_s4")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    README.write_text(patched, encoding="utf-8")
    print(f"[DONE] README.md updated ({len(text)} -> {len(patched)} chars)")
    print()
    print("Verify:")
    print("  Select-String -Path ..\\README.md -Pattern 'v3.0|Python SDK|CLI'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
