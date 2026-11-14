# code/tools/patches/patch_v2_8_roadmap.py
"""
Add a v2.8.0 entry to the README Roadmap section.

Inserts an '### v2.8.0' subsection immediately after the
'## Roadmap' heading.

Idempotent: skips if '### v2.8.0' already exists.

Usage:
    cd code
    python tools\\patches\\patch_v2_8_roadmap.py
    python tools\\patches\\patch_v2_8_roadmap.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
README = REPO / "README.md"


NEW_ENTRY = """### v2.8.0 — AI Diagnosis Refresh ✅ Released (2026-09-27)

**Status:** Released

Complete refresh of the AI diagnosis workflow in `codegen/validate/`.

**Highlights**

- **Prompt**: XML-tagged structure (10 sections) replacing the legacy
  `[Task]` / `[Output format]` text. `<context>` now includes
  role_functions, cells, and global_definitions.
- **Schema**: `ChangeRequest` extended with `id` / `evidence` /
  `priority` / `confidence`. Round-trip safe.
- **Parser**: `<response>...</response>` marker is the primary
  extraction path. All 17 actions (10 legacy + 7 cell-level) covered.
- **Validator** (`response_validator.py`, new): schema / params /
  references checks before application.
- **GUI**: `ValidationDialog` change list extended to 7 columns
  (Selection / Action / Parameter / Reason / Priority / Confidence /
  Status). Excluded rows show `EXCLUDED: <reason>` and are non-checkable.
- **Tests**: 4 new suites (P1-P4, +311 assertions), all green in CI.
- **CI**: `.github/workflows/check.yml` registers the 4 new suites.

**⚠️ Operational testing pending**

The AI features are design- and unit-test complete, but end-to-end
operational testing with a real LLM has not yet been performed.
Until OT is complete, AI proposals should be treated as review aids
only. See the `## v2.8.0` section above for details.

"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v2_8_roadmap  [{mode}]")
    print("=" * 70)

    if not README.exists():
        print(f"[FAIL] README not found: {README}")
        return 1

    text = README.read_text(encoding="utf-8")

    if "### v2.8.0" in text:
        print("[SKIP] '### v2.8.0' already present in README")
        return 0

    anchor = "## Roadmap\n"
    idx = text.find(anchor)
    if idx == -1:
        print("[FAIL] '## Roadmap' heading not found")
        return 1

    insert_at = idx + len(anchor)
    tail = text[insert_at:]
    insert_text = ("\n" + NEW_ENTRY) if not tail.startswith("\n") \
        else NEW_ENTRY

    patched = text[:insert_at] + insert_text + text[insert_at:]
    print(f"[APPLY] insert '### v2.8.0' at offset {insert_at}")

    if not args.apply:
        print("[DRY-RUN] no file written; pass --apply to execute.")
        return 0

    bak = README.with_suffix(README.suffix + ".bak_roadmap")
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