# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for StaTable.

## What is an ADR?

An ADR captures a significant architectural decision along with its context and consequences. ADRs are:

- **Point-in-time records** of past decisions
- **Not commitments** to future work
- **Superseded**, not edited, when decisions change

## Format

We use the [MADR](https://adr.github.io/madr/) format:

```
# ADR-NNNN: Title

- Status: Proposed | Accepted | Deprecated | Superseded by ADR-XXXX
- Date: YYYY-MM-DD
- Related: (specs, issues)

## Context
## Decision
## Consequences (Positive / Negative / Neutral)
```

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-use-architecture-decision-records.md) | Use Architecture Decision Records | Accepted |
| [0002](0002-multi-layer-via-tabs.md) | Multi-layer state machines via tabs | Accepted |
| [0003](0003-role-function-namespace.md) | Role function namespace design | Accepted |
| [0004](0004-13-file-code-generation.md) | 13-file code generation output | Accepted |
| [0005](0005-marker-based-user-code-preservation.md) | Marker-based user code preservation | Accepted |
| [0006](0006-three-folder-structures.md) | Three folder structures | Accepted |
| [0007](0007-isr-context-support.md) | ISR context support (Stage 3) | Accepted |
| [0008](0008-namespace-dot-notation.md) | Namespace.Name dot notation (Stage 4) | Accepted |
| [0009](0009-entry-exit-as-list.md) | State.entry / State.exit as List[str] | Accepted |
| [0010](0010-modal-only-dialogs.md) | All dialogs modal | Accepted |
| [0011](0011-mermaid-disable-flag.md) | Mermaid rendering with disable flag | Accepted |
| [0012](0012-fixed-generation-style.md) | Fixed generation style and table type | Accepted |