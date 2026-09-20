# ADR-0008: Namespace.Name dot notation (Stage 4)

- Status: Accepted
- Date: 2026-09-20 (recorded)
- Related: `SPEC_CODEGEN_v3.md` §4.3, `codegen/role_function_generator.py`

## Context

Role functions are stored with separate `name` and `namespace` fields,
but users write transitions in a text form. We needed a way for users to
reference role functions unambiguously across layers.

Options considered:

1. Require underscore form: `Driver_Init`.
2. Support dot form: `Driver.Init`.
3. Support both.

Option 3 was chosen for backward compatibility.

## Decision

Accept all of the following in conditions, pre/else actions, and ISR
actions:

| Input | Normalized |
|-------|-----------|
| `Driver.Init` | `Driver.Init` |
| `Driver.Init(arg1)` | `Driver.Init` |
| `RoleFunc_Driver_Init` | `Driver.Init` (if layer matches) |
| `Init` | `Init` |

Normalization is done by `_normalize_func_ref` in
`role_function_generator.py`. The call site lookup tries
`qualified_name` first, then falls back to `name`.

## Consequences

### Positive
- Users can write intuitive references.
- Legacy underscore names still work.

### Negative
- Bare identifiers in conditions are heuristically interpreted as
  potential function references (PascalCase only, to reduce false
  positives).

### Neutral
- C keywords are filtered out via a keyword set.