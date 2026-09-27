# code/tools/patches/patch_v2_8_readme_highlight.py
"""
Add a "What's New in v2.8.0" highlight section to the README,
right after the badges / intro (i.e. immediately before the first
'## Why StaTable?' heading).

Idempotent: skips if "## What's New in v2.8.0" already exists.

Usage:
    cd code
    python tools\\patches\\patch_v2_8_readme_highlight.py            # dry-run
    python tools\\patches\\patch_v2_8_readme_highlight.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
README = REPO / "README.md"


NEW_SECTION = """## What's New in v2.8.0

> **AI Diagnosis Refresh** — Released 2026-09-27
> See the [full release notes](https://github.com/akashi-hideki/StaTable/releases/tag/v2.8.0).

The AI diagnosis workflow in `codegen/validate/` has been completely
rewritten for reliability and transparency.

| Area | Before | After |
|------|--------|-------|
| **Prompt** | Flat `[Task]` text | 10 XML sections, full `<context>` (role_functions / cells / global_definitions) |
| **Response** | Undefined schema | `id` / `evidence` / `priority` / `confidence` fields |
| **Parser** | Fragile brace matching | `<response>...</response>` marker, all **17 actions** |
| **Validation** | None | `ResponseValidator` — schema / params / references checked **before** applying |
| **GUI** | 4-column list | **7-column** list with Priority, Confidence, Status; excluded rows clearly marked |

**Test status:** 4 new suites (+311 assertions), CI green.

**⚠️ Operational testing pending.** The AI features are design- and
unit-test complete, but end-to-end testing with a real LLM has not
been performed yet. AI proposals should be treated as review aids
only until OT completes. See the [v2.8.0 section](#v280--ai-diagnosis-refresh-design--unit-test-complete-operational-testing-pending)
below for details.

"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v2_8_readme_highlight  [{mode}]")
    print("=" * 70)

    if not README.exists():
        print(f"[FAIL] README not found: {README}")
        return 1

    text = README.read_text(encoding="utf-8")

    if "## What's New in v2.8.0" in text:
        print("[SKIP] '## What's New in v2.8.0' already present")
        return 0

    anchor = "## Why StaTable?"
    idx = text.find(anchor)
    if idx == -1:
        print(f"[FAIL] anchor '{anchor}' not found")
        return 1

    patched = text[:idx] + NEW_SECTION + text[idx:]
    print(f"[APPLY] insert '## What's New in v2.8.0' before "
          f"'{anchor}' at offset {idx}")

    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    bak = README.with_suffix(README.suffix + ".bak_highlight")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak}")

    README.write_text(patched, encoding="utf-8")
    print(f"[DONE] README.md updated ({len(patched)} chars)")
    print()
    print("Verify:")
    print("  python tests\\test_readme_consistency.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())