# ADR-0010: All dialogs modal

- Status: Accepted
- Date: 2026-09-20 (recorded)
- Related: `SPEC_SCREENS_en.md` §8

## Context

StaTable has many dialogs that edit model data (global definitions,
events, transitions, etc.). We had to decide between:

1. Modal dialogs (`exec()`), one at a time.
2. Modeless dialogs, allowing multiple simultaneous editors.

Option 1 was chosen.

## Decision

All dialogs use `exec()`. The main window is blocked while a dialog is
open.

## Consequences

### Positive
- No concurrent edits to the same model.
- Simpler lifetime management (dialog state is transient).

### Negative
- Users cannot view the transition matrix while editing a transition.
- Nested dialogs (e.g., `ActionEditorDialog` → `ConditionBuilderDialog`)
  block each other in a stack.

### Neutral
- The Mermaid preview cannot be updated while a dialog is open.