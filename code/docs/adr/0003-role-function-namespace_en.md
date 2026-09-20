# ADR-0003: Role function namespace design

- Status: Accepted
- Date: 2026-09-20 (recorded)
- Related: `statable/model.py`, `statable/state_machine.py`, `statable_gui/libcntrl/role_function_library.py`

## Context

Role functions need to be uniquely identified. Two options were
considered:

1. Flat namespace with fully qualified names (`Driver_Init`).
2. Namespace + name pair (`Driver`, `Init`), exposed as `qualified_name`.

Option 2 was chosen to support the tab-based layer model (ADR-0002).

## Decision

`RoleFunction` carries:

- `name` (pure): `"Init"`
- `namespace`: `"Driver"`
- `qualified_name` (property): `"Driver.Init"`

However, the two libraries that store role functions use **different
uniqueness keys**:

| Library | Key |
|---------|-----|
| `statable.StateMachine.role_functions` | `name` (pure) |
| `libcntrl.RoleFunctionLibrary.role_functions` | `qualified_name` |

## Consequences

### Positive
- Namespaces allow cross-layer disambiguation in most operations.
- Legacy names (`Driver_Init`) migrate automatically during XML load.

### Negative
- `StateMachine` cannot hold two role functions with the same pure name
  but different namespaces.
- Code must be careful to use `get` with fallback when looking up by
  either form.

### Neutral
- This asymmetry is documented as a known constraint.