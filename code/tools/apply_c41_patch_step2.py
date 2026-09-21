#!/usr/bin/env python3
"""Apply C-41 derived patches to glossary / SDK API / CODEGEN docs.

Purpose:
    Reflect the C-41 design principle (role functions are layer-agnostic)
    in derived documentation, after the main SPEC_OVERVIEW update.

Insertions (4 total):
    1. glossary.md          : add "calling layer" / "layer-agnostic"
    2. SPEC_SDK_API_ja.md   : add C-41 note row in terminology table
    3. SPEC_SDK_API_en.md   : add C-41 note row (English)
    4. SPEC_CODEGEN_v3.md   : add layer-agnostic note in scope list

Safety:
    - Dry-run by default (--apply to execute)
    - Idempotent: skips if the target text already exists
    - Creates .bak backups
    - Shows unified diff (--show-diff)
    - Verifies insertion counts

Usage:
    cd C:/Users/user/OneDrive/ドキュメント/GitHub/StaTable/code
    python tools/apply_c41_patch_step2.py              # dry-run
    python tools/apply_c41_patch_step2.py --apply
    python tools/apply_c41_patch_step2.py --apply --show-diff
"""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = REPO_ROOT / "code" / "docs"


# ----------------------------------------------------------------------
# Patch definitions
# ----------------------------------------------------------------------
PATCHES = [
    {
        "file": "glossary.md",
        "anchor": re.compile(r"^\|\s*名前空間\s*\|"),
        "insert_text": (
            "| 呼び出し元層 | calling layer |\n"
            "| 層非依存 | layer-agnostic |"
        ),
        "skip_if_contains": re.compile(r"calling layer"),
        "description": "glossary: add calling layer / layer-agnostic",
    },
    {
        "file": "SPEC_SDK_API_ja.md",
        "anchor": re.compile(
            r"^\|\s*ロール関数\s*\|\s*遷移・条件・ISR から呼ばれる C 関数\s*\|"
        ),
        "insert_text": (
            "| ロール関数（設計原則） | 呼び出し元層に依存しない（layer-agnostic）。"
            "層別動作は関数分割で対応（SPEC_OVERVIEW §3.2.7 参照） |"
        ),
        "skip_if_contains": re.compile(r"ロール関数（設計原則）"),
        "description": "SPEC_SDK_API_ja: add C-41 note",
    },
    {
        "file": "SPEC_SDK_API_en.md",
        "anchor": re.compile(
            r"^\|\s*Role function\s*\|\s*A C function called from transitions, conditions, or ISRs\s*\|"
        ),
        "insert_text": (
            "| Role function (design principle) | "
            "Layer-agnostic: does not depend on the calling layer. "
            "For layer-specific behavior, split into separate functions "
            "(see SPEC_OVERVIEW §3.2.7) |"
        ),
        "skip_if_contains": re.compile(r"Role function \(design principle\)"),
        "description": "SPEC_SDK_API_en: add C-41 note",
    },
    {
        "file": "SPEC_CODEGEN_v3.md",
        "anchor": re.compile(r"^- ISR-callable role functions \(Stage 3\)\s*$"),
        "insert_text": (
            "- Layer-agnostic role functions: do not depend on the calling layer "
            "(see SPEC_OVERVIEW §3.2.7)"
        ),
        "skip_if_contains": re.compile(r"Layer-agnostic role functions"),
        "description": "SPEC_CODEGEN_v3: add C-41 note",
    },
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def read_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.split("\n")


def write_lines(path: Path, lines: list[str]) -> None:
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8", newline="\n")


def find_anchor_index(lines: list[str], pattern: re.Pattern) -> int | None:
    for i, line in enumerate(lines):
        if pattern.search(line):
            return i
    return None


# ----------------------------------------------------------------------
# Apply
# ----------------------------------------------------------------------
def apply_patch(patch: dict, apply: bool, backup: bool) -> dict:
    path = DOCS / patch["file"]
    result = {
        "description": patch["description"],
        "file": patch["file"],
        "status": "unknown",
        "detail": "",
        "anchor_line": None,
    }

    if not path.exists():
        result["status"] = "MISSING"
        result["detail"] = f"file not found: {path}"
        return result

    original_text = path.read_text(encoding="utf-8")
    lines = read_lines(path)

    if patch["skip_if_contains"].search(original_text):
        result["status"] = "ALREADY_APPLIED"
        result["detail"] = "target text already present"
        return result

    anchor_idx = find_anchor_index(lines, patch["anchor"])
    if anchor_idx is None:
        result["status"] = "ANCHOR_NOT_FOUND"
        result["detail"] = (
            f"anchor pattern not found: {patch['anchor'].pattern}"
        )
        return result

    result["anchor_line"] = anchor_idx + 1

    # Insert the new lines immediately after the anchor line.
    insert_lines = patch["insert_text"].split("\n")
    new_lines = (
        lines[: anchor_idx + 1]
        + insert_lines
        + lines[anchor_idx + 1 :]
    )

    result["status"] = "WOULD_APPLY" if not apply else "APPLIED"
    result["detail"] = f"anchor at line {anchor_idx + 1}"

    if apply:
        if backup:
            bak = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, bak)
        write_lines(path, new_lines)

    return result


# ----------------------------------------------------------------------
# Diff display
# ----------------------------------------------------------------------
def show_diff(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        print(f"  (no backup for diff: {bak})")
        return

    old = bak.read_text(encoding="utf-8").splitlines(keepends=True)
    new = path.read_text(encoding="utf-8").splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        old, new,
        fromfile=f"a/{path.name}",
        tofile=f"b/{path.name}",
        lineterm="",
        n=2,
    ))
    if not diff:
        print("  (no diff)")
        return
    for line in diff:
        print(f"  {line.rstrip()}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def parse_args(argv):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--apply", action="store_true",
                    help="Execute the patch (default is dry-run).")
    ap.add_argument("--no-backup", action="store_true",
                    help="Skip creating .bak files.")
    ap.add_argument("--show-diff", action="store_true",
                    help="Show unified diff after applying (uses .bak).")
    return ap.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    apply = args.apply
    backup = not args.no_backup

    print("=" * 70)
    print(f"  C-41 derived doc patch  root={REPO_ROOT}")
    print(f"  mode   = {'APPLY' if apply else 'DRY-RUN'}")
    print(f"  backup = {backup}")
    print("=" * 70)

    results = [apply_patch(p, apply=apply, backup=backup) for p in PATCHES]

    print("\n--- Results ---")
    for r in results:
        print(f"  {r['status']:<18} {r['file']:<25} {r['detail']}")

    applied = sum(1 for r in results if r["status"] in ("APPLIED", "WOULD_APPLY"))
    skipped = sum(1 for r in results if r["status"] == "ALREADY_APPLIED")
    errors = [r for r in results if r["status"] in ("MISSING", "ANCHOR_NOT_FOUND")]

    print(f"\n  Applied: {applied}  Skipped: {skipped}  Errors: {len(errors)}")

    if errors:
        print("\n  ERROR: some patches failed. See above.")
        return 1

    if not apply:
        print("\n" + "=" * 70)
        print("  DRY-RUN complete. Re-run with --apply to execute.")
        print("=" * 70)
        return 0

    # Show diff (if requested)
    if args.show_diff:
        print("\n--- Unified diff (from .bak) ---")
        for fname in sorted({r["file"] for r in results}):
            path = DOCS / fname
            print(f"\n### {fname}")
            show_diff(path)

    # Verification
    print("\n--- Verification ---")
    for fname in sorted({r["file"] for r in results}):
        path = DOCS / fname
        text = path.read_text(encoding="utf-8")
        if fname == "glossary.md":
            count = len(re.findall(r"calling layer|layer-agnostic", text))
        elif fname == "SPEC_SDK_API_ja.md":
            count = len(re.findall(r"ロール関数（設計原則）", text))
        elif fname == "SPEC_SDK_API_en.md":
            count = len(re.findall(r"Role function \(design principle\)", text))
        elif fname == "SPEC_CODEGEN_v3.md":
            count = len(re.findall(r"Layer-agnostic role functions", text))
        else:
            count = -1
        print(f"  {fname}: {count} insertion(s) detected (expected >= 1)")

    print("\n" + "=" * 70)
    print("  DONE. Recommended for manual review:")
    print("    git diff code/docs/glossary.md")
    print("    git diff code/docs/SPEC_SDK_API_ja.md")
    print("    git diff code/docs/SPEC_SDK_API_en.md")
    print("    git diff code/docs/SPEC_CODEGEN_v3.md")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))