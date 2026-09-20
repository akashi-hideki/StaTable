# StaTable Audit Specification v1.0 (English)

Version: 1.0
Date: 2026-09-20
Purpose: Audit and handover
Audience: Auditors, new maintainers, technical reviewers
Source basis: All existing specifications (OVERVIEW / SCREENS / SEQUENCES / CODEGEN v3.0)

This document consolidates audit-relevant facts from the project specification set.
It is not a user manual. For operational procedures, refer to `SPEC_SCREENS_en.md`.

---

## Table of Contents

1. Purpose and Scope
2. System Boundary
3. Component Inventory
4. Data Model Contracts
5. Code Generation Contracts
6. GUI Contracts
7. Known Constraints (Comprehensive)
8. Unimplemented Features
9. Verification and CI
10. Risk Register
11. Handover Checklist
12. Revision History

---

## 1. Purpose and Scope

### 1.1 Purpose

Provide a single auditable reference covering:

- What StaTable does and what it does not
- Where each behavior is implemented
- Which constraints are known, documented, and accepted
- Which features are unimplemented and their fallback behavior
- What has been verified and how

### 1.2 In Scope

| Item | Detail |
|------|--------|
| Source packages | `statable/`, `statable_gui/`, `codegen/` |
| Test suite | `code/tests/test_v2_2_p*.py` (12 suites) |
| CI | `.github/workflows/check.yml` |
| Verification tools | `code/tools/find_all_japanese.py`, `code/tools/verify_generated_code.py` |

### 1.3 Out of Scope

- Feature requests / roadmap
- Third-party dependencies beyond their declared role
- Hardware-specific behavior of generated C code

---

## 2. System Boundary

### 2.1 External Interfaces

| Interface | Direction | Format | Provider |
|-----------|-----------|--------|----------|
| Project XML | In / Out | XML (UTF-8) | `statable/xml_io.py` |
| Generated C code | Out | C99 source (UTF-8) | `codegen/` |
| Settings JSON | Out | JSON (UTF-8) | `statable_gui/code_generation_dialog.py` |
| Logger stream | Out | Python `logging` | `statable_gui/logger.py` |
| GitHub Actions | Out | YAML | `.github/workflows/check.yml` |

### 2.2 Dependency Direction (Strict)

```
statable_gui  →  codegen  →  statable
libcntrl      →  (none)
transition_editor_direct  →  statable_gui
```

**No reverse dependency** exists. This was verified by module-level import analysis.

### 2.3 Runtime Environment

| Item | Requirement |
|------|------------|
| Python | 3.12 |
| GUI framework | PySide6 (Qt 6) |
| GUI addon | PySide6-Addons (for `QWebEngineView`) |
| OS (dev) | Windows 10/11, Linux (Ubuntu 22.04+) |
| OS (CI) | `ubuntu-latest` |

---

## 3. Component Inventory

### 3.1 Packages

| Package | Purpose | File count |
|---------|---------|-----------|
| `statable/` | Data model, XML I/O, Mermaid generation | 7 (excluding `__init__.py`) |
| `statable_gui/` | GUI screens, dialogs | ~20 |
| `statable_gui/libcntrl/` | Shared libraries | 5+ |
| `statable_gui/transition_editor_direct/` | D&D transition editor | 8 |
| `codegen/` | C code generation | 16 |
| `code/tests/` | Test suites | 12 |
| `code/tools/` | Verification tools | 2 |

### 3.2 Entry Points

| Entry point | Path | Purpose |
|-------------|------|---------|
| Application launch | `python -m statable_gui.main` | GUI startup |
| Test execution | `python tests/test_v2_2_p*.py` | Individual suites |
| C code verification | `python tools/verify_generated_code.py --root output` | Post-generation check |
| CI | `git push` to `main` / `develop` | Automated checks |

---

## 4. Data Model Contracts

### 4.1 `StateMachine` Key Uniqueness (Audit Finding)

| Collection | Key | Source |
|-----------|-----|--------|
| `states` | `state.name` | `state_machine.py` |
| `events` | `event.name` | `state_machine.py` |
| `role_functions` | **`rf.name` (pure)** | `state_machine.py` |
| `transitions` | list (no key) | `state_machine.py` |

**Critical**: `role_functions` uses the **pure name** as its key. Two role functions with the same pure name but different namespaces (e.g., `Driver.Init` and `App.Init`) **collide** in `StateMachine`. Only one survives.

### 4.2 `RoleFunction.qualified_name` (Audit Finding)

| Location | Key | Type |
|----------|-----|------|
| `statable.StateMachine.role_functions` | `rf.name` | pure name |
| `libcntrl.RoleFunctionLibrary.role_functions` | `rf.qualified_name` | `namespace.name` |

**Asymmetry**: The two libraries use different uniqueness keys for the same conceptual object.

### 4.3 XML Round-trip Fidelity (Audit Finding)

| Field | Saved? | Reloaded? | Note |
|-------|--------|-----------|------|
| `super_include_dir` | ❌ | ❌ | Resets to `"common"` |
| `external_includes` | ✅ | ✅ | Basename only |
| `used_role_functions` (ISR) | ✅ | ✅ | `<UsedRoleFunction ref="..."/>` |
| `used_variables` (ISR) | ✅ | ✅ | `<UsedVariable name="..."/>` |
| `RoleFunction.namespace` | ✅ | ✅ | Auto-migrates legacy names |
| `State.entry` / `State.exit` | ✅ | ✅ | `List[str]` (v2.2) |

### 4.4 `Transition` Default Values (Audit Reference)

| Field | Default | Meaning |
|-------|---------|---------|
| `condition` | `""` | Empty = unconditional |
| `has_else` | `True` | else clause active by default |
| `else_target` | `""` | else target unset |
| `transition_type` | `"external"` | Type label |

---

## 5. Code Generation Contracts

### 5.1 Output Contract

| # | File | Type | Purpose |
|---|------|------|---------|
| 1 | `statable_types.h` | Header | Types, structs, macros |
| 2 | `statable_transitions.h` | Header | Transition declarations |
| 3 | `statable_transitions.c` | Source | Cell functions, transition table, Process |
| 4 | `statable_role_functions.h` | Header | Role function declarations |
| 5 | `statable_role_functions.c` | Source | Role function implementations, call_sites |
| 6 | `statable_init.c` | Source | `SystemContext_Init` |
| 7 | `statable_event_queue.c` | Source | Queue implementation |
| 8 | `statable_interrupt.c` | Source | ISRs |
| 9 | `statable_timer.c` | Source | Timer struct + Init/Update |
| 10 | `osal.h` | Header | OS abstraction |
| 11 | `osal.c` | Source | OS abstraction impl |
| 12 | `statable_all.h` | Header | Super include |
| 13 | `{project}_run.c` | Source | Super loop |

**Count**: 13 files.

### 5.2 Folder Structure Contract

| Structure | Rule |
|-----------|------|
| `flat` | All files in one directory |
| `by_type` | `include/` / `src/` / `common/` |
| `by_layer` | Per-layer subdirectories + common at root |

Layer-specific files (5): `statable_types.h`, `statable_transitions.h`, `statable_transitions.c`, `statable_role_functions.h`, `statable_role_functions.c`.

### 5.3 Marker Contract (User Code Preservation)

| Marker | Purpose | Merge Behavior |
|--------|---------|---------------|
| `[[STABLE_USER_CODE_START]]` / `_END` | File-level user code | Inserted after last `#include` |
| `[[STABLE_USER_CODE_START:<name>]]` / `_END:<name>` | Function-level user code | Replace block; no insertion if absent |
| `[[STABLE_USER_CODE_TAIL_START]]` / `_END` | File-tail user code | Replace block |
| `[[STABLE_AUTO_GENERATED_START]]` / `_END` | Auto-generated region | Regenerated always |
| `[[STABLE_USER_INCLUDES_START]]` / `_END` | Super-include user region | Preserved |

### 5.4 ISR Contract (Stage 3)

Each generated ISR:

1. Contains `SystemContext_t *ctx = &g_ctx;` (auto-inserted).
2. Contains `(void)ctx;` to suppress unused warnings.
3. Actions converted: `Driver.Init` → `RoleFunc_Driver_Init(NULL, ctx)`.
4. Has `used_role_functions` / `used_variables` auto-extracted and written back to the model.
5. Includes user markers `<name> = PascalCase(handler.name)`.

### 5.5 Stage 4 Namespace Contract

`_normalize_func_ref` accepts:

| Input | Normalized |
|-------|-----------|
| `Driver.Init` | `Driver.Init` |
| `Driver.Init(arg1)` | `Driver.Init` |
| `RoleFunc_Driver_Init` | `Driver.Init` (if layer_name matches) |
| `Init` | `Init` |

---

## 6. GUI Contracts

### 6.1 Screen Entry

| Trigger | Opens | Modal? |
|---------|-------|--------|
| Toolbar / menu | 15 dialogs | Yes |
| Cell double-click | `ActionEditorDialog` | Yes |
| Cell Enter/F2 | `ActionEditorDialog` | Yes |
| SettingsPanel entry/exit/do double-click | `ActionEditDialog` | Yes |

### 6.2 State Transition Diagram (MermaidWidget)

| Item | Value |
|------|-------|
| Generator | `statable/mermaid_gen.py` |
| Renderer | Mermaid.js (`mermaidwin.js`) |
| Format | `stateDiagram-v2` |
| Environment override | `STATABLE_DISABLE_MERMAID=1` → placeholder `QLabel` |
| Fallback | `QPlainTextEdit` if WebEngine unavailable |

### 6.3 SettingsPanel Contract (v2.2)

| Tab | Columns |
|-----|---------|
| `State list` | Name, Description, entry function, exit function, do function, Type |
| `Role function` | Title, Function name, Namespace, Description, Return type, Arg 1 type, Arg 1 name, Arg 2 type, Arg 2 name |

**Data type**: `State.entry` and `State.exit` are `List[str]` (v2.2). UI represents them as `"; "`-joined strings. Parsing uses `_display_to_list`.

### 6.4 Modal Behavior

**All dialogs are modal.** No modeless dialog is used. This affects: user cannot interact with the main window while a dialog is open.

---

## 7. Known Constraints (Comprehensive)

This is the **most audit-relevant section**. All items have been verified against source.

| # | Item | Status | Location | Impact |
|---|------|--------|----------|--------|
| C-01 | `generation_style` / `table_type` GUI switch | **Not available** (forced to `table_driven` / `array`) | `code_generation_settings_dialog.py` | Settings UI shows fixed labels |
| C-02 | `switch_case` generation | **Not implemented** → fallback to `table_driven` | `transition_generator.py` | Warning logged |
| C-03 | `switch` table type | **Not implemented** → fallback to `array` | `transition_generator.py` | Warning logged |
| C-04 | `dictionary` table type | **Not implemented** → fallback to `array` | `transition_generator.py` | Warning logged |
| C-05 | `external_includes_in_role` | **Not implemented** | `c_code_generator.py` | Config flag has no effect |
| C-06 | `external_includes_in_transitions` | **Not implemented** | Same | Same |
| C-07 | `external_includes_in_common` | **Not implemented** | Same | Same |
| C-08 | FreeRTOS OSAL | **Include only** | `osal_generator.py` | No function bodies |
| C-09 | ThreadX OSAL | **Include only** | Same | Same |
| C-10 | `super_include_dir` in project XML | **Not persisted** | `xml_io.py` / `main_window.py` | Resets to `"common"` |
| C-11 | Role function uniqueness inconsistency | **Design asymmetry** | `statable` vs `libcntrl` | Same-name cross-namespace collision |
| C-12 | Empty `Transition.event` in `transition_to_flow_item` | **Bug** | `transition_editor_direct/draft.py` | Becomes `"NewEvent"` |
| C-13 | `palette_widget._add_function` import | **No fallback** | `palette_widget.py` | `ImportError` in some environments |
| C-14 | `project_dir_name` | **Reserved, unused** | `config.py` | No effect |
| C-15 | `flow_widget.py` / `edit_dialogs.py` | **Legacy** | `transition_editor_direct/` | Dead code, not referenced |
| C-16 | External includes path | **Basename only** | `code_generation_settings_dialog.py` | Directory part lost |
| C-17 | `TransitionContext_t` (common) vs `TransitionContext_<Layer>_t` | **Both emitted** | `struct_generator.py` | Two types with same layout |
| C-18 | Multi-layer `by_type` | **Merged into one file** | `c_code_generator.py` | Layer separation not visible |
| C-19 | Missing `\n` in output directory warning | **Cosmetic bug** | `main_window.py` | Message reads "settingsPlease specify" |
| C-20 | `flow_item_to_transition` title handling | **Edge case** | `draft.py` | `edited_text == name` → title becomes `"(無題遷移)"` |

---

## 8. Unimplemented Features

| # | Feature | Declared in | Expected Behavior |
|---|---------|-------------|-------------------|
| U-01 | `switch_case` process style | `CodeGenerationConfig.generation_style` | Fallback to `table_driven` + warning |
| U-02 | `switch` table type | `CodeGenerationConfig.table_type` | Fallback to `array` + warning |
| U-03 | `dictionary` table type | Same | Same |
| U-04 | Role-function-specific external includes | `external_includes_in_role` | No include emitted |
| U-05 | Transitions-specific external includes | `external_includes_in_transitions` | No include emitted |
| U-06 | Common-specific external includes | `external_includes_in_common` | No include emitted |
| U-07 | FreeRTOS OSAL function bodies | `osal_generator.py` | Only `#include "FreeRTOS.h"` etc. |
| U-08 | ThreadX OSAL function bodies | Same | Only `#include "tx_api.h"` |
| U-09 | `parser.py` (Excel/CSV/JSON input) | `statable/parser.py` | Stub only |
| U-10 | `super_include_dir` project persistence | `xml_io.py` | Not saved |

---

## 9. Verification and CI

### 9.1 CI Jobs

| Job | Purpose | Tool |
|-----|---------|------|
| `no-japanese` | Non-ASCII detection | `tools/find_all_japanese.py` |
| `syntax` | Python syntax | `python -m compileall` |
| `tests` | 12 test suites | `python tests/test_v2_2_p*.py` |
| `generated-code` | C code generation check | `tools/verify_generated_code.py` |

### 9.2 CI Environment

| Variable | Value | Purpose |
|----------|-------|---------|
| `QT_QPA_PLATFORM` | `offscreen` | Headless GUI |
| `STATABLE_DISABLE_MERMAID` | `1` | Skip WebEngine |
| `PYTHONIOENCODING` | `utf-8` | Prevent encoding issues |

### 9.3 Qt System Libraries (CI)

```
libegl1 libgl1 libglib2.0-0 libdbus-1-3
libxkbcommon0 libxkbcommon-x11-0
libxcb-icccm4 libxcb-image0 libxcb-keysyms1
libxcb-randr0 libxcb-render-util0 libxcb-shape0
libxcb-xinerama0 libxcb-xfixes0 libxcb-cursor0
libfontconfig1 libfreetype6
```

### 9.4 Verification Coverage

| Area | Verified by | Coverage |
|------|------------|---------|
| Data model | `test_v2_2_p1`, `p2` | High |
| GUI helpers | `test_v2_2_p3` | Medium |
| Code generation | `test_v2_2_p4a`, `p4b` | High |
| Stage features | `test_v2_2_p12_*` | High |
| C code correctness | `verify_generated_code.py` | Structural only |

### 9.5 Verification Gaps (Audit Finding)

| Gap | Impact |
|-----|--------|
| No compile test of generated C code in CI | Type errors not caught |
| No test for `super_include_dir` persistence | Regression undetected |
| No test for role function collision across namespaces | Data loss undetected |
| No test for empty-event `transition_to_flow_item` | Bug remains |
| Legacy `flow_widget.py` / `edit_dialogs.py` untested | Dead code drift |

---

## 10. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|-----------|
| R-01 | Cross-namespace role function collision | Medium | Data loss in `StateMachine.role_functions` | Use `qualified_name` as key (requires change) |
| R-02 | `super_include_dir` reset on reload | High | User settings lost | Persist in XML |
| R-03 | Empty-event transition conversion to `"NewEvent"` | Medium | Incorrect transition title | Fix `transition_to_flow_item` |
| R-04 | Generated C code compile errors undetected | Medium | Broken output ships | Add `arm-none-eabi-gcc -fsyntax-only` to CI |
| R-05 | Legacy code drift | Low | Maintenance confusion | Remove `flow_widget.py` / `edit_dialogs.py` or mark deprecated |
| R-06 | `palette_widget._add_function` import failure | Low | Silent failure in some envs | Add try/except with fallback |
| R-07 | Windows / Linux path divergence | Low | Silent failures | Add path tests to CI |
| R-08 | User code marker overwrite | Low | Loss of user edits | Add merge tests covering corner cases |

---

## 11. Handover Checklist

| # | Item | Verification | Status |
|---|------|-------------|--------|
| 1 | CI passes on `main` | GitHub Actions | ✅ |
| 2 | All 4 specification files present | `docs/` | ✅ |
| 3 | Known constraints reviewed (§7) | This document | – |
| 4 | Unimplemented features accepted (§8) | This document | – |
| 5 | Risk register reviewed (§10) | This document | – |
| 6 | Sample generation works | `SampleDataGenerator` | – |
| 7 | Project XML round-trip works | `project_to_xml` / `project_from_xml` | – |
| 8 | Generated C code verified | `tools/verify_generated_code.py` | – |
| 9 | Test suites run locally | `python tests/test_v2_2_p*.py` | – |
| 10 | Dependencies documented | This document §2.3 | – |
| 11 | UI is English-only | `main_window.py` labels | ✅ |
| 12 | CI workflow at repository root | `.github/workflows/check.yml` | ✅ |

---

## 12. Revision History

| Version | Date | Content |
|---------|------|---------|
| 1.0 | 2026-09-20 | Consolidated audit specification from all existing specs |