# ADR-0012: Fixed generation style and table type

- Status: Accepted
- Date: 2026-09-20 (recorded)
- Related: `SPEC_CODEGEN_v3.md` §11 (Known Constraints)

## Context

`CodeGenerationConfig` declares several generation styles and table
types. Only some are implemented:

| Setting | Implemented |
|---------|-------------|
| `generation_style = table_driven` | ✅ |
| `generation_style = switch_case` | ❌ (fallback) |
| `table_type = array` | ✅ |
| `table_type = switch` | ❌ (fallback) |
| `table_type = dictionary` | ❌ (fallback) |

Two options were considered:

1. Expose all options in the GUI, letting users choose unimplemented ones
   and see a fallback warning.
2. Expose only implemented options.

Option 2 was chosen.

## Decision

The settings dialog forces:

- `generation_style = "table_driven"`
- `table_type = "array"`

The config fields remain in `CodeGenerationConfig` for future use.

## Consequences

### Positive
- Users cannot accidentally select unimplemented options.
- No fallback warnings appear in normal use.

### Negative
- The config schema suggests capabilities that the UI does not expose.
- Auditors must read the code to understand the true behavior.

### Neutral
- If a future implementation adds support, only the settings dialog
  needs to be updated.