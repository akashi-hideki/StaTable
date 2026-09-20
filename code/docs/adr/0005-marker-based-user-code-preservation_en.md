# ADR-0005: Marker-based user code preservation

- Status: Accepted
- Date: 2026-09-20 (recorded)
- Related: `SPEC_CODEGEN_v3.md` §7, `codegen/code_merger.py`

## Context

Generated files must be regenerable without destroying user edits.
Several approaches were considered:

1. Never overwrite existing files.
2. Separate "generated" and "user" sections with a fixed marker.
3. Regenerate always and require users to keep patches.

Option 2 was chosen.

## Decision

Insert comment markers into generated files:

| Marker | Scope |
|--------|-------|
| `[[STABLE_USER_CODE_START]]` / `_END` | File-level user code |
| `[[STABLE_USER_CODE_START:<name>]]` / `_END:<name>` | Function-level user code |
| `[[STABLE_USER_CODE_TAIL_START]]` / `_END` | File-tail user code |

The merge process extracts these regions from the existing file and
injects them into the newly generated file.

## Consequences

### Positive
- Users can edit inside markers and keep their edits across regeneration.
- Files without markers are fully regenerated.

### Negative
- Users must not delete or rename markers manually.
- Function markers depend on generated function names (`RoleFunc_*`, `ISR_*`).

### Neutral
- Markers are English-only ASCII comments, compatible with the
  `no-japanese` CI check.