以下、MISRA 対応の全変更を反映した **`SPEC_OVERVIEW_en.md` v2.1 の完全ファイル**です。主な更新点は:

- ヘッダのバージョン番号 (2.0 → 2.1)
- §7 Code Generation に version 履歴と MISRA 対応の詳細を追加
- §7.4 に **MISRA C:2012 対応状況** セクションを新設
- §11 テストポリシーを v2.2.6 対応に更新
- §12 既知の制約に MISRA 抑制情報を追加
- §14.2 ファイルサイズを更新
- §15 改訂履歴に v2.1 を追加

---

```markdown
# StaTable Overall Specification v2.1 (English, Detailed)

Version: 2.1
Date: 2026-09-20
Scope: StaTable project (whole)
Prerequisite: Source tree available (`statable/`, `statable_gui/`, `codegen/`)

---

## Table of Contents

1. Project Overview
2. Architecture
3. Data Model Layer (`statable/`)
4. GUI Layer (`statable_gui/`)
5. Shared Libraries (`libcntrl/`)
6. Transition Editor (`transition_editor_direct/`)
7. Code Generation (`codegen/`)
8. CI/CD
9. Development Environment
10. Coding Conventions
11. Testing Policy
12. Known Constraints
13. Glossary
14. Appendix
15. Revision History

---

## 1. Project Overview

### 1.1 Purpose

**StaTable** is a GUI tool that supports the entire workflow from state-transition design to C code generation for embedded systems. Designers define state transitions in tabular form, edit conditions and actions via drag-and-drop, and directly generate embedded-targeted C code.

### 1.2 Target Users

| User type | Intended use |
|-----------|--------------|
| Embedded engineer | State-machine design, C code generation |
| Design reviewer | Review via generated Mermaid diagrams and transition tables |
| Test engineer | Unit testing and CI verification of generated code |

### 1.3 Feature List

| # | Feature | Summary |
|---|---------|---------|
| F-01 | Multi-layer state machine editing | Layers represented by tabs; execution order controlled by priority |
| F-02 | Transition matrix editing | Cell editing on (state × event) matrix |
| F-03 | Drag-and-drop flow editor | Visually place transition conditions and pre/else actions |
| F-04 | Role function library | Shareable function definitions with namespace support |
| F-05 | Condition / literal library | Condition templates and literalization |
| F-06 | Global definitions | Variables, flags, interrupts, timers, queues |
| F-07 | Mermaid diagram generation | Automatic state diagram generation and preview |
| F-08 | C code generation | 13 files with markers |
| F-09 | User code preservation | Marker-based merging preserves user code on regeneration |
| F-10 | Validation / AI diagnostics | Pre-generation consistency checks |
| F-11 | Project XML persistence | Full project save/load |
| F-12 | CI verification | Automated checks via GitHub Actions |
| F-13 | **MISRA C:2012 compliance** | Generated C code is verified against MISRA C:2012 (informational) |

### 1.4 Non-functional Requirements

| Item | Requirement |
|------|-------------|
| Supported OS | Windows 10/11, Linux (Ubuntu 22.04+) |
| Python | 3.12 |
| GUI | PySide6 (Qt 6) |
| I/O | XML (UTF-8), C sources (UTF-8) |
| Dependencies | PySide6, pycparser (tests only) |
| Generated code | C99-compliant, `static` functions used extensively |
| Testing | 12 suites (`tests/test_v2_2_p*.py`) |
| CI | GitHub Actions, `ubuntu-latest` |
| MISRA | cppcheck 2.x + MISRA addon (informational only) |

### 1.5 Terminology

| Term | Definition |
|------|------------|
| Layer | A state-machine group identified by tab name. `sm.layer_name` |
| Cell | A (state, event) pair. The minimal unit of a transition function |
| Cell function | A `static` function processing one cell |
| Role function | A function called from transitions, conditions, or ISRs |
| namespace | The owning layer or explicit namespace of a role function |
| qualified_name | Unique name in `namespace.name` form (e.g., `Driver.Init`) |
| call_sites | The list of calling cells for each role function |
| transition_id | Index within call_sites. `0xFFFF` = no match |
| Super include | `statable_all.h`. Aggregates all generated headers |
| Super loop | `{project}_run.c`. Main loop for all layers |
| Marker | Comment used for user-code preservation (`[[STABLE_...]]`) |
| MISRA suppression | A documented, intentional deviation from MISRA C:2012 |

---

## 2. Architecture

### 2.1 Overall Structure

```
┌──────────────────────────────────────────────────────────────┐
│                        StaTable                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  statable_gui/                         │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │ main_window.py  : MainWindow                     │  │  │
│  │  │ widgets.py      : StateMachineTab, SettingsPanel │  │  │
│  │  │ matrix_table.py : MatrixTableWidget              │  │  │
│  │  │ code_generation_*.py : Dialogs                   │  │  │
│  │  │ + various edit dialogs                           │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────┐  ┌───────────────────┐   │  │
│  │  │ transition_editor_direct │  │ libcntrl/         │   │  │
│  │  │ (D&D editor)             │  │ (Shared libraries)│   │  │
│  │  └──────────────────────────┘  └───────────────────┘   │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │ calls                           │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    codegen/                            │  │
│  │  CCodeGenerator + 15 sub-generators                    │  │
│  │  (generated C is MISRA C:2012-aware; see §7.4)         │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │ reads                           │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    statable/                           │  │
│  │  StateMachine, GlobalDefinitions, XML I/O              │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Layer Composition

| Layer | Package | Responsibility | Depends on |
|-------|---------|----------------|------------|
| Presentation | `statable_gui/` | GUI display and user interaction | codegen, statable, libcntrl |
| D&D editing | `transition_editor_direct/` | Per-cell transition editing UI | statable_gui |
| Shared libraries | `libcntrl/` | Shared management of role functions etc. | (none) |
| Code generation | `codegen/` | C code generation | statable |
| Data model | `statable/` | State machine, global definitions, XML | (none) |

**Dependency direction**: `statable_gui` → `codegen` → `statable`. No reverse dependency.

### 2.3 Detailed Dependencies

```
statable_gui/main_window.py
  ├── statable.state_machine.StateMachine
  ├── statable.xml_io.project_to_xml / project_from_xml
  ├── statable.global_defs.GlobalDefinitions
  ├── statable.sample_data.create_sample_*
  ├── libcntrl.role_function_library.RoleFunctionLibrary
  ├── libcntrl.condition_library.ConditionLibrary
  ├── libcntrl.literal_library.LiteralLibrary
  ├── codegen.c_code_generator.CCodeGenerator
  ├── codegen.sample_data.SampleDataGenerator
  ├── codegen.config.ConfigManager
  ├── statable_gui.code_generation_dialog.CodeGenerationDialog
  ├── statable_gui.code_generation_settings_dialog.CodeGenerationSettingsDialog
  └── statable_gui.widgets.StateMachineTab
```

### 2.4 Data Flow

#### 2.4.1 Startup → Editing

```
MainWindow.__init__
  ├── create_sample_global_defs()        # Demo data
  ├── RoleFunctionLibrary()              # Empty library
  ├── ConditionLibrary()                 # Empty library
  ├── LiteralLibrary()                   # Empty library
  ├── create_sample_state_machine()      # Demo state machine
  ├── add_state_machine_tab("Application", sample_sm)
  └── Each tab creates a StateMachineTab
       ├── MatrixTableWidget (transition matrix)
       ├── MermaidWidget (diagram)
       └── SettingsPanel (states / role functions)
```

#### 2.4.2 Cell Editing → Save

```
MatrixTableWidget.cellDoubleClicked(row, col)
  ├── sm.get_transitions_for_cell(state, event)
  ├── transition_to_flow_item(trans) -> build ActionDraft
  ├── Open ActionEditorDialog
  │    ├── PaletteWidget (left)
  │    ├── FlowCanvas (center)
  │    └── CodeWidget (bottom)
  ├── Edit flow_items via D&D
  ├── OK -> flow_item_to_transition(item) -> Transition
  └── Update sm.transitions -> populate() -> redraw
```

#### 2.4.3 Code Generation

```
MainWindow.save_generated_code_direct()
  ├── config = config_manager.get_config()
  ├── layers = _get_all_layers()        # all tabs, priority ascending
  ├── collector = WarningCollector()
  ├── root_logger.addHandler(collector)
  ├── generator = CCodeGenerator(config=config)
  ├── files = generator.generate_all_layers(layers, global_defs, lib)
  ├── if config.save_with_merge:
  │      saved = generator.save_generated_code_with_merge(files, output_dir)
  │   else:
  │      saved = generator.save_generated_code(files, output_dir)
  ├── root_logger.removeHandler(collector)
  └── QMessageBox: completion notification + warnings
```

### 2.5 Startup Sequence

```
1. python -m statable_gui.main  (or run main_window.py directly)
2. PySide6.QtWidgets.QApplication created
3. MainWindow() created
   ├── StaTableLogger() initialization
   ├── Preferences() load
   ├── ConfigManager() created
   ├── GlobalDefinitions demo data
   ├── RoleFunctionLibrary / ConditionLibrary / LiteralLibrary
   ├── create_sample_state_machine() -> register role_functions into libcntrl
   ├── QTabWidget setup
   ├── create_menus() / create_toolbar()
   ├── TraceBallWidget created (hidden)
   └── add_state_machine_tab("Application", sample_sm)
4. app.exec() enters event loop
```

---

## 3. Data Model Layer (`statable/`)

### 3.1 Module List

| # | Module | Approx. LOC | Responsibility |
|---|--------|-------------|----------------|
| 1 | `__init__.py` | - | Public API |
| 2 | `model.py` | 100 | Dataclasses and enums |
| 3 | `state_machine.py` | 60 | StateMachine container |
| 4 | `global_defs.py` | 200 | Global definitions |
| 5 | `xml_io.py` | 600 | XML save/load |
| 6 | `mermaid_gen.py` | 50 | Mermaid diagram generation |
| 7 | `sample_data.py` | 130 | Sample data |
| 8 | `parser.py` | 3 | Stub |

### 3.2 `model.py`

#### 3.2.1 Enum Definitions

```python
class StateType(Enum):
    NORMAL = "normal"
    CONCURRENT = "concurrent"
    REGION = "region"
    INITIAL = "initial"
    FINAL = "final"
    CHOICE = "choice"
    JUNCTION = "junction"

class EventKind(Enum):
    SIGNAL = "signal"
    CALL = "call"
    TIME = "time"
    CHANGE = "change"

class EventDeliveryType(Enum):
    DIRECT = "direct"    # Direct delivery
    QUEUE  = "queue"     # Queued delivery
    DOUBLE = "double"    # Double delivery

class EventSourceLayer(Enum):
    DRIVER = "driver"
    MIDDLEWARE = "middleware"
```

#### 3.2.2 `State`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | str | – | State name |
| `type` | StateType | NORMAL | State kind |
| `parent` | Optional[str] | None | Parent state (for hierarchy) |
| `entry` | List[str] | [] | Entry actions (v2.2) |
| `exit` | List[str] | [] | Exit actions (v2.2) |
| `do` | str | "" | Do action |
| `description` | str | "" | Description |

**v2.2 change**: `entry` / `exit` are now `List[str]`. Legacy `str` values are auto-migrated.

#### 3.2.3 `Event`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | str | – | Event name (empty = completion transition) |
| `id` | Optional[int] | None | Event ID |
| `kind` | EventKind | SIGNAL | Kind |
| `params` | List[str] | [] | Parameter names |
| `priority` | int | 0 | Priority |
| `description` | str | "" | Description |
| `delivery_type` | EventDeliveryType | DIRECT | Delivery type |
| `source_layer` | EventSourceLayer | DRIVER | Source layer |
| `data_type` | str | "" | Associated data type |
| `data_name` | str | "" | Associated data name |
| `title` | str | "" | Display name (auto-generated if unset) |

#### 3.2.4 `Transition` (v2.2)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `source` | str | – | Source state |
| `event` | str | – | Event name |
| `condition` | str | "" | Condition expression |
| `pre_actions` | List[str] | [] | Pre-transition actions |
| `target` | str | "" | Target state |
| `has_else` | bool | True | Presence of else clause |
| `else_target` | str | "" | else target state |
| `else_actions` | List[str] | [] | else actions |
| `action` | str | "" | Legacy field (unused) |
| `transition_type` | str | "external" | Transition type |
| `title` | str | "" | Display name |
| `early_return` | bool | False | v2.2: Commit if True |
| `label` | str | "" | v2.2: Label within cell (T1, T2, ...) |

#### 3.2.5 `RoleFunction`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | str | – | Pure name (`Init`) |
| `namespace` | str | "" | Namespace (`Driver`) |
| `description` | str | "" | Description |
| `return_type` | str | "void" | Return type |
| `arg1_type` | str | "" | Argument 1 type |
| `arg1_name` | str | "" | Argument 1 name |
| `arg2_type` | str | "" | Argument 2 type |
| `arg2_name` | str | "" | Argument 2 name |
| `title` | str | "" | Display name |

**Property**:
- `qualified_name -> str`: `namespace.name` or `name`

**Class method**:
- `from_legacy_name(legacy_name, layer_names=None) -> RoleFunction`:
  - `"Driver_Init"` → `namespace="Driver", name="Init"`
  - If not in `layer_names`, `namespace=""`

### 3.3 `state_machine.py`

#### 3.3.1 Class `StateMachine`

**Attributes**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `states` | Dict[str, State] | {} | State dictionary |
| `events` | Dict[str, Event] | {} | Event dictionary |
| `transitions` | List[Transition] | [] | Transition list |
| `role_functions` | Dict[str, RoleFunction] | {} | Role function dictionary |
| `initial_state` | Optional[str] | None | Initial state |
| `layer_priority` | int | 5 | Layer priority (1–9) |
| `layer_description` | str | "" | Layer description |
| `layer_name` | str | "" | Layer name |
| `cell_actions` | Dict[Tuple[str,str], List[ActionStep]] | {} | v2.2: Cell actions |
| `cell_relations` | Dict[Tuple[str,str], List[TransitionRelation]] | {} | v2.2: Cell relations |

**Methods**

| Method | Description | Exception |
|--------|-------------|-----------|
| `add_state(state)` | Add state | `ValueError` on duplicate |
| `add_event(event)` | Add event | `ValueError` on duplicate |
| `remove_event(name)` | Remove event and related transitions | – |
| `add_transition(trans)` | Add transition | `ValueError` if source/target/event undefined |
| `remove_transition(trans)` | Remove transition | – |
| `set_initial(name)` | Set initial state | `ValueError` if undefined |
| `add_role_function(rf)` | Add role function | `ValueError` on duplicate `rf.name` |
| `remove_role_function(name)` | Remove role function | – |
| `get_transitions_for_cell(source, event) -> List[Transition]` | Get cell transitions | – |
| `get_actions_for_cell(source, event) -> List[ActionStep]` | v2.2: cell actions | – |
| `set_actions_for_cell(source, event, actions)` | v2.2: set cell actions | – |
| `get_relations_for_cell(source, event) -> List[TransitionRelation]` | v2.2: cell relations | – |
| `set_relations_for_cell(source, event, relations)` | v2.2: set cell relations | – |
| `get_cell_keys() -> List[Tuple[str,str]]` | v2.2: all cell keys | – |
| `remove_cell_metadata(source, event)` | v2.2: remove cell metadata | – |

**Note**: `add_role_function` keys by `rf.name` (pure). `Driver.Init` and `App.Init` collide.

### 3.4 `global_defs.py`

#### 3.4.1 Dataclass List

| Class | Purpose |
|-------|---------|
| `StructMemberDef` | Struct member |
| `CustomTypeDef` | User-defined type |
| `SystemVariable` | Global variable |
| `EventFlag` | Event flag |
| `InterruptAction` | Interrupt action |
| `InterruptHandlerDef` | Interrupt handler |
| `DevicePlaceholderDef` | Device placeholder |
| `TimerDerivedDef` | Derived timer |
| `TimerBaseDef` | Timer base |
| `EventQueueDef` | Event queue |

#### 3.4.2 `InterruptHandlerDef`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | str | – | Handler name |
| `description` | str | "" | Description |
| `event_names` | List[str] | [] | Related events |
| `is_timer` | bool | False | Timer interrupt |
| `actions` | List[InterruptAction] | [] | Actions |
| `title` | str | "" | Display name |
| `used_role_functions` | List[str] | [] | Used role functions (auto-extracted) |
| `used_variables` | List[str] | [] | Used variables (auto-extracted) |

#### 3.4.3 `GlobalDefinitions`

**Attributes**
- `variables: List[SystemVariable]`
- `flags: List[EventFlag]`
- `interrupts: List[InterruptHandlerDef]`
- `placeholders: List[DevicePlaceholderDef]`
- `timer_base: TimerBaseDef`
- `extra_timers: List[TimerBaseDef]`
- `event_queues: List[EventQueueDef]`
- `custom_types: List[CustomTypeDef]`

**Methods**
- `add_timer_variables()`: auto-register timer variables in `variables` (group="Timer")
- `variable_groups() -> List[str]`: variable group list
- `flag_groups() -> List[str]`: flag group list
- `custom_type_names() -> List[str]`: custom type name list

### 3.5 `xml_io.py`

#### 3.5.1 Public Functions

| Function | Description |
|----------|-------------|
| `project_to_xml(tabs, gd, filepath, role_lib=None, cond_lib=None, lit_lib=None, project_settings=None)` | Save project |
| `project_from_xml(filepath) -> (tabs, gd, role_lib, cond_lib, lit_lib, project_settings)` | Load project |

#### 3.5.2 XML Structure (v2.2 extended)

```xml
<Project name="MyProject">
  <ProjectSettings>
    <CodeGeneration ... />
  </ProjectSettings>
  <GlobalDefinitions>
    <CustomTypes>...</CustomTypes>
    <SystemVariables>...</SystemVariables>
    <EventFlags>...</EventFlags>
    <Interrupts>
      <Interrupt name="..." ...>
        <Action condition="..." action="..."/>
        <UsedRoleFunction ref="Driver.Init"/>
        <UsedVariable name="counter"/>
      </Interrupt>
    </Interrupts>
    <DevicePlaceholders>...</DevicePlaceholders>
    <TimerBase>...</TimerBase>
    <ExtraTimers>...</ExtraTimers>
    <EventQueues>...</EventQueues>
  </GlobalDefinitions>
  <SharedLibraries>
    <RoleFunctionLibrary>...</RoleFunctionLibrary>
    <ConditionLibrary>...</ConditionLibrary>
    <LiteralLibrary>...</LiteralLibrary>
  </SharedLibraries>
  <Tab name="Application">
    <StateMachine initial="..." layer_priority="5" layer_name="Application">
      <States>
        <State name="Idle" ...>
          <Entry>
            <Action name="Driver.IdleEntry"/>
          </Entry>
          <Exit>
            <Action name="Driver.IdleExit"/>
          </Exit>
        </State>
      </States>
      <Events>...</Events>
      <RoleFunctions>
        <RoleFunction name="Init" namespace="Driver" .../>
      </RoleFunctions>
      <Transitions>
        <Transition source="..." event="..." condition="..." target="..."
                    has_else="true" else_target="..."
                    early_return="true" label="T1">
          <PreAction action="..."/>
          <ElseAction action="..."/>
        </Transition>
      </Transitions>
      <Cells>
        <Cell source="Error" event="RESET">
          <Actions>
            <Action role_function="Driver.PreCheck"
                    trigger="before_transitions" title="Pre-check" />
            <Action role_function="Driver.Cleanup"
                    trigger="after_transitions" title="Cleanup" />
          </Actions>
          <Relations>
            <Relation kind="group" members="T1,T2"
                      shared_condition="running == false" note="...">
              <Children>
                <Relation kind="exclusive" members="T1,T2"
                          shared_condition="" note="..." />
              </Children>
            </Relation>
          </Relations>
        </Cell>
      </Cells>
    </StateMachine>
  </Tab>
</Project>
```

#### 3.5.3 Legacy Migration

- If a `RoleFunction` has no `namespace` and `name` has a `<layer>_` prefix, the namespace is automatically separated.
- If `State.entry` / `exit` are legacy `str`, they are converted to `List[str]`.

#### 3.5.4 Known Constraints

- `super_include_dir` is **not** persisted (resets to default `"common"` on load)
- `_normalize_actions` automatically rejoins legacy data split into single characters

### 3.6 `mermaid_gen.py`

| Function | Description |
|----------|-------------|
| `generate_mermaid(sm) -> str` | Generate `stateDiagram-v2` from StateMachine |
| `_truncate_condition(condition, max_chars=50) -> str` | Truncate long conditions |

**Output format**:
```
stateDiagram-v2
    direction LR
    [*] --> InitialState
    Source --> Target : Title (Event) [Condition]
    note right of State : internal: Title (Event)
```

### 3.7 `sample_data.py`

| Function | Description |
|----------|-------------|
| `create_sample_state_machine() -> StateMachine` | 4 states, 5 events, 6 transitions, 2 role functions |
| `create_sample_global_defs() -> GlobalDefinitions` | 3 variables, 2 flags, 2 types, 1 interrupt, 2 timer groups, 1 queue |

**Note**: Role functions in `create_sample_state_machine` are in **legacy form** (`Sensor_Init`, `Error_Log`). No namespace used.

---

## 4. GUI Layer (`statable_gui/`)

*(See companion file `SPEC_OVERVIEW_ja.md` §4 for the full module list. This section is unchanged from v2.0 except for v2.2 SettingsPanel behavior which is described in `SPEC_SCREENS_en.md` §6.3.)*

### 4.1 Module List

| # | Module | Main class | Purpose |
|---|--------|-----------|---------|
| 1 | `main_window.py` | `MainWindow` | Main window |
| 2 | `widgets.py` | `StateMachineTab`, `SettingsPanel`, `MermaidWidget` | Tabs |
| 3 | `matrix_table.py` | `MatrixTableWidget` | Transition matrix |
| 4 | `code_generation_dialog.py` | `CodeGenerationDialog`, `WarningCollector` | Generation UI |
| 5 | `code_generation_settings_dialog.py` | `CodeGenerationSettingsDialog` | Settings UI |
| 6 | `condition_builder_dialog.py` | `ConditionBuilderDialog`, `LiteralizationDialog` | Condition builder |
| 7 | `config.py` | – | Constants, resource paths |
| 8 | `logger.py` | `StaTableLogger` | Logging |
| 9 | `preferences.py` | `Preferences` | App preferences |
| 10 | `traceball.py` | `TraceBallWidget` | Log display |
| 11 | `global_defs_dialog.py` | `GlobalDefinitionsDialog` | Global definitions |
| 12 | `event_definition_dialog.py` | `EventDefinitionDialog` | Event definitions |
| 13 | `event_delivery_settings_dialog.py` | `EventDeliverySettingsDialog` | Delivery settings |
| 14 | `interrupt_handler_edit_dialog.py` | `InterruptHandlerEditDialog` | Interrupt editing |
| 15 | `layer_settings_dialog.py` | `LayerSettingsDialog` | Layer settings |
| 16 | `validation_dialog.py` | `ValidationDialog` | Validation |
| 17 | `common_widgets.py` | `TypeManagerDialog` | Type management |
| 18 | `action_edit_dialog.py` | `ActionEditDialog` | Legacy action editing |
| 19 | `role_function_dialog.py` | `RoleFunctionDialog` | Legacy role function editing |
| 20 | `global_defs.py` | – | (re-export; estimated) |

### 4.2 `MainWindow`

*(Unchanged from v2.0; see `SPEC_SCREENS_en.md` for layout, menus, toolbar.)*

### 4.3 `StateMachineTab`

*(Unchanged from v2.0.)*

### 4.4 `MermaidWidget`

*(Unchanged from v2.0. See `SPEC_SCREENS_en.md` §2.)*

### 4.5 `MatrixTableWidget`

*(Unchanged from v2.0.)*

### 4.6 `SettingsPanel` (v2.2)

| Tab name | Columns |
|----------|---------|
| `State list` | Name / Description / entry function / exit function / do function / Type |
| `Role function` | Title / Function name / **Namespace** / Description / Return type / Arg 1 type / Arg 1 name / Arg 2 type / Arg 2 name |

`State.entry` and `State.exit` are `List[str]`; UI joins/splits via `"; "`.

### 4.7 `CodeGenerationDialog`

*(Unchanged from v2.0.)*

### 4.8 `WarningCollector`

*(Unchanged from v2.0.)*

### 4.9 `ConditionBuilderDialog`

*(Unchanged from v2.0.)*

---

## 5. Shared Libraries (`libcntrl/`)

### 5.1 Module List

| Module | Main class |
|--------|-----------|
| `role_function_library.py` | `RoleFunctionLibrary`, `RoleFunction` |
| `condition_library.py` | `ConditionLibrary`, `ConditionTemplate` |
| `literal_library.py` | `LiteralLibrary`, `LiteralDefinition` |
| `role_function_edit_dialog.py` | `RoleFunctionEditDialog` |
| `literal_management_dialog.py` | `LiteralManagementDialog`, `LiteralEditDialog` |

### 5.2 `RoleFunctionLibrary`

| Method | Description |
|--------|-------------|
| `_key(rf) -> str` | `rf.qualified_name` |
| `add(rf)` | `ValueError` on duplicate |
| `remove(name)` | Accepts both qualified and pure names |
| `get(name) -> Optional[RoleFunction]` | Accepts both qualified and pure names |
| `list_all() -> List[RoleFunction]` | All entries |

### 5.3 `RoleFunction` (libcntrl version)

| Field | Type | Default |
|-------|------|---------|
| `name` | str | – |
| `namespace` | str | "" |
| `description` | str | "" |
| `title` | str | "" |
| `used_global_vars` | List[str] | [] |
| `used_events` | List[str] | [] |
| `used_literals` | List[str] | [] |

**Property**: `qualified_name -> str`

**Note**: A different class from `statable.RoleFunction`. Both have `namespace`, but key management differs.

---

## 6. Transition Editor (`transition_editor_direct/`)

### 6.1 Module List

| Module | Main class | Purpose |
|--------|-----------|---------|
| `draft.py` | `ActionDraft`, `FlowItem`, `SystemGlobal`, `TransitionParams` | Model |
| `dialog.py` | `ActionEditorDialog` | Entry point |
| `palette_widget.py` | `PaletteWidget`, `PaletteListWidget` | Palette |
| `canvas_widget.py` | `FlowCanvas`, `FlowNodeItem` | Canvas |
| `code_widget.py` | `CodeWidget` | Code preview |
| `system_global_dialog.py` | `SystemGlobalDialog` | Global editing |
| `flow_widget.py` | `FlowWidget`, `FlowListWidget` | **Legacy** |
| `edit_dialogs.py` | `FunctionEditDialog`, `TransitionEditDialog` | **Legacy** |

*(Other details unchanged from v2.0. See `SPEC_SCREENS_en.md` §7.2 for dialog flows.)*

---

## 7. Code Generation (`codegen/`)

### 7.1 Module List (16)

| # | Module | Purpose | Current version |
|---|--------|---------|-----------------|
| 1 | `c_code_generator.py` | Step-table driven orchestration | v2.2.9 |
| 2 | `role_function_generator.py` | Role function declaration / implementation | v3.3 |
| 3 | `transition_generator.py` | Cell functions / tables / GetNextEvent | v2.6 |
| 4 | `code_templates.py` | Template dictionary (OSAL + code patterns) | v2.2.4 |
| 5 | `struct_generator.py` | System structs | – |
| 6 | `enum_generator.py` | State / Event / Flag enums | – |
| 7 | `variable_generator.py` | Variable macros + `SystemContext_Init` | – |
| 8 | `event_queue_generator.py` | Event queue implementation | – |
| 9 | `interrupt_generator.py` | ISR generation | – |
| 10 | `timer_generator.py` | Timer struct / `Timer_Init` / `Timer_Update` | v2.2 |
| 11 | `osal_generator.py` | OSAL header / source | v2.2 |
| 12 | `type_mapper.py` | C type mapping | – |
| 13 | `naming_convention.py` | Naming rules | – |
| 14 | `code_merger.py` | Marker-based merge | – |
| 15 | `config.py` | `CodeGenerationConfig` / `ConfigManager` | – |
| 16 | `sample_data.py` | Demo data for generation | – |

### 7.2 Output Files (13)

| # | File | Type | Purpose |
|---|------|------|---------|
| 1 | `statable_types_common.h` | Header | Common structs, enums (incl. `FLAG_t`), logging macros, `SystemContext_Init` / `Timer_*` prototypes |
| 2 | `statable_types.h` | Header | Per-layer enums + `TransitionContext_<Layer>_t` |
| 3 | `statable_transitions.h` | Header | `StateMachine_Process_*` + `StateMachine_GetNextEvent_*` prototypes |
| 4 | `statable_transitions.c` | Source | Cell functions, transition table, `Process`, `GetNextEvent` |
| 5 | `statable_role_functions.h` | Header | `RoleFunc_<NS>_<Name>` declarations (self-layer only) |
| 6 | `statable_role_functions.c` | Source | Role function implementations + `call_sites` + `Transition_GetId` |
| 7 | `statable_init.c` | Source | `SystemContext_Init` |
| 8 | `statable_event_queue.c` | Source | Event queue implementation |
| 9 | `statable_interrupt.c` | Source | ISRs |
| 10 | `statable_timer.c` | Source | Timer struct + `Timer_Init` / `Timer_Update` |
| 11 | `osal.h` | Header | OS abstraction |
| 12 | `osal.c` | Source | OS abstraction (NonRTOS / FreeRTOS includes / ThreadX includes) |
| 13 | `statable_all.h` | Header | Super include |
| 14 | `{project}_run.c` | Source | Super loop |

*(13 files when super include is counted separately.)*

### 7.3 Folder Structures

| Structure | Layout |
|-----------|--------|
| `flat` | All files in one directory |
| `by_type` | `include/` / `src/` / `common/` |
| `by_layer` | Per-layer subdirectories + common at root |

### 7.4 MISRA C:2012 Compliance

#### 7.4.1 Overview

StaTable's generated C code is verified against **MISRA C:2012** using `cppcheck` + the official MISRA addon. The check is **informational only** — it does not fail the build (see `misra_report/summary.md`). Baseline history and suppressions are documented in `misra/baseline.md` and `misra/suppressions.txt`.

#### 7.4.2 Baseline History

| Version | Date | MISRA hits | Non-MISRA | Primary fixes |
|---------|------|-----------:|----------:|---------------|
| v2.2.5 | 2026-09-19 | 183 | 290 | Initial measurement |
| v2.2.6 | 2026-09-20 | 38 | 9 | Cross-layer `role_functions` include; `(void)` on unused locals |
| v2.2.7 | 2026-09-20 | 29 | 9 | `LOG_*` macros defined; `GetNextEvent_*` prototypes |
| v2.2.8 | 2026-09-20 | 14 | 9 | 12.1 parentheses; 10.4 unsigned literals in OSAL |
| v2.2.9 | 2026-09-20 | 14 | 9 | `statable_types_common.h` added to `transitions_c` |
| v2.6 | 2026-09-20 | 11 | 9 | `LOG_ERROR` removed from generated `GetNextEvent_*` body |
| v2.6.1 | 2026-09-20 | **10** | 9 | 10.4 timer multiplier `10U` |

#### 7.4.3 Current State (v2.6.1)

**MISRA hits: 10 (all suppressed by design)**

| Rule | Count | Suppression reason |
|------|------:|--------------------|
| `8.4` | 3 | Module structure: per-layer extern visibility |
| `11.5` | 4 | bare-metal OSAL pointer cast (`void *` → `uint8_t *`) |
| `18.4` | 2 | bare-metal OSAL pointer arithmetic |
| `15.7` | 1 | `_handled` pattern: independent `if` guards |

**Non-MISRA warnings: 9 (informational only)**

| ID | Count | Status |
|----|------:|--------|
| `knownConditionTrueFalse` | 3 | Acceptable (relation nesting) |
| `redundantInitialization` | 2 | Cosmetic |
| `variableScope` | 2 | Cosmetic |
| `unreadVariable` | 2 | Acceptable (user code markers) |

#### 7.4.4 Suppression Rationale

See `misra/suppressions.txt` for the full text. Summary:

| Rule | Rationale |
|------|-----------|
| `8.4` | Per-layer extern visibility requires module reorganization; design decision to keep layer-crossing cooperation |
| `11.5` | bare-metal OSAL uses `void *` + `uint8_t *` casts to avoid `memcpy` (real-time / code size) |
| `18.4` | Same as `11.5`: OSAL queue pointer arithmetic |
| `15.7` | `_handled` pattern: each `if` is an independent guard; `else if` would change semantics |

#### 7.4.5 Condition-side Role Function Calls

Role function calls inside `Transition.condition` and `Relation.shared_condition` are emitted **without** a `(void)` cast, so their `int` return value is preserved:

```c
if (RoleFunc_Driver_PreCheck(transition, ctx) == 0) {   /* return value preserved */
    next_state = STATE_Driver_Ready;
}
```

Role function calls in **action contexts** (`pre_actions`, `else_actions`, cell actions, state entry / exit) are emitted with a `(void)` cast for MISRA 17.7 compliance:

```c
(void)RoleFunc_Driver_LogError(transition, ctx);
```

This distinction is implemented via:
- `_role_func_call_expr()` — for condition expressions (no `(void)`)
- `_role_func_call_action()` — for action contexts (`(void)` cast)
- Raw text insertion of `Transition.condition` / `Relation.shared_condition`

---

## 8. CI/CD

### 8.1 Workflow

`.github/workflows/check.yml` (repository root)

### 8.2 Job Composition

| Job | Depends on | Purpose |
|-----|-----------|---------|
| `no-japanese` | – | Detect non-ASCII |
| `syntax` | – | compileall |
| `tests` | syntax | 12 test suites |
| `generated-code` | syntax | C code generation verification |

### 8.3 Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `QT_QPA_PLATFORM` | `offscreen` | GUI headless |
| `STATABLE_DISABLE_MERMAID` | `1` | Mermaid suppression |
| `PYTHONIOENCODING` | `utf-8` | Prevent encoding issues |

### 8.4 Qt System Libraries

```
libegl1, libgl1, libglib2.0-0, libdbus-1-3,
libxkbcommon0, libxkbcommon-x11-0,
libxcb-icccm4, libxcb-image0, libxcb-keysyms1,
libxcb-randr0, libxcb-render-util0, libxcb-shape0,
libxcb-xinerama0, libxcb-xfixes0, libxcb-cursor0,
libfontconfig1, libfreetype6
```

### 8.5 Recommended (Not Yet Implemented)

The following CI additions are recommended (see §12 R-04):

- `gcc -fsyntax-only` for all generated `.c` files
- `arm-none-eabi-gcc -fsyntax-only` for embedded targets

---

## 9. Development Environment

### 9.1 Requirements

| Item | Version |
|------|---------|
| Python | 3.12 |
| PySide6 | Latest |
| Git | Latest |
| OS | Windows 10/11 or Ubuntu 22.04+ |
| cppcheck | 2.x (for MISRA verification) |

### 9.2 Setup

```bash
git clone https://github.com/akashi-hideki/StaTable.git
cd StaTable/code
pip install PySide6 pycparser
```

### 9.3 Run

```bash
cd code
python -m statable_gui.main
```

### 9.4 Test

```bash
cd code
python tests/test_v2_2_p1.py
# ... 11 other suites
```

### 9.5 MISRA Verification

```bash
cd code
python tools/run_misra_check.py --root output --out misra_report
python tools/analyze_misra_impact.py \
  --xml misra_report/cppcheck_stderr.txt \
  --out misra_report/impact.md \
  --csv misra_report/impact.csv
```

---

## 10. Coding Conventions

### 10.1 Python

| Item | Convention |
|------|------------|
| Indentation | 4 spaces |
| Strings | Double quotes preferred |
| Type hints | Required on public APIs |
| Docstrings | At module top + public classes/methods |
| Naming | `snake_case` (functions/variables), `PascalCase` (classes) |

### 10.2 Comment Language

- **In-code comments and docstrings**: English preferred (detected by the `no-japanese` CI job)
- **Specifications**: Separate Japanese and English versions

### 10.3 C Code

- C99-compliant
- Extensive use of `static` functions
- Generated files start with `@file` / `@brief` / `@note` / `@date`
- MISRA C:2012 aware (see §7.4)

---

## 11. Testing Policy

### 11.1 Test Suites

| File | Target | Expected result |
|------|--------|-----------------|
| `test_v2_2_p1.py` | Data model (v2.2 additions) | 94 PASS / 0 FAIL |
| `test_v2_2_p2.py` | Codegen (v2.2 / MISRA-aware expectations) | 67 PASS / 0 FAIL |
| `test_v2_2_p3.py` | GUI helpers | 37 PASS / 0 FAIL |
| `test_v2_2_p4a.py` | Code generation (basics) | 82 PASS / 0 FAIL |
| `test_v2_2_p4b.py` | Code generation (detailed) | 30 PASS / 0 FAIL |
| `test_v2_2_p12_2.py` | Stage 2 features | 31 PASS / 0 FAIL |
| `test_v2_2_p12_5.py` | Stage 5 features (group nesting) | 37 PASS / 0 FAIL |
| `test_v2_2_p12_6.py` | Stage 6 features (AI action ext.) | 55 PASS / 0 FAIL |
| `test_v2_2_p12_7.py` | Stage 7 features | 9 PASS / 0 FAIL |
| `test_v2_2_p12_8.py` | Stage 8 features (generated C struct) | 25 PASS / 0 FAIL |
| `test_v2_2_p12_9.py` | Stage 9 features (XML round-trip) | 41 PASS / 0 FAIL |
| `test_v2_2_p12_10.py` | Stage 10 features (structure) | 29 PASS / 2 SKIP / 0 FAIL |

**Total**: **537 PASS / 0 FAIL / 2 SKIP**

### 11.2 `test_v2_2_p2.py` Update History

- **v2.2.6**: Updated expectations for MISRA-aware codegen:
  - Single Commit no longer declares `_handled`
  - Mixed `!`/`&&` conditions are parenthesized (MISRA 12.1)
  - `_role_func_call_action()` emits `(void)` in action contexts

### 11.3 Execution Environment

- Local: works on Windows too
- CI: `ubuntu-latest` + `QT_QPA_PLATFORM=offscreen`

### 11.4 Verification Tools

- `tools/find_all_japanese.py`: non-ASCII detection
- `tools/verify_generated_code.py`: syntax and structure verification of generated C code
- `tools/run_misra_check.py`: MISRA C:2012 check via cppcheck + addon
- `tools/analyze_misra_impact.py`: Maps MISRA violations to responsible codegen sources

### 11.5 Testing Gaps

| Gap | Impact |
|-----|--------|
| No `gcc -fsyntax-only` in CI | Compile errors not detected |
| No test for `super_include_dir` persistence | Regression undetected |
| No namespace-collision test | Data loss undetected |
| No test for empty-event `transition_to_flow_item` | Bug remains |
| Legacy `flow_widget.py` / `edit_dialogs.py` untested | Dead code drift |

---

## 12. Known Constraints

| # | Item | Status | Impact |
|---|------|--------|--------|
| C-01 | `generation_style` / `table_type` GUI switch | **Not selectable** (forced) | Settings UI fixed label |
| C-02 | `switch_case` generation | **Not implemented** → `table_driven` | Warning log |
| C-03 | `switch` table | **Not implemented** → `array` | Warning log |
| C-04 | `dictionary` table | **Not implemented** → `array` | Warning log |
| C-05 | `external_includes_in_role` | **Not implemented** | Config flag ignored |
| C-06 | `external_includes_in_transitions` | **Not implemented** | Same as above |
| C-07 | `external_includes_in_common` | **Not implemented** | Same as above |
| C-08 | FreeRTOS OSAL | **Include only** | No function bodies |
| C-09 | ThreadX OSAL | **Include only** | Same as above |
| C-10 | Project XML `super_include_dir` | **Not persisted** | Resets to `"common"` |
| C-11 | Role function uniqueness mismatch | **Design asymmetry** | Cross-namespace collision |
| C-12 | `transition_to_flow_item` empty event | **Bug** | Converts to `"NewEvent"` |
| C-13 | `palette_widget._add_function` import | **No fallback** | `ImportError` possible |
| C-14 | `project_dir_name` | **Reserved, unused** | No effect |
| C-15 | `flow_widget.py` / `edit_dialogs.py` | **Legacy** | Dead code, unreferenced |
| C-16 | External include path | **Filename only** | Directory part lost |
| C-17 | `TransitionContext_t` vs `TransitionContext_<Layer>_t` | **Both emitted** | Two types, same layout |
| C-18 | Multi-layer `by_type` | **Merged into 1 file** | Layer separation invisible |
| C-19 | Output-dir warning missing `\n` | **Cosmetic bug** | "settingsPlease specify" |
| C-20 | `flow_item_to_transition` title handling | **Edge case** | `edited_text == name` → `"(無題遷移)"` |
| C-21 | MISRA 8.4 / 11.5 / 18.4 / 15.7 | **Suppressed by design** | See §7.4.4 and `misra/suppressions.txt` |

---

## 13. Glossary

| Term | Description |
|------|-------------|
| Layer | A state-machine group per tab |
| Cell | A (state, event) pair |
| Cell function | A `static` transition function per cell |
| Role function | A function for condition evaluation and actions |
| namespace | The namespace of a role function |
| qualified_name | `namespace.name` |
| call_sites | List of calling cells for a role function |
| transition_id | Index within call_sites |
| Super include | `statable_all.h` |
| Super loop | `{project}_run.c` |
| Marker | Comment used for user-code preservation |
| ISR | Interrupt Service Routine |
| D&D | Drag and Drop |
| MIME | Format identifier for drag data |
| MISRA | Motor Industry Software Reliability Association |
| cppcheck | Static analysis tool for C/C++ |

---

## 14. Appendix

### 14.1 File Tree

```
StaTable/
├── .github/
│   └── workflows/
│       └── check.yml
├── code/
│   ├── statable/
│   ├── statable_gui/
│   │   ├── transition_editor_direct/
│   │   └── libcntrl/
│   ├── codegen/
│   ├── tests/
│   ├── tools/
│   └── misra/
│       ├── suppressions.txt
│       └── baseline.md
├── docs/
│   ├── SPEC_OVERVIEW_ja.md
│   ├── SPEC_OVERVIEW_en.md
│   ├── SPEC_SCREENS_ja.md
│   ├── SPEC_SCREENS_en.md
│   ├── SPEC_AUDIT_ja.md
│   └── SPEC_CODEGEN_v3.md
└── README.md
```

### 14.2 Approximate File Sizes

| File | Approx. LOC |
|------|-------------|
| `codegen/c_code_generator.py` | ~1,400 |
| `codegen/role_function_generator.py` | ~950 |
| `codegen/code_templates.py` | ~750 |
| `codegen/transition_generator.py` | ~700 |
| `statable_gui/main_window.py` | ~1,000 |
| `statable_gui/code_generation_dialog.py` | ~400 |
| `transition_editor_direct/canvas_widget.py` | ~450 |

### 14.3 MISRA Artifacts

| Artifact | Path | Content |
|----------|------|---------|
| Suppressions | `misra/suppressions.txt` | Documented, intentional deviations |
| Baseline | `misra/baseline.md` | Version history of MISRA counts |
| Raw XML | `misra_report/cppcheck_stderr.txt` | cppcheck output (XML) |
| Summary | `misra_report/summary.md` | Aggregated rule counts |
| Impact | `misra_report/impact.md` | Codegen source attribution |
| Impact CSV | `misra_report/impact.csv` | Machine-readable attribution |

---

## 15. Revision History

| Version | Date | Content |
|---------|------|---------|
| 1.0 | 2026-09-20 | Initial (summary) |
| 2.0 | 2026-09-20 | Detailed (per-module description, data flow added) |
| 2.1 | 2026-09-20 | **MISRA C:2012 compliance work**: §7.4 added (baseline history, suppressions, condition/action call split); §7.1 version column added; §11.2/11.5 updated; §12 C-21 added; §14.3 MISRA artifacts added |
```

---

