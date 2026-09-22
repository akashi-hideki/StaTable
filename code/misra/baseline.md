# MISRA C Check Baseline

> **Informational only.** cppcheck + MISRA addon is not a certified
> MISRA checker. Builds are not failed by this check.

## Versions

| Version | Date | Source XML | Notes |
|---------|------|-----------|-------|
| v2.5.2 | 2026-09-23 | docs/tutorial/vending_machine.xml | 3 layers, namespace=Vending |
| (initial) | 2026-09-20 | tests/data/v22_features_test3.xml | 3 layers, namespace=App |

## v2.5.2 - vending_machine

Recorded: 2026-09-23
Source XML: docs/tutorial/vending_machine.xml
Generated with: tools/gen_output_from_xml.py
Verified with: tools/verify_c_syntax.py --compiler both

### Summary

| Metric | Value |
|--------|-------|
| Files analyzed | 12 |
| Total MISRA rule hits | 3 |
| Distinct rules hit | 1 |
| Non-MISRA warnings | 11 |

### MISRA rules hit

| Rule | Count | Note |
|------|------:|------|
| misra-c2012-2.7 | 3 | Unused parameter `ctx` in MW_RESET transitions |

### Non-MISRA warnings (informational)

| ID | Count |
|----|------:|
| constParameterCallback | 3 |
| knownConditionTrueFalse | 2 |
| variableScope | 2 |
| unreadVariable | 2 |
| constVariablePointer | 1 |
| constParameterPointer | 1 |

### Action Items

- [x] Add `misra-c2012-2.7` to `misra/suppressions.txt`
      (justification: transition function signature is fixed by
       the function-pointer table; `ctx` cannot be removed)
- [ ] (future) Consider `(void)ctx;` auto-injection in
      `transition_generator.py` when `ctx` is unused

## v22_features_test3 (initial)

Recorded: 2026-09-20
Source XML: tests/data/v22_features_test3.xml

### Summary

| Metric | Value |
|--------|-------|
| Files analyzed | 12 |
| Total MISRA rule hits | 10 |
| Distinct rules hit | 4 |
| Non-MISRA warnings | 9 |

### MISRA rules hit

| Rule | Count |
|------|------:|
| misra-c2012-8.4 | 3 |
| misra-c2012-11.5 | 4 |
| misra-c2012-18.4 | 2 |
| misra-c2012-15.7 | 1 |

## Known issues

- `tools/run_misra_check.py` writes cppcheck XML to
  `cppcheck_raw.xml` (stdout) but cppcheck 2.21 emits XML to stderr.
  The script still parses correctly (see `find_xml()`), but
  `cppcheck_raw.xml` is empty. Tracked as a future improvement.
