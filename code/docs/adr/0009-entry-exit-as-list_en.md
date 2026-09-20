# ADR-0009: State.entry / State.exit as List[str]

- Status: Accepted
- Date: 2026-09-20 (recorded, v2.2)
- Related: `statable_gui/widgets.py` (v2.2), `statable/model.py`

## Context

Before v2.2, `State.entry` and `State.exit` were single strings. As
projects grew, users wanted multiple entry/exit actions per state.

Options considered:

1. Keep single string, use semicolon-separated user input.
2. Change the model to `List[str]`.

Option 2 was chosen.

## Decision

- `State.entry: List[str]`
- `State.exit: List[str]`
- `State.do: str` (unchanged)

The UI displays `List[str]` as `"; "`-joined strings.

Conversion helpers:

| Function | Direction |
|----------|-----------|
| `_list_to_display(items)` | `List[str]` → `"A; B; C"` |
| `_display_to_list(text)` | `"A; B; C"` → `List[str]` |

XML I/O handles both forms and normalizes on read.

## Consequences

### Positive
- Multiple entry/exit actions are first-class.
- Round-trip through XML is lossless.

### Negative
- Split on `";"` assumes no semicolon inside individual action strings.
- `State.do` remains a single string, creating an inconsistency.

### Neutral
- The same helpers are used in `SettingsPanel.populate` and
  `SettingsPanel.apply_changes`.