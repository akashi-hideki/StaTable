# ADR-0004: 13-file code generation output

- Status: Accepted
- Date: 2026-09-20 (recorded)
- Related: `SPEC_CODEGEN_v3.md` §3.5

## Context

We needed to decide how many files the generator emits and how they are
partitioned. Options considered:

1. Single `.c` + single `.h`.
2. One file per concern (types, transitions, role functions, etc.).
3. Very fine-grained (one file per state).

Option 2 was chosen.

## Decision

Emit **13 files**:

| # | File |
|---|------|
| 1 | `statable_types.h` |
| 2 | `statable_transitions.h` |
| 3 | `statable_transitions.c` |
| 4 | `statable_role_functions.h` |
| 5 | `statable_role_functions.c` |
| 6 | `statable_init.c` |
| 7 | `statable_event_queue.c` |
| 8 | `statable_interrupt.c` |
| 9 | `statable_timer.c` |
| 10 | `osal.h` |
| 11 | `osal.c` |
| 12 | `statable_all.h` |
| 13 | `{project}_run.c` |

`statable_all.h` and `{project}_run.c` were added after the initial 11-file
design (v2.0 → v3.0) to support super-include and super-loop.

## Consequences

### Positive
- Clear separation of concerns.
- Users can replace individual generated files without touching others.
- Super-include reduces the boilerplate in user `main.c`.

### Negative
- More files to manage in the build system.
- `{project}_run.c` is named dynamically based on `project_name`, which
  means the file list is not entirely static.

### Neutral
- `statable_all.h` is resolved via a dedicated path resolver rather than
  `FILE_CATEGORY`.