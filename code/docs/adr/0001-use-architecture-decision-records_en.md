# ADR-0001: Use Architecture Decision Records

- Status: Accepted
- Date: 2026-09-20
- Related: (none)

## Context

StaTable has accumulated a set of architectural decisions over multiple
development stages. These decisions were made in code and commit messages
but not always recorded as standalone documents. Auditors and new
maintainers have asked for a way to understand *why* certain design
choices were made.

Two alternatives were considered:

1. A "risk register" listing known issues and proposed fixes.
2. Architecture Decision Records (ADRs).

A risk register tends to be read as a **commitment to future work**,
which places an ongoing obligation on the project. An ADR records a
**point-in-time decision**, which limits the responsibility to the
original judgment.

## Decision

Adopt Architecture Decision Records using the MADR format. Place them
under `docs/adr/`.

## Consequences

### Positive
- Decisions are recorded with their context.
- New maintainers can understand rationale without reverse-engineering.
- ADRs are not read as future commitments.

### Negative
- Requires discipline to write a new ADR for each significant decision.

### Neutral
- ADRs supersede each other; existing ones are not edited in place.