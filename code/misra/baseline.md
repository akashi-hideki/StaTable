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
| Total MISRA rule hits | 0 |
| Distinct rules hit | 0 |
| Non-MISRA warnings | 11 |

> Note: The initial run (before `misra-c2012-2.7` was added to
> `misra/suppressions.txt`) reported 3 hits.  After suppression, the
> count is 0.

### MISRA rules hit

なし（`misra-c2012-2.7` は `suppressions.txt` に登録済み）

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
- [x] (v2.5.2) `(void)ctx;` auto-injection implemented in
      `transition_generator.py`
- [x] (v2.5.3) MISRA check now runs correctly (R-15 resolved)

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

（なし。R-15 は v2.5.3 で解決済み）

### Resolved

- **R-15** (v2.5.3, 2026-09-23): `tools/run_misra_check.py` produced
  an empty `cppcheck_raw.xml` and MISRA rule hits = 0 due to three
  compounding issues:
  1. `misra/suppressions.txt` had a UTF-8 BOM, causing cppcheck to
     abort before emitting any XML ("Invalid id").
  2. `subprocess.run(text=True)` used the Windows locale encoding
     (cp932) and crashed on cppcheck's UTF-8 output.
  3. The script wrote `result.stdout` to `cppcheck_raw.xml`, but
     cppcheck 2.21 emits XML on stderr.
  Fixed by: BOM removal, forcing `encoding='utf-8'` in subprocess,
  and routing `find_xml()`'s result to `cppcheck_raw.xml`.
  Raw streams preserved as `cppcheck_stdout.txt` / `cppcheck_stderr.txt`.
  A BOM guard was added before invoking cppcheck to prevent regressions.