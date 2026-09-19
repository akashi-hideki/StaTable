# StaTable Overall Specification v2.0 (English, Detailed)

Version: 2.0
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
| `entry` | str | "" | Entry action |
| `exit` | str | "" | Exit action |
| `do` | str | "" | Do action |
| `description` | str | "" | Description |

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

#### 3.2.4 `Transition`

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
| `get_transitions_for_event(event) -> List[Transition]` | Get by event | – |

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

#### 3.5.2 XML Structure

```xml
<Project name="MyProject">
  <ProjectSettings>
    <CodeGeneration
      project_name="MyProject"
      table_type="array"
      generation_style="table_driven"
      os_type="non_rtos"
      folder_structure="by_type"
      include_dir_name="include"
      source_dir_name="src"
      common_dir_name="common"
      project_dir_name="project"
      generate_super_include="true"
      super_include_file="statable_all.h"
      max_consecutive_pending_events="16"
      external_includes_in_super="true"
      external_includes_in_role="true"
      external_includes_in_transitions="false"
      external_includes_in_common="false">
      <ExternalIncludes>
        <Include name="..."/>
      </ExternalIncludes>
    </CodeGeneration>
  </ProjectSettings>
  <GlobalDefinitions>
    <CustomTypes>...</CustomTypes>
    <SystemVariables>...</SystemVariables>
    <EventFlags>...</EventFlags>
    <Interrupts>
      <Interrupt name="..." description="..." event_names="..." is_timer="..." title="...">
        <Action condition="..." action="..."/>
        <UsedRoleFunction ref="Driver.Init"/>
        <UsedVariable name="counter"/>
      </Interrupt>
    </Interrupts>
    <DevicePlaceholders>...</DevicePlaceholders>
    <TimerBase>
      <Timer variable_name="..." unit="..." data_type="..." title="..." interrupt_name="...">
        <Derived period_name="..." multiplier="..." variable_name="..." data_type="..." title="..."/>
      </Timer>
    </TimerBase>
    <ExtraTimers>...</ExtraTimers>
    <EventQueues>
      <Queue name="..." size="..." element_type="..." event_ids="..." ... />
    </EventQueues>
  </GlobalDefinitions>
  <SharedLibraries>
    <RoleFunctionLibrary>...</RoleFunctionLibrary>
    <ConditionLibrary>...</ConditionLibrary>
    <LiteralLibrary>...</LiteralLibrary>
  </SharedLibraries>
  <Tab name="Application">
    <StateMachine initial="..." layer_priority="5" layer_name="Application">
      <States>...</States>
      <Events>...</Events>
      <RoleFunctions>
        <RoleFunction name="Init" namespace="Driver" .../>
      </RoleFunctions>
      <Transitions>
        <Transition source="..." event="..." condition="..." target="..." has_else="true" else_target="...">
          <PreAction action="..."/>
          <ElseAction action="..."/>
        </Transition>
      </Transitions>
    </StateMachine>
  </Tab>
</Project>
```

#### 3.5.3 Legacy Migration

If a `RoleFunction` has no `namespace` and `name` has a `<layer>_` prefix, the namespace is automatically separated.

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

#### 4.2.1 Main Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `logger` | StaTableLogger | Logger |
| `prefs` | Preferences | App preferences |
| `config_manager` | ConfigManager | Code generation config |
| `global_defs` | GlobalDefinitions | Global definitions |
| `role_function_library` | RoleFunctionLibrary | Shared library |
| `condition_library` | ConditionLibrary | Condition library |
| `literal_library` | LiteralLibrary | Literal library |
| `tab_widget` | QTabWidget | Tabs |
| `traceball` | TraceBallWidget | Log display |

#### 4.2.2 Main Methods

| Method | Description |
|--------|-------------|
| `create_toolbar()` | Build toolbar |
| `create_menus()` | Build menus |
| `add_state_machine_tab(name, sm)` | Add tab |
| `close_tab(index)` | Close tab |
| `rename_tab_at(index)` | Rename tab |
| `open_project()` | Load XML |
| `save_project()` | Save XML |
| `open_code_generation_dialog()` | Open generation dialog |
| `save_generated_code_direct()` | Direct save |
| `open_validation_dialog()` | Validation |
| `_get_all_layers() -> List[(name, sm)]` | Collect all layers (priority order) |

### 4.3 `StateMachineTab`

| Method | Description |
|--------|-------------|
| `__init__(sm, gd, lib..., parent)` | Initialization |
| `update_mermaid()` | Apply settings + update Mermaid |

**Layout**: QSplitter (left: MatrixTable + Mermaid, right: SettingsPanel)

### 4.4 `MatrixTableWidget`

| Method | Description |
|--------|-------------|
| `populate()` | Rebuild transition matrix |
| `open_transition_dialog(row, col)` | Launch D&D editor |
| `keyPressEvent(event)` | Enter/F2: edit, Delete: remove |
| `_find_transitions(state, event)` | Get cell transitions |
| `_generate_cell_label(trans, event)` | Cell display string |

### 4.5 `CodeGenerationDialog`

| Method | Description |
|--------|-------------|
| `_load_saved_settings()` | Load `codegen_settings.json` |
| `_save_settings()` | Save only 4 fields |
| `_generate_code()` | Run generation |
| `_save_code()` | Run save |
| `_show_warnings(records)` | Show warnings (deduplicated) |
| `_update_preview()` | Update preview |

**Attribute `all_layers`**: set externally by `MainWindow`.

### 4.6 `WarningCollector`

```python
class WarningCollector(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.records: List[str] = []
    def emit(self, record):
        if record.levelno >= logging.WARNING:
            try:
                msg = record.getMessage()
            except Exception:
                msg = str(record.msg)
            self.records.append(msg)
```

### 4.7 `ConditionBuilderDialog`

| Argument | Description |
|----------|-------------|
| `condition` | Existing condition expression |
| `event_name` | Event name |
| `global_defs` | Global definitions |
| `state_machine` | State machine |
| `literal_library` | Literal library |
| `states` | Target state candidates |
| `target_state` | Current target state |
| `else_target_state` | Current else target state |

| Getter | Description |
|--------|-------------|
| `get_condition_text()` | Condition expression |
| `get_event_name()` | Event name |
| `get_target_state()` | Target state |
| `get_else_target_state()` | else target state |
| `get_c_code_text()` | C code preview |

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

### 6.2 MIME Protocol

```
MIME_TYPE = "application/x-flow-item"
Payload   = {"item_type": "function"|"transition", "name": str}
```

### 6.3 Drop Rules

| Drop target | Treatment of `item_type=function` |
|-------------|-----------------------------------|
| `transition` | Append to parent transition's `pre_actions` |
| `pre_action` | Append to parent transition's `pre_actions` |
| `else` | Append to parent transition's `else_actions` |
| `else_action` | Append to parent transition's `else_actions` |
| Otherwise | Add as standalone `function` node |

`item_type=transition` always adds a new transition node.

### 6.4 `ActionDraft`

| Field | Type | Description |
|-------|------|-------------|
| `source` | str | Source state |
| `event` | str | Event name |
| `flow_items` | List[FlowItem] | Flow |
| `default_target` | str | Default target state |
| `system_globals` | List[SystemGlobal] | System globals |
| `generated_code` | str | Generated code |
| `role_func_map` | Dict[str, str] | Role function name map |
| `user_code` | Dict[str, str] | User code |

### 6.5 `FlowItem`

| Field | Type | Description |
|-------|------|-------------|
| `item_type` | str | `function` / `transition` / `pre_action` / `else` / `else_action` |
| `name` | str | Name |
| `edited_text` | str | Edited text |
| `params` | Dict | Parameters |
| `pos_x`, `pos_y` | Optional[float] | Position |

**Method**: `display_text() -> str`

### 6.6 Conversion Functions

| Function | Description |
|----------|-------------|
| `ensure_list(value) -> List[str]` | Normalize string/None/list |
| `transition_to_flow_item(trans) -> FlowItem` | Transition → FlowItem |
| `flow_item_to_transition(item, source, event) -> Transition` | FlowItem → Transition |

**Note**: `transition_to_flow_item` converts empty event to `"NewEvent"` (bug).

---

## 7. Code Generation (`codegen/`)

Refer to the separate **Deliverable #2 Detailed Specification v3.0**. Summary only.

### 7.1 Module List (16)

`c_code_generator.py`, `code_merger.py`, `code_templates.py`, `transition_generator.py`, `role_function_generator.py`, `struct_generator.py`, `enum_generator.py`, `variable_generator.py`, `event_queue_generator.py`, `interrupt_generator.py`, `timer_generator.py`, `osal_generator.py`, `type_mapper.py`, `naming_convention.py`, `config.py`, `sample_data.py`

### 7.2 Output Files (13)

`statable_types.h`, `statable_transitions.h/.c`, `statable_role_functions.h/.c`, `statable_init.c`, `statable_event_queue.c`, `statable_interrupt.c`, `statable_timer.c`, `osal.h/.c`, `statable_all.h`, `{project}_run.c`

### 7.3 Folder Structures

| Structure | Layout |
|-----------|--------|
| `flat` | All files in one directory |
| `by_type` | `include/` / `src/` / `common/` |
| `by_layer` | Per-layer subdirectories + common at root |

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

---

## 9. Development Environment

### 9.1 Requirements

| Item | Version |
|------|---------|
| Python | 3.12 |
| PySide6 | Latest |
| Git | Latest |
| OS | Windows 10/11 or Ubuntu 22.04+ |

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

---

## 11. Testing Policy

### 11.1 Test Suites

| File | Target |
|------|--------|
| `test_v2_2_p1.py` | Basic data model |
| `test_v2_2_p2.py` | StateMachine |
| `test_v2_2_p3.py` | GUI helpers |
| `test_v2_2_p4a.py` | Code generation (basics) |
| `test_v2_2_p4b.py` | Code generation (detailed) |
| `test_v2_2_p12_2.py` | Stage 2 features |
| `test_v2_2_p12_5.py` | Stage 5 features |
| `test_v2_2_p12_6.py` | Stage 6 features |
| `test_v2_2_p12_7.py` | Stage 7 features |
| `test_v2_2_p12_8.py` | Stage 8 features |
| `test_v2_2_p12_9.py` | Stage 9 features |
| `test_v2_2_p12_10.py` | Stage 10 features |

### 11.2 Execution Environment

- Local: works on Windows too
- CI: `ubuntu-latest` + `QT_QPA_PLATFORM=offscreen`

### 11.3 Verification Tools

- `tools/find_all_japanese.py`: non-ASCII detection
- `tools/verify_generated_code.py`: syntax and structure verification of generated C code

---

## 12. Known Constraints

| # | Item | Status | Impact |
|---|------|--------|--------|
| 1 | `generation_style` / `table_type` GUI switchable | Not implemented (forced) | Settings UI |
| 2 | `switch_case` generation | Not implemented (fallback) | `transition_generator` |
| 3 | `switch` / `dictionary` tables | Not implemented (fallback) | `transition_generator` |
| 4 | `external_includes_in_role/transitions/common` | Not implemented | `c_code_generator` |
| 5 | FreeRTOS / ThreadX OSAL | Include only | `osal_generator` |
| 6 | `super_include_dir` XML persistence | Not persisted (resets to default) | `xml_io` / `main_window` |
| 7 | Role function uniqueness mismatch | qualified vs pure name | `statable` / `libcntrl` |
| 8 | Empty event → `"NewEvent"` | Bug | `draft.transition_to_flow_item` |
| 9 | `palette_widget._add_function` import | No fallback | `palette_widget` |
| 10 | `project_dir_name` | Reserved, unused | `config` |
| 11 | `flow_widget.py` / `edit_dialogs.py` | Legacy | `transition_editor_direct` |
| 12 | `statable_gui/global_defs.py` | Actual role unclear | `statable_gui` |

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
│   └── tools/
├── docs/
│   ├── SPEC_OVERVIEW_ja.md
│   ├── SPEC_OVERVIEW_en.md
│   └── SPEC_CODEGEN_v3.md
└── README.md
```

### 14.2 Approximate File Sizes

| File | Approx. LOC |
|------|-------------|
| `codegen/c_code_generator.py` | ~1,400 |
| `codegen/role_function_generator.py` | ~900 |
| `codegen/code_templates.py` | ~700 |
| `statable_gui/main_window.py` | ~1,000 |
| `statable_gui/code_generation_dialog.py` | ~400 |
| `transition_editor_direct/canvas_widget.py` | ~450 |

---

## 15. Revision History

| Version | Date | Content |
|---------|------|---------|
| 1.0 | 2026-09-20 | Initial (summary) |
| 2.0 | 2026-09-20 | Detailed (per-module description, data flow added) |