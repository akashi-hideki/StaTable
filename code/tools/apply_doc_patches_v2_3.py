#!/usr/bin/env python3
"""Apply v2.3 documentation patches (C-40, §11.5) automatically.

Targets:
    docs/SPEC_OVERVIEW_ja.md
    docs/SPEC_OVERVIEW_en.md

Patches:
    1. §12 Known Constraints: insert C-40 row right after C-39 row.
    2. §11.5 Verification Tools: insert tools/rename_ja_suffix.py line
       right after verify_new_project_code_facts.py line.

Safety:
    - Dry-run by default. Only executes when --apply is passed.
    - Creates a .bak backup for each file before writing.
    - Idempotent: refuses to re-insert if the target text already exists.
    - UTF-8 with LF line endings (POSIX).

Usage:
    cd C:/Users/user/OneDrive/ドキュメント/GitHub/StaTable/code
    python tools/apply_doc_patches_v2_3.py             # dry-run
    python tools/apply_doc_patches_v2_3.py --apply     # execute
    python tools/apply_doc_patches_v2_3.py --apply --no-backup
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent  # .../StaTable
DOCS = REPO_ROOT / "docs"

# --- Patches per file -------------------------------------------------
# Each patch: {
#   "file": relative path from REPO_ROOT,
#   "anchor": regex (one line) that identifies the insertion point,
#   "insert_after": list of lines to insert immediately after anchor,
#   "skip_if_contains": regex to detect the patch was already applied,
#   "description": human-readable description
# }

C40_JA = (
    "| C-40 | `StaTableLogger` シングルトンと TraceBall のコールバック保持 "
    "| **v2.3 で緩和**（`_TraceBallHandler.emit` で `RuntimeError` を catch） "
    "| 複数 `MainWindow` を生成するテスト環境での安全性確保 |"
)

C40_EN = (
    "| C-40 | `StaTableLogger` singleton and TraceBall callback retention "
    "| **Mitigated in v2.3** (`_TraceBallHandler.emit` catches `RuntimeError`) "
    "| Safety for test environments creating multiple `MainWindow` instances |"
)

TOOLS_JA = (
    "- `tools/rename_ja_suffix.py`（v2.3）："
    "`*_jp.*` → `*_ja.*` 一括リネーム（参照更新付き）"
)

TOOLS_EN = (
    "- `tools/rename_ja_suffix.py` (v2.3): "
    "batch rename `*_jp.*` -> `*_ja.*` with reference updates"
)

PATCHES = [
    # --- ja: C-40 ---
    {
        "file": "docs/SPEC_OVERVIEW_ja.md",
        "anchor": re.compile(r"^\|\s*C-39\s*\|"),
        "insert_after": [C40_JA],
        "skip_if_contains": re.compile(r"^\|\s*C-40\s*\|", re.MULTILINE),
        "description": "SPEC_OVERVIEW_ja §12: add C-40",
    },
    # --- ja: §11.5 ---
    {
        "file": "docs/SPEC_OVERVIEW_ja.md",
        "anchor": re.compile(r"verify_new_project_code_facts\.py"),
        "insert_after": [TOOLS_JA],
        "skip_if_contains": re.compile(r"rename_ja_suffix\.py"),
        "description": "SPEC_OVERVIEW_ja §11.5: add rename_ja_suffix.py",
    },
    # --- en: C-40 ---
    {
        "file": "docs/SPEC_OVERVIEW_en.md",
        "anchor": re.compile(r"^\|\s*C-39\s*\|"),
        "insert_after": [C40_EN],
        "skip_if_contains": re.compile(r"^\|\s*C-40\s*\|", re.MULTILINE),
        "description": "SPEC_OVERVIEW_en §12: add C-40",
    },
    # --- en: §11.5 ---
    {
        "file": "docs/SPEC_OVERVIEW_en.md",
        "anchor": re.compile(r"verify_new_project_code_facts\.py"),
        "insert_after": [TOOLS_EN],
        "skip_if_contains": re.compile(r"rename_ja_suffix\.py"),
        "description": "SPEC_OVERVIEW_en §11.5: add rename_ja_suffix.py",
    },
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def read_lines(path: Path) -> list[str]:
    """Read file as a list of lines (no newline chars)."""
    text = path.read_text(encoding="utf-8")
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.split("\n")


def write_lines(path: Path, lines: list[str]) -> None:
    """Write list of lines as UTF-8 with LF endings."""
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8", newline="\n")


def find_anchor_line(lines: list[str], pattern: re.Pattern) -> int | None:
    """Return the 0-based line index of the first match, or None."""
    for i, line in enumerate(lines):
        if pattern.search(line):
            return i
    return None


def apply_patch(patch: dict, apply: bool, backup: bool) -> dict:
    """Apply one patch. Return a result dict with status info."""
    file_rel = patch["file"]
    path = REPO_ROOT / file_rel
    result = {
        "description": patch["description"],
        "file": file_rel,
        "status": "unknown",
        "detail": "",
    }

    if not path.exists():
        result["status"] = "MISSING"
        result["detail"] = f"file not found: {path}"
        return result

    text = path.read_text(encoding="utf-8")
    lines = read_lines(path)

    # Idempotency check
    if patch["skip_if_contains"].search(text):
        result["status"] = "ALREADY_APPLIED"
        result["detail"] = "target text already present"
        return result

    anchor_idx = find_anchor_line(lines, patch["anchor"])
    if anchor_idx is None:
        result["status"] = "ANCHOR_NOT_FOUND"
        result["detail"] = f"anchor pattern not found: {patch['anchor'].pattern}"
        return result

    # Compute new content
    new_lines = (
        lines[: anchor_idx + 1]
        + patch["insert_after"]
        + lines[anchor_idx + 1 :]
    )

    result["status"] = "WOULD_APPLY" if not apply else "APPLIED"
    result["detail"] = (
        f"inserted {len(patch['insert_after'])} line(s) "
        f"after line {anchor_idx + 1}"
    )

    if apply:
        if backup:
            bak = path.with_suffix(path.suffix + ".bak")
            bak.write_text(text, encoding="utf-8")
        write_lines(path, new_lines)

    return result


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="Execute the plan (default is dry-run).")
    ap.add_argument("--no-backup", action="store_true",
                    help="Skip creating .bak files.")
    return ap.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    apply = args.apply
    backup = not args.no_backup

    print("=" * 70)
    print(f"  Apply v2.3 doc patches  root={REPO_ROOT}")
    print(f"  mode = {'APPLY' if apply else 'DRY-RUN'}")
    print(f"  backup = {backup}")
    print("=" * 70)

    results = []
    for patch in PATCHES:
        r = apply_patch(patch, apply=apply, backup=backup)
        results.append(r)

    # Summary table
    print("\nResults:")
    print(f"{'status':<20} {'file':<30} detail")
    print("-" * 70)
    for r in results:
        print(f"{r['status']:<20} {r['file']:<30} {r['detail']}")

    # Exit code
    hard_errors = [r for r in results
                   if r["status"] in ("MISSING", "ANCHOR_NOT_FOUND")]
    if hard_errors:
        print("\nERROR: some patches could not be applied. See above.")
        return 1

    if not apply:
        print("\n" + "=" * 70)
        print("  DRY-RUN complete. Re-run with --apply to execute.")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("  DONE. Recommended: git diff docs/")
        print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))