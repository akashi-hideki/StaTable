# MISRA C Check Summary

> **Informational only.** This report does not fail the build.
> cppcheck + MISRA addon is not a certified MISRA checker.

## Overview

- Files analyzed: 12
- Total MISRA rule hits: 0
- Distinct MISRA rules hit: 0
- Non-MISRA warnings: 10

## Non-MISRA warnings (by frequency)

| ID | Count | Sample message |
|----|------:|----------------|
| knownConditionTrueFalse | 3 | Condition '!_handled' is always true |
| redundantInitialization | 2 | Redundant initialization for 'next_state'. The initialized value is overwritten  |
| variableScope | 2 | The scope of the variable '_handled' can be reduced. |
| unreadVariable | 2 | Variable '_handled' is assigned a value that is never used. |
| constVariablePointer | 1 | Variable 'src' can be declared as pointer to const |

## Artifacts

- `cppcheck_raw.xml` — XML from stdout
- `cppcheck_stderr.txt` — XML from stderr (may be empty)

## Next Steps

1. Review top rules above.
2. Add justified suppressions to `misra/suppressions.txt`.
3. Record progress in `misra/baseline.md`.
