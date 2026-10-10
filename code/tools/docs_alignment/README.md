# Docs Alignment Scripts (v3.4.3)

One-time scripts used to align `code/docs/samples/*.md` with
`cooking_heater_controller.xml` at v3.4.3.

## Diagnostic
- `dump_xml_structure.py`   — dump current XML structure (tabs/states/roles)
- `extract_doc_outdated.py` — find outdated strings in docs
- `verify_docs_alignment.py`— cross-check XML vs docs

## Stage A (mechanical)
- `align_docs_stage_a.py`   — 6->7 layers, 23->31 states, 54->60 roles

## Stage B (structural)
- `align_docs_stage_b2a.py`   — §4.1 Driver -> DriverInput + DriverOutput
- `align_docs_stage_b2b.py`   — chapter renumbering §4.2-4.6 -> §4.3-4.7
- `align_docs_stage_b2c.py`   — TOC + version
- `align_docs_stage_b2def.py` — §2.1-2.3 (Mermaid / table / namespace)
- `align_docs_stage_b2g.py`   — §3.1-3.3 (design theory)
- `align_docs_stage_b2h.py`   — §4.3 MwMicrowave + §4.6 MwSteam
- `align_docs_stage_b245.py`  — LAYER changelog + README + INSTALL
- `align_docs_stage_b3b.py`   — ROLE_FUNCTIONS §3 replacement
- `align_docs_stage_b3c.py`   — ROLE_FUNCTIONS chapter renumbering
- `align_docs_stage_b3d.py`   — ROLE_FUNCTIONS TOC
- `align_docs_stage_b3e.py`   — ROLE_FUNCTIONS changelog + blank-line fix

## Extractor-only (diagnostic)
- `align_docs_stage_b1.py`, `align_docs_stage_b2d1.py`,
  `align_docs_stage_b2g1.py`, `align_docs_stage_b2h1.py`,
  `align_docs_stage_b3a.py` — section extractors used for verification

All scripts are **idempotent** (safe to re-run).