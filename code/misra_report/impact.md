# MISRA Impact Analysis

> Informational only. This report does not fail the build.
> Shows which `codegen/` source files are responsible for
> each MISRA violation detected in generated C code.

## Totals by category

| Category | Count |
|----------|------:|
| misra-active | 6 |
| non-misra | 10 |
| suppressed | 4 |
| other | 4 |

## Codegen sources to modify (ranked)

| Codegen source | Total hits | Top rules |
|----------------|-----------:|-----------|
| `codegen/code_templates.py` | 20 | knownConditionTrueFalse(6), redundantInitialization(4), misra-c2012-11.5(4) |
| `codegen/transition_generator.py` | 14 | knownConditionTrueFalse(6), redundantInitialization(4), variableScope(2) |
| `codegen/osal_generator.py` | 6 | misra-c2012-11.5(4), misra-c2012-18.4(2) |

## Rules to address (ranked)

| Rule | Total | Responsible codegen |
|------|------:|---------------------|
| knownConditionTrueFalse | 12 | `codegen/transition_generator.py`, `codegen/code_templates.py` |
| redundantInitialization | 8 | `codegen/transition_generator.py`, `codegen/code_templates.py` |
| misra-c2012-11.5 | 8 | `codegen/osal_generator.py`, `codegen/code_templates.py` |
| variableScope | 4 | `codegen/transition_generator.py`, `codegen/code_templates.py` |
| unreadVariable | 4 | `codegen/transition_generator.py`, `codegen/code_templates.py` |
| misra-c2012-18.4 | 4 | `codegen/osal_generator.py`, `codegen/code_templates.py` |

## Suggested action order

Based on frequency and estimated fix effort:

| # | Rule | Action | Hits |
|---|------|--------|-----:|
| 1 | misra-c2012-17.3 | Add missing includes in generated .c files | 0 |
| 2 | misra-c2012-17.7 | Add (void) cast to RoleFunc_* calls | 0 |
| 3 | unreadVariable | Add (void)var; for generated locals | 4 |
| 4 | knownConditionTrueFalse | Review _handled logic in cell functions | 12 |
| 5 | misra-c2012-12.1 | Add parentheses around operator expressions | 0 |
| 6 | variableScope | Reduce _handled variable scope | 4 |
| 7 | misra-c2012-11.5 | Add explicit casts in osal.c | 8 |
| 8 | misra-c2012-18.4 | Review pointer arithmetic in osal.c | 4 |
| 9 | misra-c2012-10.4 | Check type mismatch in statable_timer.c | 0 |

## Suppressed by design

The following rules are suppressed in `misra/suppressions.txt`.

- Suppressed hits: 4
