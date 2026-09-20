# MISRA C Check Summary

> **Informational only.** This report does not fail the build.
> cppcheck + MISRA addon is not a certified MISRA checker.

## Overview

- Files analyzed: 12
- Total MISRA rule hits: 10
- Distinct MISRA rules hit: 4
- Non-MISRA warnings: 9

## MISRA rules (by frequency)

| Rule | Count |
|------|------:|
| misra-c2012-11.5 | 4 |
| misra-c2012-8.4 | 3 |
| misra-c2012-18.4 | 2 |
| misra-c2012-15.7 | 1 |

## Non-MISRA warnings (by frequency)

| ID | Count | Sample message |
|----|------:|----------------|
| knownConditionTrueFalse | 3 | Condition '!_handled' is always true |
| redundantInitialization | 2 | Redundant initialization for 'next_state'. The initialized value is overwritten  |
| variableScope | 2 | The scope of the variable '_handled' can be reduced. |
| unreadVariable | 2 | Variable '_handled' is assigned a value that is never used. |

## Artifacts

- `cppcheck_raw.xml` — XML from stdout
- `cppcheck_stderr.txt` — XML from stderr (may be empty)

## Next Steps

1. Review top rules above.
2. Add justified suppressions to `misra/suppressions.txt`.
3. Record progress in `misra/baseline.md`.
