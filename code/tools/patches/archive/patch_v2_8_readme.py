# code/tools/patch_v2_8_readme.py
"""
Patch v2.8.0 README.

Adds a new "v2.8.0" section describing the AI prompt refresh and,
crucially, an operational-testing disclaimer for the AI features.

Insertion policy (in order):
  1. If README already contains "## v2.8.0" → skip (idempotent).
  2. Insert before "## Roadmap"       (groups with version info).
  3. Else insert before "## License"  (end-of-document fallback).
  4. Else append at end of file.

Usage:
    cd code
    python tools\\patch_v2_8_readme.py
    python tools\\patch_v2_8_readme.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
README = REPO / "README.md"


NEW_SECTION = """## v2.8.0 — AI Diagnosis Refresh (design + unit-test complete, operational testing pending)

### Summary

The AI diagnosis workflow in `codegen/validate/` has been substantially
rewritten. The old `[Task]` / `[Output format]` prompt has been replaced
by a full XML-tagged specification (`SPEC_AI_PROMPT_v1.1`) with a
matching response schema, a stricter parser, and a new validation layer
between parsing and application.

### What changed

| Area | Before | After |
|------|--------|-------|
| Prompt structure | Flat `[Task]` text | 10 XML sections (`<system>`, `<workflow>`, `<task>`, `<output_schema>`, `<examples>`, `<constraints>`, `<context>`, `<validation>`, `<actions>`, `<response_format>`) |
| Context sent to AI | States / events / transitions only | + role_functions / cells / global_definitions, full ActionStep detail, EventTrigger |
| Output schema | Undefined | `version` / `summary` / `changes[]` with `id` / `evidence` / `priority` / `confidence` |
| Response extraction | Fragile brace matching | `<response>...</response>` marker first, `<json>...` legacy fallback |
| Action coverage | 10 legacy actions | All 17 actions (10 legacy + 7 cell-level) |
| Pre-apply validation | None | `ResponseValidator` (schema / params / references) |
| GUI change list | 4 columns | 7 columns (Selection / Action / Parameter / Reason / Priority / Confidence / Status), excluded rows shown as `EXCLUDED: <reason>` |

### New / updated files

| File | Status |
|------|--------|
| `codegen/validate/data/prompt_templates.py` | Rewritten |
| `codegen/validate/prompt_generator.py` | Rewritten (`_format_data`, `_format_validation`, `_format_actions` extended) |
| `codegen/validate/change_actions.py` | `ChangeRequest` extended (id / evidence / priority / confidence) |
| `codegen/validate/response_parser.py` | `<response>` marker priority, 17-action mapping |
| `codegen/validate/response_validator.py` | **New** |
| `codegen/validate/validation_dialog.py` | ResponseValidator integration, 7-column change tree |
| `tests/test_v2_8_p1_ai_prompt.py` | **New** (123 assertions) |
| `tests/test_v2_8_p2_response_parser.py` | **New** (106 assertions) |
| `tests/test_v2_8_p3_response_validator.py` | **New** (56 assertions) |
| `tests/test_v2_8_p4_gui_integration.py` | **New** (26 assertions) |
| `docs/SPEC_AI_PROMPT_v1.md` | **New** (v1.1, design spec) |
| `tools/gui_smoke_v2_8.py` | **New** (headless GUI smoke test) |

### Test status

| Suite | Result |
|-------|:------:|
| `test_v2_8_p1_ai_prompt.py` | 123 PASS / 0 FAIL |
| `test_v2_8_p2_response_parser.py` | 106 PASS / 0 FAIL |
| `test_v2_8_p3_response_validator.py` | 56 PASS / 0 FAIL |
| `test_v2_8_p4_gui_integration.py` | 26 PASS / 0 FAIL |
| Regression `test_v2_2_p12_6.py` | 55 PASS / 0 FAIL |

### ⚠️ Operational testing status of the AI features

The AI diagnosis workflow has been **designed, implemented, and
unit-tested**, but **end-to-end operational testing with a real
LLM is still pending**. In particular:

- The prompt has not yet been validated against a wide variety of
  LLM providers / models in real sessions.
- The `evidence` / `priority` / `confidence` fields are advisory;
  they have not been calibrated against measured outcomes.
- The GUI change-list integration is unit-tested but has not been
  exercised in a sustained multi-user workflow.
- The few-shot examples shipped in `prompt_templates.py` reflect
  the intended response shape but have not been tuned on
  production-scale designs.

Until operational testing is complete, **AI proposals should be
treated as review aids only** and every proposed change should be
examined by a human before applying it. If you observe a parsing
or validation failure, please capture:

- the raw AI reply,
- the entries shown in the `Change list / apply` tab,
- the log lines from `logs/validate_*.log`.

These will drive the next iteration of the prompt and validator.

"""


def find_insertion_index(text: str) -> tuple[int, str]:
    """Return (index, label) for the best insertion point."""
    for heading, label in (
        ("## Roadmap", "before '## Roadmap'"),
        ("## License", "before '## License'"),
        ("## Licence", "before '## Licence'"),
    ):
        idx = text.find(heading)
        if idx != -1:
            return idx, label
    return len(text), "append at end"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    print("=" * 70)
    print("  patch_v2_8_readme")
    print("=" * 70)

    if not README.exists():
        print(f"[FAIL] README not found: {README}")
        return 1

    text = README.read_text(encoding="utf-8")

    if "## v2.8.0" in text:
        print("[SKIP] README already contains a '## v2.8.0' section")
        return 0

    idx, label = find_insertion_index(text)

    if idx == len(text):
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + NEW_SECTION
    else:
        text = text[:idx] + NEW_SECTION + text[idx:]

    print(f"[APPLY] {label} at offset {idx}")

    if args.dry_run:
        print("[DRY-RUN] no file written")
        return 0

    bak = README.with_suffix(README.suffix + ".bak")
    if not bak.exists():
        bak.write_text(README.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  Backup: {bak}")

    README.write_text(text, encoding="utf-8")
    print(f"[DONE] README.md updated ({len(text)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())