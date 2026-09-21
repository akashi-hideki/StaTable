# StaTable Code Generation Module Specification v3.0 (English)

Version: 3.0
Date: 2026-09-20
Scope: `code/codegen/` — 16 modules
Source basis: all uploaded files in `codegen/`
Prerequisite: `statable/` data model (see `SPEC_OVERVIEW_en.md` §3)

Prior v2.0 → v3.0 changes:
- File count 11 → **13** (`statable_all.h`, `{project}_run.c` added)
- Super-include / super-loop implemented
- Stage 3: ISR context support (`ctx` auto-insertion)
- Stage 4: Namespace.Name support in transitions / actions / ISR
- `RoleFunctionGenerator` rewritten with NULL guard, call_sites, `Transition_GetId`
- `struct_generator` gains common `TransitionContext_t` and `pending_event`

---

## Table of Contents

1. Overview
2. Module Composition
3. Data Specifications
4. API Specifications
5. Configuration Defaults
6. Processing Flows
7. Marker Specification
8. Naming Conventions
9. Generated File Layout
10. Errors and Warnings
11. Known Constraints
12. Revision History

---

## 1. Overview

### 1.1 Purpose

Generate C-language state machine code from `StateMachine` + `GlobalDefinitions`. Emit **13 files** and realize:

- User-editable region preservation via marker-based merging
- Three output layouts via `folder_structure` (`flat` / `by_type` / `by_layer`)
- Multi-layer state machines (tab = layer)
- Super-include (`statable_all.h`) and super-loop (`{project}_run.c`)
- ISR-callable role functions (Stage 3)
- Layer-agnostic role functions: do not depend on the calling layer (see SPEC_OVERVIEW §3.2.7)
- `Namespace.Name` accepted in conditions / actions (Stage 4)

### 1.2 Scope

| Category | Content |
|----------|---------|
| In scope | All 16 modules in `codegen/`, GUI integration, shared library coupling |
| Out of scope | Tests, `statable/` internals, `transition_editor_direct/` UI detail |

### 1.3 Terminology

| Term | Definition |
|------|------------|
| Layer | A state-machine group identified by tab name (`sm.layer_name`) |
| Cell | A (state, event) pair. Minimal unit of a transition function |
| Cell function | `t_<State>_<Event>` when `SHORT_CELL_NAMES=True` |
| Role function | `RoleFunc_<Namespace>_<PascalName>` |
| call_sites | Per-role-function list of calling cells |
| transition_id | Index into call_sites; `0xFFFF` = no match |
| Super include | `statable_all.h` aggregating all generated headers |
| Super loop | `{project}_run.c` providing the main loop for all layers |
| Namespace | Owning layer or explicit namespace (`Driver` in `Driver.Init`) |

---

## 2. Module Composition

| # | Module | Main Class | Responsibility |
|---|--------|-----------|----------------|
| 1 | `c_code_generator.py` | `CCodeGenerator` | Orchestration. Step tables, dispatch, folder resolution, save |
| 2 | `code_merger.py` | `CodeMerger` | Merge generated with existing code |
| 3 | `code_templates.py` | `CodeTemplates` | Fixed strings / templates (incl. `ISR_TEMPLATES`) |
| 4 | `transition_generator.py` | `TransitionGenerator` | Cell functions, transition table, Process function |
| 5 | `role_function_generator.py` | `RoleFunctionGenerator` / `RoleFuncCallSite` | Role function decls / impls, call_sites, `Transition_GetId` |
| 6 | `struct_generator.py` | `CStructGenerator` | SystemData / EventFlags / SystemContext / TransitionContext |
| 7 | `enum_generator.py` | `CEnumGenerator` | STATE / EVENT / FLAG enums |
| 8 | `variable_generator.py` | `VariableGenerator` | Variable macros, `SystemContext_Init` (incl. pending_event) |
| 9 | `event_queue_generator.py` | `EventQueueGenerator` | Queue struct, Enqueue / Dequeue |
| 10 | `interrupt_generator.py` | `InterruptGenerator` | ISR generation (Stage 3: ctx pointer, NULL safety, marker) |
| 11 | `timer_generator.py` | `TimerGenerator` | Timer struct, Init / Update |
| 12 | `osal_generator.py` | `OSALGenerator` | OSAL header / source (non_rtos impl, freertos/threadx include only) |
| 13 | `type_mapper.py` | `CTypeMapper` | Type mapping |
| 14 | `naming_convention.py` | `CNamingConvention` | Name conversion |
| 15 | `config.py` | `CodeGenerationConfig` / `ConfigManager` | Config dataclass and manager |
| 16 | `sample_data.py` | `SampleDataGenerator` | Test / demo sample data |

---

## 3. Data Specifications

### 3.1 `CodeGenerationConfig` (`config.py`)

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `generation_style` | str | `"table_driven"` | GUI forces this |
| `table_type` | str | `"array"` | GUI forces this |
| `os_type` | str | `"non_rtos"` | `non_rtos` / `freertos` / `threadx` |
| `naming_prefix` | str | `""` | |
| `state_prefix` | str | `"STATE"` | |
| `event_prefix` | str | `"EVENT"` | |
| `flag_prefix` | str | `"FLAG"` | |
| `enable_debug_logs` | bool | `True` | |
| `enable_info_logs` | bool | `True` | |
| `enable_error_logs` | bool | `True` | |
| `enable_comments` | bool | `True` | |
| `enable_doxygen` | bool | `True` | |
| `enable_user_markers` | bool | `True` | |
| `output_directory` | str | `""` | |
| `save_with_merge` | bool | `True` | |
| `project_name` | str | `"MyProject"` | Used for `{project}_run.c` |
| `folder_structure` | str | `"by_type"` | `flat` / `by_layer` / `by_type` |
| `include_dir_name` | str | `"include"` | |
| `source_dir_name` | str | `"src"` | |
| `common_dir_name` | str | `"common"` | |
| `project_dir_name` | str | `"project"` | Reserved, unused |
| `generate_super_include` | bool | `True` | |
| `super_include_file` | str | `"statable_all.h"` | |
| `super_include_dir` | str | `"common"` | For by_type. **Not persisted in project XML** |
| `external_includes` | List[str] | `[]` | GUI registers basename only |
| `external_includes_in_super` | bool | `True` | |
| `external_includes_in_role` | bool | `True` | **Not implemented** |
| `external_includes_in_transitions` | bool | `False` | **Not implemented** |
| `external_includes_in_common` | bool | `False` | **Not implemented** |
| `max_consecutive_pending_events` | int | `16` | Matches macro default |

**Methods**

- `to_dict() -> Dict` — all fields
- `from_dict(data: Dict) -> CodeGenerationConfig` — unknown keys ignored

### 3.2 `ConfigManager`

| Method | Return | Description |
|--------|--------|-------------|
| `get_config()` | `CodeGenerationConfig` | Current config |
| `set_config(config)` | – | Replace |
| `update(**kwargs)` | – | `hasattr` check + `setattr` |
| `reset()` | – | Reset to defaults |
| `get_available_styles()` | `Dict[str, str]` | `table_driven` / `switch_case` |
| `get_available_table_types()` | `Dict[str, str]` | `array` / `switch` / `dictionary` |
| `get_available_os_types()` | `Dict[str, str]` | `non_rtos` / `freertos` / `threadx` |
| `get_available_folder_structures()` | `Dict[str, str]` | `flat` / `by_layer` / `by_type` |

### 3.3 `RoleFuncCallSite` (`role_function_generator.py`)

```python
class RoleFuncCallSite:
    __slots__ = ('func_name', 'kind', 'from_state', 'event', 'target')
    def __init__(self, func_name, kind, from_state, event, target): ...
    def key(self) -> tuple:   # (from_state, event)
    def __repr__(self) -> str
```

`kind` ∈ `'condition'` / `'pre_action'` / `'else_action'`.

### 3.4 `InterruptAction` / `InterruptHandlerDef` (`statable.global_defs`)

```python
@dataclass
class InterruptAction:
    condition: str = ""
    action: str = ""

@dataclass
class InterruptHandlerDef:
    name: str
    description: str = ""
    event_names: List[str] = field(default_factory=list)
    is_timer: bool = False
    actions: List[InterruptAction] = field(default_factory=list)
    title: str = ""
    used_role_functions: List[str] = field(default_factory=list)
    used_variables: List[str] = field(default_factory=list)
```

XML round-trip via `<UsedRoleFunction ref="..."/>` / `<UsedVariable name="..."/>`.
Written back via `update_handler_symbols` (called from `_step_interrupts`).

### 3.5 File Metadata (`CCodeGenerator.file_generators`)

| # | File | description | guard_name | by_type category |
|---|------|-------------|-----------|------------------|
| 1 | `statable_types.h` | State machine type definitions | `STATABLE_TYPES_H` | include |
| 2 | `statable_transitions.h` | Transition function declarations | `STATABLE_TRANSITIONS_H` | include |
| 3 | `statable_transitions.c` | Transition logic | `None` | src |
| 4 | `statable_role_functions.h` | Role function declarations | `STATABLE_ROLE_FUNCTIONS_H` | include |
| 5 | `statable_role_functions.c` | Role function implementations | `None` | src |
| 6 | `statable_init.c` | Initialization | `None` | src |
| 7 | `statable_event_queue.c` | Event queue implementation | `None` | src |
| 8 | `statable_interrupt.c` | ISRs | `None` | src |
| 9 | `statable_timer.c` | Timer handling | `None` | src |
| 10 | `osal.h` | OSAL header | `OSAL_H` | common |
| 11 | `osal.c` | OSAL source | `None` | common |
| 12 | `statable_all.h` | Super include | `STATABLE_ALL_H` | (dedicated resolution) |
| 13 | `{project}_run.c` | Super loop | `None` | src |

> File 12 is **not** in `FILE_CATEGORY`; resolved by `_resolve_super_include_path`.
> File 13 is registered dynamically in `__init__`.

### 3.6 Include Definitions (`CCodeGenerator.include_headers`)

| Key | Content |
|-----|---------|
| `types` | `<stdint.h>` `<stdbool.h>` `<string.h>` |
| `transitions_h` | `"statable_types.h"` |
| `transitions_c` | `"statable_transitions.h"` `"statable_role_functions.h"` |
| `role_functions_h` | `"statable_types.h"` |
| `role_functions_c` | `"statable_role_functions.h"` |
| `init_c` | `"statable_types.h"` |
| `event_queue_c` | `"statable_types.h"` |
| `interrupt_c` | `"statable_types.h"` + `"statable_all.h"` (Stage 3) |
| `timer_c` | `"statable_types.h"` |

---

## 4. API Specifications

### 4.1 `CCodeGenerator`

#### Class Constant Tables

| Table | Type | Purpose |
|-------|------|---------|
| `FILE_STEPS` | `Dict[str, List[Dict]]` | Per-file step definitions (super_loop added dynamically) |
| `STRUCT_KIND_DISPATCH` | `Dict[str, str]` | `system_data` / `event_flags` / `system_context` |
| `FILE_DISPATCH` | `Dict[str, str]` | File name → generation method |
| `FILE_CATEGORY` | `Dict[str, str]` | (File 12 not included) |
| `FOLDER_STRUCTURE_RESOLVERS` | `Dict[str, str]` | `flat` / `by_type` / `by_layer` |
| `LAYER_SPECIFIC_FILES` | set | 5 layer-specific files for by_layer |
| `COMMON_FILES` | set | 7 common files for by_layer |

**`LAYER_SPECIFIC_FILES`**: `statable_types.h`, `statable_transitions.h`, `statable_transitions.c`, `statable_role_functions.h`, `statable_role_functions.c`

**`COMMON_FILES`**: `statable_init.c`, `statable_event_queue.c`, `statable_interrupt.c`, `statable_timer.c`, `osal.h`, `osal.c`, `statable_all.h`

#### Public Methods

| Method | Description |
|--------|-------------|
| `__init__(config=None)` | Build sub-generators; register super_loop dynamically |
| `get_config()` / `set_config()` / `update_config()` / `reset_config()` | Config |
| `generate_all(sm, gd, role_function_library=None)` | Single-layer, all 13 files |
| `generate_file(filename, sm, gd, ...)` | Single file |
| `generate_all_layers(layers, gd, ...)` | Multi-layer; `by_layer` → `_generate_all_by_layer` |
| `save_generated_code(files, output_dir, layer_name='')` | Save with folder resolution |
| `save_generated_code_with_merge(files, output_dir, layer_name='')` | Save with merge |
| `get_merge_summary(files, output_dir, layer_name='')` | Merge summary |
| `get_generated_file_list()` | File names |

#### Folder Resolution

| Method | Behavior |
|--------|----------|
| `_resolve_output_path(filename, layer_name)` | If filename contains path separator → early return. `statable_all.h` handled specially |
| `_resolve_super_include_path(layer_name)` | `flat` → filename / `by_type` → `super_include_dir/` / `by_layer` → layer folder or root |
| `_resolve_path_flat` | As-is |
| `_resolve_path_by_type` | Per `FILE_CATEGORY` into `include/` `src/` `common/` |
| `_resolve_path_by_layer` | Only layer-specific files get `{layer}/` prefix |

#### Multi-Layer

| Method | Description |
|--------|-------------|
| `_normalize_layers(layers)` | Normalize to `[(name, sm)]`, sort by `layer_priority` ascending |
| `_setup_layer_generators(sm)` | Propagate layer name to `enum_gen` / `transition_gen` / `role_func_gen` / `struct_gen` / `interrupt_gen` |
| `_generate_all_by_layer(layers, gd, lib)` | Layer files keyed `"layer/filename"`; common files normal keys |

#### Step Execution

`_run_steps(filename, sm, gd)` / `_run_steps_multi(filename, layers, gd)` run steps in order.
Context dict:
```
{layers, state_machine, global_defs, file_config, filename, config, is_multi}
```

#### Step Executor Overview

| Action | Method | Notes |
|--------|--------|-------|
| `file_header` / `blank` / `guard_start/end` / `include_section` / `section_header` | `_step_*` | Common |
| `enums` / `custom_types` / `struct` / `var_macros` | `_step_*` | Concatenate across layers |
| `state_machine_decl` / `cell_prototypes` / `transition_table` / `cell_functions` / `process_func` | `_step_*` | Per-layer, concatenated |
| `role_decls` / `role_impls` | `_step_*` | Per-layer |
| `init_func` / `event_queues` | `_step_*` | |
| `interrupts` | `_step_interrupts` | Calls `update_handler_symbols` |
| `timer_struct` / `timer_init` / `timer_update` | `_step_*` | |
| `osal_header` / `osal_source` | `_step_*` | |
| `super_include_*` (10 actions) | `_step_*` | Layer includes, extern vars / funcs |
| `super_loop_*` (6 actions) | `_step_*` | Layer state vars, Init / Run blocks |

### 4.2 `CodeMerger`

#### Marker Constants (`MARKERS`)

| Key | Value |
|-----|-------|
| `file_user_start/end` | `/* [[STABLE_USER_CODE_START]] */` / `_END` |
| `func_user_start/end` | `/* [[STABLE_USER_CODE_START:{func_name}]] */` / `_END:{func_name}` |
| `auto_start/end` | `/* [[STABLE_AUTO_GENERATED_START]] */` / `_END` |
| `file_tail_user_start/end` | `/* [[STABLE_USER_CODE_TAIL_START]] */` / `_END` |

#### Function Name Patterns

```python
FUNC_NAME_PATTERNS = [
    r'RoleFunc_(\w+)\s*\(',   # RoleFunc_Driver_Init -> 'Driver_Init'
    r'ISR_(\w+)\s*\(',        # ISR_TIMER0           -> 'TIMER0'
]
```

#### Public Methods

| Method | Description |
|--------|-------------|
| `extract_file_user_code(content)` | File-level user code |
| `extract_func_user_code(content, func_name)` | Function-level user code |
| `extract_all_func_user_codes(content)` | All (RoleFunc_ / ISR_) |
| `extract_file_tail_user_code(content)` | File-tail user code |
| `inject_file_user_code(content, user_code)` | Insert after last `#include`, else top |
| `inject_func_user_code(content, func_name, user_code)` | Replace existing marker block; no insertion |
| `inject_file_tail_user_code(content, user_code)` | Replace tail marker block |
| `merge_file(generated, existing)` | Combine above for one file |
| `merge_all_files(files, existing_dir, path_resolver=None, layer_name='')` | Folder-aware merge |
| `has_user_code(content)` / `has_func_user_code(content, name)` | Presence check |
| `get_user_code_summary(content)` | Summary dict |

### 4.3 `RoleFunctionGenerator`

#### Class Constant Tables (8)

`DECLARATION_TEMPLATES`, `IMPLEMENTATION_TEMPLATES`, `NONE_DEFINE_TEMPLATES`,
`ENTRY_STRUCT_TEMPLATES`, `TRANSITION_ID_FUNC_TEMPLATES`,
`CALL_SITE_TABLE_TEMPLATES`, `CALL_SITES_COMMENT_TEMPLATES`,
`TAIL_USER_SECTION_TEMPLATES`

#### Public Methods

| Method | Description |
|--------|-------------|
| `set_layer(name)` | Set layer name |
| `generate_all_declarations(funcs)` | All decls (dedup by `namespace.name`) |
| `generate_all_implementations(funcs, sm=None, gd=None)` | Main; 7-stage output when `sm` provided |
| `generate_none_define()` | `TRANSITION_ID_NONE` define |
| `generate_entry_struct()` | `RoleFuncCallSiteEntry_<Layer>_t` |
| `generate_transition_id_prototype()` | `Transition_GetId` forward decl |
| `generate_transition_id_function()` | `Transition_GetId` body |
| `generate_call_sites_table(func, call_sites)` | call_sites table for one function |
| `generate_declaration(func)` / `generate_implementation(...)` | Individual |
| `generate_call(func_name)` | `RoleFunc_XX_Name(transition, ctx)` |
| `generate_tail_user_section()` | File tail user section |

#### Stage 4: Namespace.Name support

| Method | Change |
|--------|--------|
| `_normalize_func_ref(ref)` | Keep dot form; `RoleFunc_Driver_Init` → `Driver.Init`; strip args |
| `_extract_func_names_from_condition(cond)` | Detect dot form, `RoleFunc_XXX`, `func(...)`, bare PascalCase identifier |
| `_get_call_sites_for_func(func, call_map)` | Try `qualified_name`, fall back to `name` |
| `_dedupe_by_name(funcs)` | Dedup by `namespace.name` |

#### NULL Guard Expansion

`generate_implementation` always emits:

```c
/* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
STATE_<Layer>_t from_state = STATE_<Layer>_MAX;
EVENT_<Layer>_t event      = EVENT_<Layer>_NONE;
if (transition != NULL) {
    from_state = transition->from_state;
    event      = transition->event;
}
(void)from_state;   /* 未使用警告抑制 */
(void)event;
```

Then `transition_id` local, `ctx->data` local pointer, `int ret = 0;`, user markers.

#### `Transition_GetId` body

```c
static uint16_t Transition_GetId(
    const TransitionContext_<Layer>_t *transition,
    const RoleFuncCallSiteEntry_<Layer>_t *table,
    uint16_t table_size)
{
    if (transition == NULL || table == NULL) return TRANSITION_ID_NONE;
    for (uint16_t i = 0; i < table_size; i++) {
        if (table[i].from_state == transition->from_state &&
            table[i].event      == transition->event) return i;
    }
    return TRANSITION_ID_NONE;
}
```

### 4.4 `TransitionGenerator`

#### Class Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `SHORT_CELL_NAMES` | `True` | `t_<State>_<Event>` short name |
| `TABLE_MIN_COL_WIDTH` | `14` | Table column width |
| `DEFAULT_TABLE_TYPE` | `'array'` | |
| `DEFAULT_GENERATION_STYLE` | `'table_driven'` | |

#### Template Tables (6)

`CELL_TEMPLATES`, `CELL_PROTO_TEMPLATES`, `TABLE_TEMPLATES`,
`TABLE_HEADER_TEMPLATES`, `DICT_TEMPLATES`, `PROCESS_TEMPLATES`,
`GET_NEXT_TEMPLATES`

#### Dispatch

```python
self.table_generators = {
    'array':      self._generate_table_array,
    'switch':     self._generate_table_switch,     # Not implemented → array
    'dictionary': self._generate_table_dictionary, # Not implemented → array
}
self.process_generators = {
    'table_driven': self._generate_process_table_driven,
    'switch_case':  self._generate_process_switch_case,  # Not implemented → table_driven
}
```

#### Public Methods

| Method | Description |
|--------|-------------|
| `set_layer(name)` | Set layer name |
| `generate_transition_cell_prototypes(sm)` | Cell function forward decls |
| `generate_transition_cell_functions(sm)` | Cell function bodies |
| `generate_transition_table(sm, table_type=None)` | Transition table (dispatch) |
| `generate_transition_table_header(sm)` | `extern` declaration |
| `generate_function_dictionary(sm)` | Function dictionary |
| `generate_process_function(sm, generation_style=None)` | `StateMachine_Process_<Layer>` |
| `generate_get_next_event_function(sm)` | `StateMachine_GetNextEvent_<Layer>` |
| `generate_all(sm)` | Dict of the 7 above |

### 4.5 `CStructGenerator`

#### Generated Items

| # | Method | Output |
|---|--------|--------|
| 1 | `_generate_custom_type` | User-defined type |
| 2 | `_generate_system_data` | `SystemData_t` |
| 3 | `_generate_event_flags` | `EventFlags_t` |
| 4 | `_generate_system_context` | `SystemContext_t` (with `pending_event` / `pending_event_valid`) |
| 5 | `generate_common_transition_context()` | Common `TransitionContext_t` (`uint16_t`-based) |
| 6 | `generate_layer_transition_context(state_type, event_type)` | `TransitionContext_<Layer>_t` (typed) |
| 7 | `generate_pending_event_macros()` | `FIRE_EVENT` / `MAX_CONSECUTIVE_PENDING_EVENTS` |

#### Batch

`generate_all_structs(gd)` / `generate_all(gd)` (dict of 6) / `generate_struct(kind, item)` (compat)

### 4.6 `CEnumGenerator`

| Method | Output |
|--------|--------|
| `generate_state_enum(states)` | `STATE_<Layer>_t` (no NONE, `_MAX` explicit) |
| `generate_event_enum(events)` | `EVENT_<Layer>_t` (`NONE = 0` first, `_MAX` explicit) |
| `generate_flag_enum(flags)` | `FLAG_t` (layer-independent) |
| `generate_bit_mask_enum(flags)` | `FLAG_MASK_t` (optional) |
| `generate_all_enums(states, events, flags=None)` | Concatenate 3 above |
| `generate_enum(kind, items)` | Compat |

### 4.7 `VariableGenerator`

| Method | Description |
|--------|-------------|
| `generate_init_function(gd)` | `SystemContext_Init` (incl. pending_event init) |
| `generate_all_macros(gd)` | `DATA_*` / `FLAG_*` macros |
| `generate_variable(kind, item)` | `macro` / `init` / `global` / `flag` |
| `generate_all(gd)` | Dict `init_function` / `macros` |

`INIT_FUNCTION_STEPS` has 18 steps including `pending_event_comment` / `pending_event_init`.

### 4.8 `InterruptGenerator` (Stage 3)

#### Class Constants

| Constant | Value |
|----------|-------|
| `AUTO_INSERT_CTX` | `True` |
| `CTX_VAR_NAME` | `'ctx'` |
| `G_CTX_NAME` | `'g_ctx'` |

#### Step Sequence (9)

`comment` → `signature` → `open` → `context` → `enter_log` → `actions` → `user_section` → `exit_log` → `close`

#### Name Generation

| Method | Example |
|--------|---------|
| `_get_isr_function_name` | `TIMER0` → `ISR_Timer0` |
| `_get_marker_name` | `TIMER0` → `Timer0` |
| `_get_handler_display_name` | As-is (for logs) |

#### Action Parsing

`_parse_action(text)`:

| Input | C output | used_role_functions |
|-------|----------|---------------------|
| `Driver.Init` | `RoleFunc_Driver_Init(NULL, ctx)` | `["Driver.Init"]` |
| `Init(args)` | `RoleFunc_<Layer>_Init(NULL, ctx)` | `["<Layer>.Init"]` |
| `RoleFunc_XXX(...)` | as-is | empty |
| C keyword (`if`, `return`, etc.) | as-is | empty |

`_parse_action_with_semicolon(action)` handles `if (cond) { body; }`.

#### Symbol Extraction

`extract_used_symbols(handler) -> (used_role_functions, used_variables)`
Extracts `ctx->data.X` / `ctx->flags.X` via regex.

`update_handler_symbols(handler)` writes back (called from `_step_interrupts`).

#### Public API

| Method | Description |
|--------|-------------|
| `set_layer(name)` | For legacy `identifier(args)` name generation |
| `generate_isr(handler, update_handler=False)` | Generate one ISR |
| `generate_all_isrs(gd, update_handlers=False)` | All ISRs |

#### Generated ISR Example (`UART_RX`)

```c
/**
 * @brief  UART_RX 割り込みハンドラ
 * @note   UART受信割り込み
 * @note   使用ロール関数:
 *         - Driver.Init
 */
void ISR_UartRx(void)
{
    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: UART_RX");

    /* ===== アクション（自動生成） ===== */
    if (ctx->data.battery_voltage > 3000) { RoleFunc_Driver_Init(NULL, ctx); }

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:UartRx]] */
    /* ユーザー追加コードをここに記述 */
    /* [[STABLE_USER_CODE_END:UartRx]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: UART_RX");
}
```

### 4.9 `EventQueueGenerator` / `TimerGenerator` / `OSALGenerator`

All use step-table + executor dict pattern.

- `EventQueueGenerator`: `generate_struct` / `generate_enqueue_function` / `generate_dequeue_function` / `generate_all_code(queue)` / `generate_all(gd)`
- `TimerGenerator`: `generate_struct` / `generate_init_function` / `generate_update_function` / `generate_all(gd)`
- `OSALGenerator`: `generate_header(os_type)` / `generate_source(os_type)` / `generate_all(os_type)` / `get_available_os_types()`

`OSALGenerator` fully implements **`non_rtos` only**. `freertos` / `threadx` add includes only.

### 4.10 `CTypeMapper` / `CNamingConvention`

- `CTypeMapper.map_type(sta_type)`: `uint16` → `uint16_t`, etc.
- `CTypeMapper.get_required_headers(types)`: required standard headers
- `CNamingConvention.to_pascal_case` / `to_upper_snake` / `sanitize_identifier`, etc.
- `CNamingConvention.create_identifier(name, kind)`: `variable` / `function` / `type` / `enum` / `macro`
- `CNamingConvention.create_type_name(name)`: `PascalName_t`

### 4.11 `CodeTemplates`

Key tables:

- `STRINGS` / `SECTION_HEADERS` / `STRUCT_COMMENTS` / `ENUM_COMMENTS`
- `TYPE_NAMES` / `FUNCTION_NAMES` / `MACRO_NAMES` / `FORMATS`
- `LAYER_TEMPLATES` / `COMMON_TYPES_TEMPLATES` / `TRANSITION_CELL_TEMPLATES` / `TRANSITION_TABLE_TEMPLATES`
- `PROCESS_FUNC_TEMPLATES` / `GET_NEXT_EVENT_TEMPLATES` / `ROLE_FUNC_TEMPLATES`
- `SUPER_INCLUDE_TEMPLATES` / `SUPER_LOOP_TEMPLATES`
- `ISR_TEMPLATES`
- `DEBUG_MESSAGES` / `OSAL`

### 4.12 `SampleDataGenerator`

| Method | Description |
|--------|-------------|
| `create_sample_state_machine()` | 4 states, 5 events, 6 transitions, 2 role functions |
| `create_sample_global_defs()` | 3 vars, 2 flags, 2 custom types, 1 interrupt, 2 timer groups, 1 queue |
| `get_sample_data()` | `(sm, gd)` tuple |

Module-level helpers: `get_sample_state_machine()` / `get_sample_global_defs()` / `get_sample_data()`.

---

## 5. Configuration Defaults

| Setting | Default | Notes |
|---------|---------|-------|
| `folder_structure` | `"by_type"` | GUI switchable |
| `generate_super_include` | `True` | |
| `super_include_file` | `"statable_all.h"` | |
| `super_include_dir` | `"common"` | For by_type |
| `os_type` | `"non_rtos"` | |
| `project_name` | `"MyProject"` | `{project}_run.c` |
| `save_with_merge` | `True` | |
| `generation_style` | `"table_driven"` | GUI forced |
| `table_type` | `"array"` | GUI forced |

---

## 6. Processing Flows

### 6.1 Single-Layer (`generate_all`)

```
generate_all(sm, gd, lib)
 ├─ _setup_layer_generators(sm)
 ├─ _current_role_function_library = lib （try/finally）
 ├─ for each filename in file_generators:
 │   ├─ statable_all.h && !generate_super_include → skip
 │   ├─ method = FILE_DISPATCH[filename]
 │   └─ _run_steps(filename, sm, gd) → _run_steps_multi
 └─ return Dict[filename, content]
```

### 6.2 Multi-Layer (`generate_all_layers`)

```
_normalize_layers(layers)  # [(name, sm)], priority ascending
 ├─ folder_structure == 'by_layer'
 │   └─ _generate_all_by_layer()
 │       ├─ LAYER_SPECIFIC_FILES → "layer/filename" keys
 │       └─ COMMON_FILES + super_loop → normal keys (_run_steps_multi)
 └─ else (flat / by_type)
     └─ all files via _run_steps_multi
```

### 6.3 Save

```
save_generated_code(files, output_dir, layer_name='')
 ├─ os.makedirs(output_dir, exist_ok=True)
 └─ for filename, content:
     ├─ rel_path = _resolve_output_path(filename, layer_name)
     │   ├─ contains path separator → as-is
     │   ├─ statable_all.h → _resolve_super_include_path
     │   └─ FOLDER_STRUCTURE_RESOLVERS[structure]
     ├─ os.makedirs(parent, exist_ok=True)
     └─ open(..., 'w').write(content)

save_generated_code_with_merge(...)
 ├─ merger.merge_all_files(files, output_dir,
 │                          path_resolver=self._resolve_output_path,
 │                          layer_name=layer_name)
 └─ save_generated_code(merged, output_dir, layer_name)
```

---

## 7. Marker Specification

### 7.1 Marker List

| Kind | Marker |
|------|--------|
| File user code | `[[STABLE_USER_CODE_START]]` / `[[STABLE_USER_CODE_END]]` |
| Function user code | `[[STABLE_USER_CODE_START:<name>]]` / `[[STABLE_USER_CODE_END:<name>]]` |
| File tail user code | `[[STABLE_USER_CODE_TAIL_START]]` / `[[STABLE_USER_CODE_TAIL_END]]` |
| Auto-generated region | `[[STABLE_AUTO_GENERATED_START]]` / `[[STABLE_AUTO_GENERATED_END]]` |
| Super include user region | `[[STABLE_USER_INCLUDES_START]]` / `[[STABLE_USER_INCLUDES_END]]` |

### 7.2 Function Marker `<name>`

| Origin | `<name>` example |
|--------|------------------|
| Role function (with layer) | `Driver_Init` |
| Role function (no layer) | `Init` |
| ISR | `Timer0` (PascalCase of `handler.name`) |

### 7.3 Extraction Patterns

| Pattern | Target |
|---------|--------|
| `RoleFunc_(\w+)\s*\(` | Role functions |
| `ISR_(\w+)\s*\(` | ISRs |

---

## 8. Naming Conventions

### 8.1 Types

| Target | Naming |
|--------|--------|
| State type | `STATE_<Layer>_t` (`STATE_t` without layer) |
| Event type | `EVENT_<Layer>_t` |
| Flag type | `FLAG_t` (common) |
| Common transition context | `TransitionContext_t` |
| Layer transition context | `TransitionContext_<Layer>_t` |
| Transition function pointer | `TransitionFunc_<Layer>_t` |
| call_sites entry | `RoleFuncCallSiteEntry_<Layer>_t` |
| Custom type | `<PascalName>_t` (`create_type_name`) |

### 8.2 Values

| Target | Naming |
|--------|--------|
| State value | `STATE_<Layer>_<Pascal>` |
| Event value | `EVENT_<Layer>_<UPPER_SNAKE>` |
| Event NONE | `EVENT_<Layer>_NONE` (= 0) |
| MAX | `STATE_<Layer>_MAX` / `EVENT_<Layer>_MAX` |
| Flag | `FLAG_<UPPER_SNAKE>` |

### 8.3 Functions

| Target | Naming |
|--------|--------|
| Cell function | `t_<State>_<Event>` (`static`) |
| Process | `StateMachine_Process_<Layer>` |
| GetNextEvent | `StateMachine_GetNextEvent_<Layer>` |
| Role function | `RoleFunc_<Namespace>_<PascalName>` |
| Transition ID | `Transition_GetId` (`static`) |
| ISR | `ISR_<Pascal(handler.name)>` |
| Init | `SystemContext_Init` |
| Super loop | `{project_name}_Init` / `{project_name}_Run` |

### 8.4 Globals

| Target | Naming |
|--------|--------|
| Context | `g_ctx` |
| Layer state | `g_<Layer>_state` (`g_state` without layer) |
| Transition table | `transition_table_<Layer>` (`transition_matrix` without layer) |
| call_sites table | `call_sites_<Short>` |
| Count macro | `CALL_SITES_<Short>_COUNT` |

### 8.5 Macros

| Macro | Value |
|-------|-------|
| `TRANSITION_ID_NONE` | `((uint16_t)0xFFFF)` |
| `FIRE_EVENT(ctx, evt)` | `do { (ctx)->pending_event = (uint16_t)(evt); (ctx)->pending_event_valid = true; } while(0)` |
| `MAX_CONSECUTIVE_PENDING_EVENTS` | `16` (overridable) |
| `DATA_<VAR>(ctx)` | `((ctx)->data.<var>)` |
| `FLAG_<FLAG>(ctx)` | `((ctx)->flags.<flag>)` |

---

## 9. Generated File Layout

### 9.1 `flat`

```
<output_dir>/
├── statable_types.h
├── statable_transitions.h
├── statable_transitions.c
├── statable_role_functions.h
├── statable_role_functions.c
├── statable_init.c
├── statable_event_queue.c
├── statable_interrupt.c
├── statable_timer.c
├── osal.h
├── osal.c
├── statable_all.h
└── {project}_run.c
```

### 9.2 `by_type` (default)

```
<output_dir>/
├── include/
│   ├── statable_types.h
│   ├── statable_transitions.h
│   └── statable_role_functions.h
├── src/
│   ├── statable_transitions.c
│   ├── statable_role_functions.c
│   ├── statable_init.c
│   ├── statable_event_queue.c
│   ├── statable_interrupt.c
│   ├── statable_timer.c
│   └── {project}_run.c
└── common/
    ├── osal.h
    ├── osal.c
    └── statable_all.h
```

`statable_all.h` is placed in `super_include_dir` (default `"common"`).

### 9.3 `by_layer` (multi-layer)

```
<output_dir>/
├── Driver/
│   ├── statable_types.h
│   ├── statable_transitions.h
│   ├── statable_transitions.c
│   ├── statable_role_functions.h
│   └── statable_role_functions.c
├── Application/
│   └── ... (same 5 files)
├── statable_init.c          ← common
├── statable_event_queue.c   ← common
├── statable_interrupt.c     ← common
├── statable_timer.c         ← common
├── osal.h                   ← common
├── osal.c                   ← common
├── statable_all.h           ← common (or root if super_include_dir unused)
└── {project}_run.c          ← common
```

### 9.4 Header Sample (`statable_types.h`)

- `STATE_<Layer>_t` / `EVENT_<Layer>_t` / `FLAG_t`
- `SystemData_t` / `EventFlags_t` / `SystemContext_t`
- `TransitionContext_t` / `TransitionContext_<Layer>_t`
- `DATA_*` / `FLAG_*` / `FIRE_EVENT` / `MAX_CONSECUTIVE_PENDING_EVENTS`

### 9.5 Source Sample (`statable_role_functions.c`)

Generation order (Stage 4):

1. `TRANSITION_ID_NONE` define
2. `RoleFuncCallSiteEntry_<Layer>_t` common struct
3. `Transition_GetId` prototype
4. Per-function `call_sites_<Short>[]`
5. Per-role-function implementations (NULL guard, transition_id, ctx->data pointer, ret, user markers)
6. `Transition_GetId` body (`static`)
7. File-tail user section

### 9.6 Source Sample (`statable_interrupt.c`)

- `#include "statable_types.h"`
- `#include "statable_all.h"` (Stage 3)
- Per ISR (ctx reference, logs, actions, user markers)

---

## 10. Errors and Warnings

| Kind | Source | Content |
|------|--------|---------|
| warning | `_run_steps_multi` | Unknown step action |
| warning | `_generate_table_switch` / `_generate_table_dictionary` | Not implemented → array fallback |
| warning | `_generate_process_switch_case` | Not implemented → table_driven fallback |
| warning | `merge_all_files` | `path_resolver` failure → use filename |
| warning | `inject_func_user_code` | Marker not found |
| warning | `inject_file_tail_user_code` | Tail marker not found |
| warning | `_step_interrupts` | `update_handler_symbols` failure |
| warning | `_dedupe_by_name` | Missing name or duplicate |
| warning | `_extract_func_names_from_condition` | C keyword excluded |

GUI's `WarningCollector` (`code_generation_dialog.py`) attaches to root logger; collects `WARNING+`, deduplicates, and shows QMessageBox.

---

## 11. Known Constraints

| # | Item | Status | Location |
|---|------|--------|----------|
| 1 | `switch_case` generation | **Not implemented** → `table_driven` fallback | `transition_generator.py` |
| 2 | `switch` table type | **Not implemented** → `array` fallback | Same |
| 3 | `dictionary` table type | **Not implemented** → `array` fallback | Same |
| 4 | `generation_style` / `table_type` GUI switch | **Not available** (forced) | `code_generation_settings_dialog.py` |
| 5 | `external_includes` in role / transitions / common | **Not implemented** | `c_code_generator.py` |
| 6 | FreeRTOS / ThreadX OSAL | Include only | `osal_generator.py` |
| 7 | `TransitionContext_t` common vs layer types | Both emitted; common uses `uint16_t` | `struct_generator.py` |
| 8 | Multi-layer `by_type` file merging | All layers merged into one file | `c_code_generator.py` |
| 9 | `project_dir_name` | Reserved, unused | `config.py` |
| 10 | `super_include_dir` in project XML | Not persisted (resets to `"common"`) | `xml_io.py` / `main_window.py` |
| 11 | `libcntrl` vs `statable` role uniqueness | Inconsistent (qualified vs pure) | `state_machine.py` / `libcntrl` |
| 12 | External includes path | Basename only | `code_generation_settings_dialog.py` |
| 13 | Empty `Transition.event` in `transition_to_flow_item` | Becomes `"NewEvent"` | `draft.py` |

---

## 12. Revision History

| Version | Date | Content |
|---------|------|---------|
| 3.0 | 2026-09-20 | Source-aligned full spec; covers 13 files, super include/loop, Stage 3 (ISR ctx), Stage 4 (Namespace.Name) |