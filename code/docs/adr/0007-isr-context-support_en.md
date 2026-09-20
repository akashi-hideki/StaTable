# ADR-0007: ISR context support (Stage 3)

- Status: Accepted
- Date: 2026-09-20 (recorded)
- Related: `SPEC_CODEGEN_v3.md` §4.8

## Context

Before Stage 3, ISRs could only call a limited set of functions because
they had no access to `SystemContext_t`. We wanted ISRs to call role
functions directly.

Options considered:

1. Require ISRs to use a global `g_ctx` directly.
2. Insert a local `ctx` pointer automatically into each generated ISR.
3. Leave ISR bodies entirely to the user.

Option 2 was chosen.

## Decision

Each generated ISR contains:

```c
SystemContext_t *ctx = &g_ctx;
(void)ctx;
```

Actions written as `Driver.Init` or `Init(args)` are converted to
`RoleFunc_<...>_<Pascal>(NULL, ctx)`.

`used_role_functions` and `used_variables` are extracted from the ISR
actions and written back into the model (`InterruptHandlerDef`).

## Consequences

### Positive
- ISRs can call role functions with full context access.
- Role functions are NULL-guarded for `transition` so that ISR calls
  (`transition == NULL`) remain safe.

### Negative
- Role functions now must handle `transition == NULL` in their bodies.
- The `(void)ctx;` line is generated even if unused.

### Neutral
- `statable_interrupt.c` now includes `statable_all.h` in addition to
  `statable_types.h`.