# MISRA C Check for StaTable

This directory contains configuration and policy for the MISRA C:2012
check applied to StaTable-generated C code.

## Policy

- **Informational only.** The CI job never fails the build.
- **Not a certification.** cppcheck + MISRA addon is not a certified
  MISRA checker. It is a best-effort static analyzer.
- **No compliance claim.** Passing this check does NOT mean the
  generated code is MISRA-compliant. Final compliance is the
  responsibility of the user.

## Toolchain

| Tool | Version | Purpose |
|------|---------|---------|
| cppcheck | latest (apt) | Static analysis engine |
| misra addon | bundled with cppcheck | Rule mapping |

## What is checked

Only the files under the generated output directory:

- `output/src/*.c`
- `output/common/*.c` (if present)

Headers are analyzed indirectly via includes.

## What is NOT checked

- The StaTable Python source.
- The correctness of the state machine logic.
- Compilation for the target MCU.
- Runtime behavior.

## Coverage

cppcheck's MISRA addon does not cover all MISRA C:2012 rules.
The following categories are partially or fully outside its scope:

- Rules requiring whole-program analysis
- Rules requiring knowledge of target hardware
- Rules about documentation and process
- Rules about specific language extensions

Approximate coverage: **~60–70% of MISRA C:2012 rules.**

For full coverage, a commercial tool (PC-lint Plus, Helix QAC,
Coverity) is required.

## Suppressions

Suppressions are in `suppressions.txt`. Each must have a rationale
comment. Do not suppress without justification.

## Baseline

`baseline.md` records the initial state (first measured run).
Update it after each significant change to the generated code.

## Progress Tracking

1. Run the CI job.
2. Download the `misra-report` artifact.
3. Review `summary.md`.
4. Add justified suppressions if needed.
5. Update `baseline.md`.

## Future Improvements

- [ ] Add a threshold (e.g., fail if total hits increase by >10%).
- [ ] Track per-rule trends over time.
- [ ] Evaluate commercial MISRA checkers.
- [ ] Achieve MISRA C:2012 compliance for the core templates.

## Disclaimer

StaTable is not a certified MISRA checker. Generated code is provided
"AS IS". Users are responsible for final verification against their
applicable standards.