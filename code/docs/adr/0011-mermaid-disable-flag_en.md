# ADR-0011: Mermaid rendering with disable flag

- Status: Accepted
- Date: 2026-09-20 (recorded)
- Related: `SPEC_SCREENS_en.md` §2.6, `statable_gui/widgets.py`

## Context

The state transition diagram is rendered with Mermaid.js inside a
`QWebEngineView`. `QWebEngineView` requires `PySide6-Addons` and a
graphics stack, which is heavy for headless CI.

Options considered:

1. Always require WebEngine.
2. Skip rendering if import fails.
3. Add an environment variable to explicitly disable.

Option 3 was chosen.

## Decision

Support `STATABLE_DISABLE_MERMAID=1`. When set, `MermaidWidget` shows a
placeholder label and does not import `QWebEngineView`.

## Consequences

### Positive
- CI runs without installing QtWebEngine.
- Local headless testing works.

### Negative
- Users must set the variable to benefit from faster startup.
- The rendering path is less exercised in CI.

### Neutral
- The env var is read at module load time, not per-instance.