# ADR-0006: Three folder structures

- Status: Accepted
- Date: 2026-09-20 (recorded)
- Related: `SPEC_CODEGEN_v3.md` §9

## Context

Embedded projects use different source layouts. We needed an option to
fit common cases without forcing one structure.

Options considered:

1. Flat only.
2. Two structures: `flat` and `by_type`.
3. Three: `flat`, `by_type`, `by_layer`.

Option 3 was chosen to accommodate multi-layer projects (ADR-0002).

## Decision

Support three folder structures:

| Value | Layout |
|-------|--------|
| `flat` | All files in one directory |
| `by_type` | `include/` / `src/` / `common/` |
| `by_layer` | Per-layer subdirectories + common at root |

The GUI defaults to `by_type`.

## Consequences

### Positive
- Fits a range of common build systems.
- `by_layer` matches the tab model closely.

### Negative
- `by_layer` keys generated files as `"layer/filename"`, which requires
  special handling in the merge and save paths.

### Neutral
- `statable_all.h` is placed via `_resolve_super_include_path`, not by
  `FILE_CATEGORY`.