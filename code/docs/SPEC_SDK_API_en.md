```markdown
# StaTable SDK API Reference

Version: 1.2 (English Master / Reviewed)
Date: 2026-09-22
Target: Tool vendor developers
License: MIT / Apache 2.0
Based on: StaTable v2.2.9 / v2.6.1

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [Data Model (Core API)](#3-data-model-core-api)
4. [Code Generation API](#4-code-generation-api)
5. [Validation API](#5-validation-api)
6. [MISRA Integration API](#6-misra-integration-api)
7. [Utility API](#7-utility-api)
8. [Error Codes](#8-error-codes)
9. [Limitations](#9-limitations)
10. [Appendix](#10-appendix)

---

## 1. Overview

### 1.1 Purpose

The StaTable SDK provides programmatic access to the state-transition design and C code generation engine used by the StaTable GUI application. It enables tool vendors to:

- Build custom state-machine design tools
- Generate embedded-targeted C code from state-transition models
- Validate models before generation (35 rules across 11 categories)
- Integrate MISRA C:2012 checking as an informational step
- Preserve user code across regenerations via marker-based merging

### 1.2 Target Audience

| User type | Intended use |
|-----------|--------------|
| Tool vendor developer | Integrate StaTable engine into a commercial tool |
| Embedded toolchain provider | Add state-machine code generation to an existing IDE |
| Framework developer | Build a domain-specific modeling layer on top of StaTable |

### 1.3 Feature Summary

| # | Feature | SDK Entry Point |
|---|---------|-----------------|
| F-01 | State machine construction | §3 `StateMachine` |
| F-02 | Global definitions | §3 `GlobalDefinitions` |
| F-03 | Project XML persistence | §7 `project_to_xml` / `project_from_xml` |
| F-04 | Mermaid diagram generation | §7 `generate_mermaid` |
| F-05 | C code generation (14 files) | §4 `CCodeGenerator` |
| F-06 | Marker-based user code preservation | §4 `CodeMerger` (via `save_generated_code_with_merge`) |
| F-07 | Model validation (35 rules) | §5 `CodeGenerationValidator` |
| F-08 | AI-assisted change application | §5 `ChangeApplier` |
| F-09 | MISRA C:2012 informational check | §6 CLI tools |
| F-10 | Cell-level actions and relations (v2.2) | §3 `ActionStep`, `TransitionRelation` |

### 1.4 Non-functional Requirements

| Item | Requirement |
|------|-------------|
| Python | 3.12 |
| OS | Windows 10/11, Linux (Ubuntu 22.04+) |
| External dependency | PySide6 (only for GUI modules; core SDK is GUI-free) |
| MISRA checker | cppcheck 2.x + MISRA addon (optional, CLI only) |
| License | MIT / Apache 2.0 |

### 1.5 Terminology

| Term | Definition |
|------|------------|
| Layer | A state-machine group identified by tab name (`sm.layer_name`) |
| Cell | A (state, event) pair; the minimal unit of a transition function |
| Cell function | A `static` C function processing one cell |
| Cell action | v2.2: A transition-independent `ActionStep` attached to a cell |
| Cell relation | v2.2: A `TransitionRelation` between transitions in a cell |
| Role function | A C function called from transitions, conditions, or ISRs |
| Role function (design principle) | Layer-agnostic: does not depend on the calling layer. For layer-specific behavior, split into separate functions (see SPEC_OVERVIEW §3.2.7) |
| namespace | The owning layer or explicit namespace of a role function |
| qualified_name | Unique name in `namespace.name` form (e.g., `Driver.Init`) |
| call_sites | The list of calling cells for each role function |
| transition_id | Index within call_sites. `0xFFFF` = no match |
| `used_global_vars` | v3.8: List of SystemVariable names referenced by a role function |
| `used_events` | v3.8: List of Event names referenced by a role function |
| `used_literals` | v3.8: List of literal names referenced by a role function |
| `layer_names_provider` | v3.11: Callable returning all tab names (namespace combo candidates) |
| Reserved fields | v3.7 / v1.5: `return_type` / `arg1_*` / `arg2_*` / `do` — not exposed in UI, preserved through XML |
| Super include | `statable_all.h`. Aggregates all generated headers |
| Super loop | `{project}_run.c`. Main loop for all layers |
| Marker | Comment used for user-code preservation (`[[STABLE_...]]`) |
| Commit | v2.2: `early_return=True` (stops evaluating later transitions in a cell) |
| Tentative | v2.2: `early_return=False` (later transitions may overwrite) |
| MISRA suppression | A documented, intentional deviation from MISRA C:2012 |

---

## 2. Quick Start

### 2.1 Minimal Example

```python
from statable import StateMachine, State, Event, Transition, GlobalDefinitions
from codegen.c_code_generator import CCodeGenerator
from codegen.config import CodeGenerationConfig

# 1. Build a StateMachine
sm = StateMachine()
sm.layer_name = "Application"
sm.layer_priority = 5

sm.add_state(State(name="Idle", entry=["Driver.IdleEntry"]))
sm.add_state(State(name="Running"))
sm.add_event(Event(name="START"))
sm.set_initial("Idle")

sm.add_transition(Transition(
    source="Idle", event="START", target="Running",
    condition="mode == MODE_AUTO", early_return=True, label="T1",
))

# 2. Build GlobalDefinitions
gd = GlobalDefinitions()

# 3. Configure code generation
config = CodeGenerationConfig(
    project_name="Demo",
    folder_structure="by_type",
    output_directory="./output",
)
gen = CCodeGenerator(config=config)

# 4. Generate all layers
files = gen.generate_all_layers(
    layers=[("Application", sm)],
    global_defs=gd,
)

# 5. Save with marker-based merge
saved = gen.save_generated_code_with_merge(files, "./output")
print(f"{len(saved)} files saved")
```

### 2.2 Multi-layer Example

```python
layers = [
    ("Application", sm_app),
    ("Driver", sm_driver),
    ("Middleware", sm_mw),
]
files = gen.generate_all_layers(layers, gd)
# Layers are sorted internally by layer_priority (ascending)
```

### 2.3 With Validation

```python
from codegen.validate.validator import CodeGenerationValidator

validator = CodeGenerationValidator()
result = validator.validate(sm, gd)

if not result.passed:
    for issue in result.get_errors():
        print(f"[{issue.category}] {issue.code}: {issue.message}")
```

### 2.4 XML Round-trip

```python
from statable.xml_io import project_to_xml, project_from_xml

project_to_xml(
    tabs=[("Application", sm)],
    global_defs=gd,
    filepath="project.xml",
    project_settings={"project_name": "Demo"},
)

tabs, gd2, role_lib, cond_lib, lit_lib, settings = project_from_xml("project.xml")
```

### 2.5 GUI Integration

```python
from statable_gui.code_generation_dialog import CodeGenerationDialog

dialog = CodeGenerationDialog(
    state_machine=sm,
    global_defs=gd,
    role_function_library=role_lib,
)
dialog.all_layers = [("Application", sm)]
dialog.exec()
files = dialog.get_generated_files()
```

**Note**: GUI modules require PySide6. The core SDK (§3, §4, §5, §6, §7) has no PySide6 dependency.

---

## 3. Data Model (Core API)

### 3.1 Enums

#### 3.1.1 `StateType`

```python
from statable import StateType

class StateType(Enum):
    NORMAL     = "normal"
    CONCURRENT = "concurrent"
    REGION     = "region"
    INITIAL    = "initial"
    FINAL      = "final"
    CHOICE     = "choice"
    JUNCTION   = "junction"
```

| Member | Value | Description |
|--------|-------|-------------|
| `NORMAL` | `"normal"` | Normal state (default) |
| `CONCURRENT` | `"concurrent"` | Concurrent state |
| `REGION` | `"region"` | Concurrent region |
| `INITIAL` | `"initial"` | Initial pseudo-state |
| `FINAL` | `"final"` | Final state |
| `CHOICE` | `"choice"` | Choice pseudo-state |
| `JUNCTION` | `"junction"` | Junction pseudo-state |

#### 3.1.2 `EventKind`

```python
from statable import EventKind

class EventKind(Enum):
    SIGNAL = "signal"
    CALL   = "call"
    TIME   = "time"
    CHANGE = "change"
```

| Member | Value |
|--------|-------|
| `SIGNAL` | `"signal"` |
| `CALL` | `"call"` |
| `TIME` | `"time"` |
| `CHANGE` | `"change"` |

#### 3.1.3 `EventDeliveryType`

```python
from statable import EventDeliveryType

class EventDeliveryType(Enum):
    DIRECT = "direct"
    QUEUE  = "queue"
    DOUBLE = "double"
```

| Member | Value | Description |
|--------|-------|-------------|
| `DIRECT` | `"direct"` | Direct delivery (default) |
| `QUEUE` | `"queue"` | Queued delivery |
| `DOUBLE` | `"double"` | Both direct and queued |

#### 3.1.4 `EventSourceLayer`

```python
from statable import EventSourceLayer

class EventSourceLayer(Enum):
    DRIVER     = "driver"
    MIDDLEWARE = "middleware"
```

### 3.2 `State` (dataclass)

```python
from statable import State, StateType

@dataclass
class State:
    name: str
    type: StateType = StateType.NORMAL
    parent: Optional[str] = None
    entry: List[str] = field(default_factory=list)
    exit: List[str] = field(default_factory=list)
    do: str = ""
    description: str = ""
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | `str` | ○ | – | State name (key in `StateMachine.states`) |
| `type` | `StateType` | – | `NORMAL` | State kind |
| `parent` | `Optional[str]` | – | `None` | Parent state (hierarchy) |
| `entry` | `List[str]` | – | `[]` | Entry actions (v2.2: `str` → `List[str]`) |
| `exit` | `List[str]` | – | `[]` | Exit actions (v2.2) |
| `do` | `str` | – | `""` | Do action |
| `description` | `str` | – | `""` | Description |

**`__post_init__` behavior**: Auto-normalization
- `None` → `[]`
- `""` → `[]`
- `"func"` → `["func"]`
- `List` → preserved

### 3.3 `Event` (dataclass)

```python
from statable import Event, EventKind, EventDeliveryType, EventSourceLayer

@dataclass
class Event:
    name: str
    id: Optional[int] = None
    kind: EventKind = EventKind.SIGNAL
    params: List[str] = field(default_factory=list)
    priority: int = 0
    description: str = ""
    delivery_type: EventDeliveryType = EventDeliveryType.DIRECT
    source_layer: EventSourceLayer = EventSourceLayer.DRIVER
    data_type: str = ""
    data_name: str = ""
    title: str = ""
```

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `name` | `str` | ○ | – |
| `id` | `Optional[int]` | – | `None` |
| `kind` | `EventKind` | – | `SIGNAL` |
| `params` | `List[str]` | – | `[]` |
| `priority` | `int` | – | `0` |
| `description` | `str` | – | `""` |
| `delivery_type` | `EventDeliveryType` | – | `DIRECT` |
| `source_layer` | `EventSourceLayer` | – | `DRIVER` |
| `data_type` | `str` | – | `""` |
| `data_name` | `str` | – | `""` |
| `title` | `str` | – | `""` |

**Note**: `name == ""` represents a completion transition.

### 3.4 `Transition` (dataclass, kw_only)

```python
from statable import Transition

@dataclass(kw_only=True)
class Transition:
    source: str
    event: str
    condition: str = ""
    pre_actions: List[str] = field(default_factory=list)
    target: str = ""
    has_else: bool = True
    else_target: str = ""
    else_actions: List[str] = field(default_factory=list)
    early_return: bool = False
    label: str = ""
    action: str = ""
    transition_type: str = "external"
    title: str = ""
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `source` | `str` | ○ | – | Source state name |
| `event` | `str` | ○ | – | Event name (`""` = completion) |
| `condition` | `str` | – | `""` | C condition expression |
| `pre_actions` | `List[str]` | – | `[]` | Pre-transition actions |
| `target` | `str` | – | `""` | Target state |
| `has_else` | `bool` | – | `True` | Whether else clause exists |
| `else_target` | `str` | – | `""` | Else target state |
| `else_actions` | `List[str]` | – | `[]` | Else actions |
| `early_return` | `bool` | – | `False` | v2.2: Commit if True |
| `label` | `str` | – | `""` | v2.2: Cell-internal label (T1, T2, ...) |
| `action` | `str` | – | `""` | Legacy field (unused) |
| `transition_type` | `str` | – | `"external"` | Transition type |
| `title` | `str` | – | `""` | Display name |

**v1.6 change**: `kw_only=True`.
**v2.2 additions**: `early_return`, `label`.

### 3.5 `ActionStep` (dataclass, kw_only, v2.2)

```python
from statable import ActionStep

@dataclass(kw_only=True)
class ActionStep:
    role_function: str = ""
    trigger: str = "before_transitions"
    title: str = ""
```

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `role_function` | `str` | – | `""` |
| `trigger` | `str` | – | `"before_transitions"` |
| `title` | `str` | – | `""` |

**`trigger` values**: `"before_transitions"` / `"after_transitions"`.

**`__post_init__`**: `title` is auto-filled with `role_function` (or `"(untitled action)"` if empty).

### 3.6 `TransitionRelation` (dataclass, kw_only, v2.2)

```python
from statable import TransitionRelation

@dataclass(kw_only=True)
class TransitionRelation:
    kind: str = "sequential"
    members: List[str] = field(default_factory=list)
    shared_condition: str = ""
    note: str = ""
    children: List["TransitionRelation"] = field(default_factory=list)
```

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `kind` | `str` | – | `"sequential"` |
| `members` | `List[str]` | – | `[]` |
| `shared_condition` | `str` | – | `""` |
| `note` | `str` | – | `""` |
| `children` | `List[TransitionRelation]` | – | `[]` |

**`kind` values**: `"sequential"` / `"exclusive"` / `"group"`.

### 3.7 `RoleFunction` (dataclass, kw_only)

```python
from statable import RoleFunction

@dataclass(kw_only=True)
class RoleFunction:
    name: str
    namespace: str = ""
    description: str = ""
    return_type: str = "void"
    arg1_type: str = ""
    arg1_name: str = ""
    arg2_type: str = ""
    arg2_name: str = ""
    title: str = ""
    # [v3.8] GUI symbol tracking (mirrors libcntrl.RoleFunction).
    # Persisted in XML; not consumed by codegen.
    used_global_vars: List[str] = []
    used_events: List[str] = []
    used_literals: List[str] = []
```

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `name` | `str` | ○ | – |
| `namespace` | `str` | – | `""` |
| `description` | `str` | – | `""` |
| `return_type` | `str` | – | `"void"` |
| `arg1_type` | `str` | – | `""` |
| `arg1_name` | `str` | – | `""` |
| `arg2_type` | `str` | – | `""` |
| `arg2_name` | `str` | – | `""` |
| `title` | `str` | – | `""` |
| `used_global_vars` | `List[str]` | – | `[]` |
| `used_events` | `List[str]` | – | `[]` |
| `used_literals` | `List[str]` | – | `[]` |

**Properties**

| Name | Type | Description |
|------|------|-------------|
| `qualified_name` | `str` | `namespace.name` or `name` |

**Class method**: `from_legacy_name(legacy_name, layer_names=None) -> RoleFunction`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `legacy_name` | `str` | ○ | e.g., `"Driver_Init"` |
| `layer_names` | `Optional[List[str]]` | – | Prefix-separation names |

**Example**:

```python
rf = RoleFunction.from_legacy_name("Driver_Init", ["Driver", "App"])
# rf.namespace == "Driver", rf.name == "Init"
```

**`__post_init__` behavior**: If `title` is empty, it is auto-filled with `f"Role function: {qualified_name}"`.

**Note**: This class is distinct from `statable_gui.libcntrl.role_function_library.RoleFunction` (see §5.3 and §7.5.2).

### 3.8 `GlobalDefinitions`

#### 3.8.1 Dataclasses

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

#### 3.8.2 `GlobalDefinitions` class

```python
from statable import GlobalDefinitions

class GlobalDefinitions:
    def __init__(self) -> None: ...

    # Attributes
    variables: List[SystemVariable]
    flags: List[EventFlag]
    interrupts: List[InterruptHandlerDef]
    placeholders: List[DevicePlaceholderDef]
    timer_base: TimerBaseDef
    extra_timers: List[TimerBaseDef]
    event_queues: List[EventQueueDef]
    custom_types: List[CustomTypeDef]

    # Methods
    def add_timer_variables(self) -> None: ...
    def variable_groups(self) -> List[str]: ...
    def flag_groups(self) -> List[str]: ...
    def custom_type_names(self) -> List[str]: ...
```

**`add_timer_variables`**: Synchronizes timer definitions into `variables`. Existing variables preserve `description` / `title`; only `type` / `unit` are overwritten.

### 3.9 `StateMachine`

```python
from statable import StateMachine

class StateMachine:
    def __init__(self) -> None: ...

    # Attributes
    states: Dict[str, State]
    events: Dict[str, Event]
    transitions: List[Transition]
    role_functions: Dict[str, RoleFunction]
    initial_state: Optional[str]
    layer_priority: int
    layer_description: str
    layer_name: str
    cell_actions: Dict[Tuple[str, str], List[ActionStep]]
    cell_relations: Dict[Tuple[str, str], List[TransitionRelation]]
```

#### Methods

| Method | Signature | Exception |
|--------|-----------|-----------|
| `add_state` | `(state: State) -> None` | `ValueError` on duplicate name |
| `add_event` | `(event: Event) -> None` | `ValueError` on duplicate name |
| `remove_event` | `(name: str) -> None` | – |
| `add_transition` | `(trans: Transition) -> None` | `ValueError` if source/target/event undefined |
| `remove_transition` | `(trans: Transition) -> None` | – |
| `set_initial` | `(state_name: str) -> None` | `ValueError` if undefined |
| `add_role_function` | `(rf: RoleFunction) -> None` | `ValueError` on duplicate `rf.name` |
| `remove_role_function` | `(name: str) -> None` | – |
| `get_transitions_for_cell` | `(source: str, event: str) -> List[Transition]` | – |
| `get_transitions_for_event` | `(event: str) -> List[Transition]` | – |
| `get_actions_for_cell` | `(source: str, event: str) -> List[ActionStep]` | – |
| `set_actions_for_cell` | `(source: str, event: str, actions: List[ActionStep]) -> None` | – |
| `get_relations_for_cell` | `(source: str, event: str) -> List[TransitionRelation]` | – |
| `set_relations_for_cell` | `(source: str, event: str, relations: List[TransitionRelation]) -> None` | – |
| `get_cell_keys` | `() -> List[Tuple[str, str]]` | – |
| `remove_cell_metadata` | `(source: str, event: str) -> None` | – |

**Important**: `add_role_function` keys by `rf.name` (bare name). `Driver.Init` and `App.Init` collide. See §9 L-24.

---

## 4. Code Generation API

### 4.1 `CCodeGenerator`

Module version: **v2.2.9**.

```python
from codegen.c_code_generator import CCodeGenerator

class CCodeGenerator:
    def __init__(self, config: Optional[CodeGenerationConfig] = None) -> None: ...
```

#### Class Constants

| Constant | Type | Description |
|----------|------|-------------|
| `FILE_STEPS` | `Dict[str, List[Dict]]` | Step table per file |
| `STRUCT_KIND_DISPATCH` | `Dict[str, str]` | Struct kind → generator method |
| `FILE_DISPATCH` | `Dict[str, str]` | File → generator method |
| `FILE_CATEGORY` | `Dict[str, str]` | File → category (`include` / `src` / `common`) |
| `FOLDER_STRUCTURE_RESOLVERS` | `Dict[str, str]` | Structure → path resolver |
| `LAYER_SPECIFIC_FILES` | `Set[str]` | 5 files (per-layer suffix) |
| `COMMON_FILES` | `Set[str]` | 8 files (shared) |

**`LAYER_SPECIFIC_FILES`**: `statable_types.h`, `statable_transitions.h`, `statable_transitions.c`, `statable_role_functions.h`, `statable_role_functions.c`.

#### Public Methods

| Method | Signature |
|--------|-----------|
| `get_config` | `() -> CodeGenerationConfig` |
| `set_config` | `(config: CodeGenerationConfig) -> None` |
| `update_config` | `(**kwargs) -> None` |
| `reset_config` | `() -> None` |
| `generate_all` | `(state_machine, global_defs, role_function_library=None) -> Dict[str, str]` |
| `generate_file` | `(filename, state_machine, global_defs, role_function_library=None) -> str` |
| `generate_all_layers` | `(layers, global_defs, role_function_library=None) -> Dict[str, str]` |
| `save_generated_code` | `(generated_files: Dict[str, str], output_dir: str, layer_name: str = '') -> List[str]` |
| `save_generated_code_with_merge` | `(generated_files, output_dir, layer_name='') -> List[str]` |
| `get_merge_summary` | `(generated_files, output_dir, layer_name='') -> Dict[str, Dict[str, int]]` |
| `get_generated_file_list` | `() -> List[str]` |

**Exceptions**

| Exception | Condition |
|-----------|-----------|
| `ValueError` | `generate_file` with unknown filename |
| `OSError` | `save_generated_code` write failure |

### 4.2 `CodeGenerationConfig`

```python
from codegen.config import CodeGenerationConfig

@dataclass
class CodeGenerationConfig:
    generation_style: str = "table_driven"
    table_type: str = "array"
    os_type: str = "non_rtos"
    naming_prefix: str = ""
    state_prefix: str = "STATE"
    event_prefix: str = "EVENT"
    flag_prefix: str = "FLAG"
    enable_debug_logs: bool = True
    enable_info_logs: bool = True
    enable_error_logs: bool = True
    enable_comments: bool = True
    enable_doxygen: bool = True
    enable_user_markers: bool = True
    output_directory: str = ""
    save_with_merge: bool = True
    project_name: str = "MyProject"
    folder_structure: str = "by_type"
    include_dir_name: str = "include"
    source_dir_name: str = "src"
    common_dir_name: str = "common"
    project_dir_name: str = "project"
    generate_super_include: bool = True
    super_include_file: str = "statable_all.h"
    super_include_dir: str = "common"
    external_includes: List[str] = field(default_factory=list)
    external_includes_in_super: bool = True
    external_includes_in_role: bool = True
    external_includes_in_transitions: bool = False
    external_includes_in_common: bool = False
    max_consecutive_pending_events: int = 16
```

**Methods**

| Method | Description |
|--------|-------------|
| `to_dict() -> Dict` | Serialize |
| `from_dict(data: Dict) -> CodeGenerationConfig` | Deserialize (unknown keys ignored) |

### 4.3 `ConfigManager`

```python
from codegen.config import ConfigManager

class ConfigManager:
    def __init__(self) -> None: ...
    def get_config(self) -> CodeGenerationConfig: ...
    def set_config(self, config: CodeGenerationConfig) -> None: ...
    def update(self, **kwargs) -> None: ...
    def reset(self) -> None: ...
    def get_available_styles(self) -> Dict[str, str]: ...
    def get_available_table_types(self) -> Dict[str, str]: ...
    def get_available_os_types(self) -> Dict[str, str]: ...
    def get_available_folder_structures(self) -> Dict[str, str]: ...
```

### 4.4 Output Files (14)

| # | File | Category | Layer-specific |
|---|------|----------|----------------|
| 1 | `statable_types_common.h` | include | – |
| 2 | `statable_types.h` | include | ○ |
| 3 | `statable_transitions.h` | include | ○ |
| 4 | `statable_transitions.c` | src | ○ |
| 5 | `statable_role_functions.h` | include | ○ |
| 6 | `statable_role_functions.c` | src | ○ |
| 7 | `statable_init.c` | src | – |
| 8 | `statable_event_queue.c` | src | – |
| 9 | `statable_interrupt.c` | src | – |
| 10 | `statable_timer.c` | src | – |
| 11 | `osal.h` | common | – |
| 12 | `osal.c` | common | – |
| 13 | `statable_all.h` | common | – |
| 14 | `{project_name}_run.c` | src | – |

### 4.5 Folder Structures

| Structure | Layout |
|-----------|--------|
| `flat` | All files in one directory |
| `by_type` | `include/` / `src/` / `common/` |
| `by_layer` | `<layer_name>/` per-layer + common at root |

### 4.6 `CodeTemplates`

Template dictionary class (subclass to customize).

| Dictionary | Type | Purpose |
|-----------|------|---------|
| `STRINGS` | `Dict[str, str]` | Basic strings (section lines, log macros) |
| `SECTION_HEADERS` | `Dict[str, str]` | 25 section header names |
| `STRUCT_COMMENTS` | `Dict[str, Dict]` | Struct comments |
| `ENUM_COMMENTS` | `Dict[str, Dict]` | Enum comments |
| `TYPE_NAMES` | `Dict[str, str]` | Type names (`STATE_t`, `EVENT_t`, `FLAG_t`) |
| `FUNCTION_NAMES` | `Dict[str, str]` | Function name prefixes |
| `MACRO_NAMES` | `Dict[str, str]` | Macro names |
| `FORMATS` | `Dict[str, str]` | Format strings |
| `LAYER_TEMPLATES` | `Dict[str, str]` | Per-layer file templates |
| `COMMON_TYPES_TEMPLATES` | `Dict[str, str]` | `SystemContext_t` etc. |
| `ISR_TEMPLATES` | `Dict[str, str]` | ISR templates |
| `DEBUG_MESSAGES` | `Dict[str, str]` | Log message templates |
| `OSAL` | `Dict` | OSAL templates (os_types, header, source) |
| `SUPER_INCLUDE_TEMPLATES` | `Dict[str, str]` | `statable_all.h` |
| `SUPER_LOOP_TEMPLATES` | `Dict[str, str]` | Super loop |

### 4.7 `RoleFunctionGenerator`

Internal sub-generator. Module version: **v3.3**.

| Method | Signature |
|--------|-----------|
| `set_layer` | `(layer_name: str) -> None` |
| `generate_none_define` | `() -> str` |
| `generate_entry_struct` | `() -> str` |
| `generate_transition_id_prototype` | `() -> str` |
| `generate_transition_id_function` | `() -> str` |
| `generate_call_sites_table` | `(func, call_sites) -> str` |
| `generate_tail_user_section` | `() -> str` |
| `generate_declaration` | `(func) -> str` |
| `generate_implementation` | `(func, global_defs=None, call_sites=None, include_transition_id=True) -> str` |
| `generate_call` | `(func_name: str) -> str` |
| `generate_all_declarations` | `(role_functions: List) -> str` |
| `generate_all_implementations` | `(role_functions, state_machine=None, global_defs=None) -> str` |

### 4.8 `TransitionGenerator`

Internal sub-generator. Module version: **v2.6**.

| Method | Signature |
|--------|-----------|
| `set_layer` | `(layer_name: str) -> None` |
| `generate_transition_cell_functions` | `(state_machine) -> str` |
| `generate_transition_cell_prototypes` | `(state_machine) -> str` |
| `generate_transition_table` | `(state_machine, table_type=None) -> str` |
| `generate_transition_table_header` | `(state_machine) -> str` |
| `generate_function_dictionary` | `(state_machine) -> str` |
| `generate_process_function` | `(state_machine, generation_style=None) -> str` |
| `generate_get_next_event_function` | `(state_machine) -> str` |
| `generate_all` | `(state_machine) -> Dict[str, str]` |
| `generate_all_transitions` | `(state_machine, table_type='array', process_type='table_driven') -> str` |

**Role function call forms (MISRA 17.7)**:

| Form | Usage | Output |
|------|-------|--------|
| Condition | `Transition.condition`, `Relation.shared_condition` | `RoleFunc_X(transition, ctx)` |
| Action | `pre_actions`, `else_actions`, cell actions, entry/exit | `(void)RoleFunc_X(transition, ctx)` |

### 4.9 Internal Sub-generators (SDK-non-public)

The following 7 classes are used internally by `CCodeGenerator`. **Do not call directly** from SDK consumer code.

| Class | Module | Purpose |
|-------|--------|---------|
| `CStructGenerator` | `struct_generator.py` | Struct generation (v2.2.1) |
| `CEnumGenerator` | `enum_generator.py` | Enum generation (v1.5) |
| `VariableGenerator` | `variable_generator.py` | Variable macros + `SystemContext_Init` (v2.0) |
| `EventQueueGenerator` | `event_queue_generator.py` | Event queue |
| `InterruptGenerator` | `interrupt_generator.py` | ISR generation (H3) |
| `TimerGenerator` | `timer_generator.py` | Timer struct / Init / Update (v2.2) |
| `OSALGenerator` | `osal_generator.py` | OSAL header / source (v2.2) |

### 4.10 Auxiliary API

#### 4.10.1 `CTypeMapper`

All methods are classmethods.

```python
from codegen.type_mapper import CTypeMapper

CTypeMapper.map_type("uint32")           # -> "uint32_t"
CTypeMapper.get_type_category("uint32")  # -> "integer"
CTypeMapper.get_required_headers(["uint32", "bool"])
# -> ["#include <stdbool.h>", "#include <stdint.h>"]
```

#### 4.10.2 `CNamingConvention`

All methods are classmethods. Module version: **v2.2.5**.

| Method | Description |
|--------|-------------|
| `to_snake_case(name, upper=False)` | – |
| `to_upper_snake(name)` | `"myEvent"` → `"MY_EVENT"` |
| `to_lower_snake(name)` | `"MyEvent"` → `"my_event"` |
| `to_camel_case(name)` | `"my_event"` → `"myEvent"` |
| `to_pascal_case(name)` | `"my_event"` → `"MyEvent"` |
| `sanitize_identifier(name)` | Escape C keywords, replace symbols |
| `create_type_name(name)` | Idempotent `_t` suffix |
| `create_enum_value(prefix, name)` | – |
| `create_function_name(module, action)` | – |
| `create_variable_name(name)` | – |
| `create_macro_name(name)` | – |

**`create_type_name` idempotency**:
```
create_type_name("SystemStatus")     # -> "SystemStatus_t"
create_type_name("SystemStatus_t")   # -> "SystemStatus_t"
create_type_name("sensor_data")      # -> "SensorData_t"
create_type_name("")                 # -> "Unknown_t"
```

#### 4.10.3 `CodeMerger`

Marker-based merge. Module version: **v2.0**.

| Category | Methods |
|----------|---------|
| Extract | `extract_file_user_code`, `extract_func_user_code`, `extract_all_func_user_codes`, `extract_file_tail_user_code` |
| Inject | `inject_file_user_code`, `inject_func_user_code`, `inject_file_tail_user_code` |
| Merge | `merge_file`, `merge_all_files` |
| Query | `has_user_code`, `has_func_user_code`, `get_user_code_summary` |

See §7.4 for marker specification.

---

## 5. Validation API

### 5.1 `CodeGenerationValidator`

```python
from codegen.validate.validator import CodeGenerationValidator

class CodeGenerationValidator:
    VALIDATORS: Dict[str, Type] = {...}  # 11 entries

    def __init__(self) -> None: ...
    def validate(self, state_machine, global_defs) -> ValidationResult: ...
    def validate_category(self, category, state_machine, global_defs) -> List[ValidationIssue]: ...
    def get_categories(self) -> List[str]: ...
```

**Registered validators (11)**

| Category | Class |
|----------|-------|
| `state` | `StateValidator` |
| `event` | `EventValidator` |
| `transition` | `TransitionValidator` |
| `role_function` | `RoleFunctionValidator` |
| `variable` | `VariableValidator` |
| `flag` | `FlagValidator` |
| `queue` | `QueueValidator` |
| `interrupt` | `InterruptValidator` |
| `timer` | `TimerValidator` |
| `custom_type` | `CustomTypeValidator` |
| `cell` | `CellValidator` (v2.2) |

**Behavior**: Each validator is executed in insertion order. Per-category exceptions are caught and logged via `logger.error`; processing continues.

### 5.2 Data Model

#### 5.2.1 `ValidationSeverity`

```python
class ValidationSeverity(Enum):
    ERROR   = "error"
    WARNING = "warning"
    INFO    = "info"

    @classmethod
    def from_string(cls, value: str) -> 'ValidationSeverity'
```

**`from_string`**: Case-insensitive. Unknown values → `INFO`.

#### 5.2.2 `ValidationIssue`

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `category` | `str` | ○ | – |
| `code` | `str` | ○ | – |
| `message` | `str` | ○ | – |
| `severity` | `ValidationSeverity` | ○ | – |
| `target` | `str` | – | `""` |
| `suggestion` | `str` | – | `""` |
| `details` | `Dict[str, Any]` | – | `{}` |

**Methods**: `to_dict`, `from_dict`, `__str__`.

#### 5.2.3 `ValidationResult`

| Field | Type | Description |
|-------|------|-------------|
| `issues` | `List[ValidationIssue]` | All issues |

**Properties**: `passed` (True if `error_count == 0`), `error_count`, `warning_count`, `info_count`.

**Methods**: `get_errors`, `get_warnings`, `get_infos`, `get_by_category`, `to_dict`, `from_dict`.

**Note**: Only `ERROR` affects `passed`. Warnings and infos do not.

#### 5.2.4 `ValidationContext`

| Field | Type | Description |
|-------|------|-------------|
| `state_machine` | `Any` | Target `StateMachine` or `None` |
| `global_defs` | `Any` | Target `GlobalDefinitions` or `None` |

**Proxy properties** (returns empty when `None`):

- SM: `states`, `events`, `transitions`, `role_functions`, `initial_state`
- GD: `variables`, `flags`, `event_queues`, `interrupts`, `custom_types`, `timer_base`, `extra_timers`

**Note**: `cell_actions` / `cell_relations` proxies are not implemented; `CellValidator` accesses `state_machine` directly.

### 5.3 `BaseValidator`

```python
from codegen.validate.items.base_validator import BaseValidator

class BaseValidator:
    category: str = ""
    rules: Dict[str, Callable] = {}

    def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        ...
```

**Subclass convention**:

```python
class MyValidator(BaseValidator):
    category = "my_category"
    rules = {
        "MY_CODE_1": _check_1,
        "MY_CODE_2": _check_2,
    }
```

**Two implementation patterns observed in the codebase**:

- **Pattern A (10 validators)**: Override `validate()` for per-rule `try/except`, and use `_create_issue(code, **kwargs)` that pulls `message` / `severity` / `suggestion` from `VALIDATION_RULES`.
- **Pattern B (1 validator: `CellValidator`)**: Do **not** override `validate()`; use `_make_issue(code, message, target)` with a hard-coded message string. `suggestion` is not set. See §9 L-21 / L-30.

### 5.4 Item Validators (35 rules)

| Category | Rules |
|----------|-------|
| `state` | `STATE_NO_INITIAL`, `STATE_UNREACHABLE`, `STATE_NO_TRANSITION`, `STATE_DUPLICATE` |
| `event` | `EVENT_UNUSED`, `EVENT_NO_TRANSITION` |
| `transition` | `TRANSITION_TARGET_UNDEFINED`, `TRANSITION_EVENT_UNDEFINED`, `TRANSITION_SOURCE_UNDEFINED`, `TRANSITION_DUPLICATE`, `TRANSITION_SELF_LOOP` |
| `role_function` | `ROLE_FUNC_NO_RETURN_TYPE`, `ROLE_FUNC_ARG_MISMATCH`, `ROLE_FUNC_UNUSED` |
| `variable` | `VAR_DUPLICATE_NAME`, `VAR_INVALID_TYPE`, `VAR_INVALID_ARRAY_SIZE` |
| `flag` | `FLAG_DUPLICATE_NAME`, `FLAG_INVALID_RANGE` |
| `queue` | `QUEUE_INVALID_SIZE`, `QUEUE_UNDEFINED_EVENT` |
| `interrupt` | `INTERRUPT_DUPLICATE_NAME`, `INTERRUPT_UNDEFINED_EVENT` |
| `timer` | `TIMER_DUPLICATE_VARIABLE`, `TIMER_INVALID_MULTIPLIER` |
| `custom_type` | `TYPE_DUPLICATE_NAME`, `TYPE_NO_MEMBERS` |
| `cell` | `CELL_EMPTY_CONDITION`, `CELL_DUPLICATE_LABEL`, `CELL_DANGLING_RELATION`, `CELL_UNREACHABLE_TRANSITION`, `CELL_OVERLAP_POSSIBLE`, `CELL_DUPLICATE_TARGET`, `CELL_EXCLUSIVE_NO_RETURN`, `CELL_EMPTY_TARGET` |

**Note on `ROLE_FUNC_UNUSED`**: The implementation checks only `Transition.action` and `Transition.condition` (exact string match). In v2.2, `pre_actions` / `else_actions` / cell actions are **not** considered, so the rule may produce false positives when only v2.2 action fields are used. See §9 L-23.

**Note on `EventValidator` (v2.4.1)**: `EVENT_UNUSED` and `EVENT_NO_TRANSITION` are semantically duplicated. See §9 L-31.

### 5.5 Severity Distribution

| Category | Error | Warning | Info |
|---------|------:|--------:|-----:|
| state | 1 | 3 | 0 |
| event | 0 | 2 | 0 |
| transition | 3 | 1 | 1 |
| role_function | 2 | 1 | 0 |
| variable | 2 | 1 | 0 |
| flag | 1 | 1 | 0 |
| queue | 1 | 1 | 0 |
| interrupt | 1 | 1 | 0 |
| timer | 2 | 0 | 0 |
| custom_type | 1 | 1 | 0 |
| cell | 2 | 4 | 2 |
| **Total** | **16** | **16** | **3** |

### 5.6 AI Diagnostics

#### 5.6.1 `AIPromptGenerator`

```python
from codegen.validate.prompt_generator import AIPromptGenerator

class AIPromptGenerator:
    def __init__(self) -> None: ...
    def generate_diagnosis_prompt(self, sm, gd, validation_result=None) -> str: ...
```

#### 5.6.2 `AIResponseParser`

```python
from codegen.validate.response_parser import AIResponseParser

class AIResponseParser:
    ACTION_MAPPING: Dict[str, ChangeActionType]  # 10 legacy actions only

    def parse(self, text: str) -> List[ChangeRequest]: ...
    def parse_json_response(self, text: str) -> List[ChangeRequest]: ...
    def parse_text_response(self, text: str) -> List[ChangeRequest]: ...
```

**Limitation**: v2.2 cell-level actions are **not** parsed. See §9 L-18.

### 5.7 Change Application

#### 5.7.1 `ChangeActionType` (17 values)

**Legacy (10)**: `SET_INITIAL`, `ADD_TRANSITION`, `ADD_STATE`, `ADD_EVENT`, `REMOVE_TRANSITION`, `UPDATE_TRANSITION`, `ADD_ROLE_FUNCTION`, `REMOVE_ROLE_FUNCTION`, `ADD_VARIABLE`, `ADD_FLAG`.

**v2.2 cell-level (7)**: `ADD_CELL`, `REMOVE_CELL`, `ADD_ACTION_STEP`, `REMOVE_ACTION_STEP`, `ADD_TRANSITION_RELATION`, `REMOVE_TRANSITION_RELATION`, `SET_EARLY_RETURN`.

#### 5.7.2 `ChangeRequest`

| Field | Type | Default |
|-------|------|---------|
| `action` | `ChangeActionType` | – |
| `params` | `Dict[str, Any]` | `{}` |
| `reason` | `str` | `""` |
| `source` | `str` | `"ai"` |

#### 5.7.3 `ChangeApplier`

```python
from codegen.validate.change_applier import ChangeApplier

class ChangeApplier:
    def __init__(self, sm, gd) -> None: ...
    def apply(self, change: ChangeRequest) -> Tuple[bool, str]: ...
    def apply_all(self, changes: List[ChangeRequest]) -> Dict: ...
```

**`apply_all` return**:

```python
{
    'total': int,
    'applied': int,
    'failed': int,
    'results': List[{'change': ChangeRequest, 'success': bool, 'message': str}],
}
```

**Note (v2.4.1 / C-28)**: `_add_variable` and `_add_flag` now reject duplicate names and empty names. See §9 L-19.

---

## 6. MISRA Integration API

### 6.1 Overview

MISRA checking is performed by invoking **`cppcheck` + MISRA addon** as an external process. StaTable does not link against cppcheck.

| Item | Value |
|------|-------|
| Checker | `cppcheck` 2.x + `--addon=misra` |
| Output format | XML (`--xml --xml-version=2`) |
| Execution | CLI tools (Python 3.12) |
| Build failure | Never (informational only) |
| Prerequisite | `cppcheck` in `PATH` |

**Important**: `cppcheck + MISRA addon` is **not a certified MISRA checker**. StaTable uses the terms "supported" and "evaluated"; it does not claim "compliance".

### 6.2 CLI Tool 1: `tools/run_misra_check.py`

```bash
python tools/run_misra_check.py --root <DIR> --out <DIR> [--suppressions <FILE>]
```

**Arguments**

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--root` | `str` | ○ | – | Root directory of generated `.c` files |
| `--out` | `str` | ○ | – | Output directory |
| `--suppressions` | `str` | – | `misra/suppressions.txt` | Suppression list |

**Output**

| File | Content |
|------|---------|
| `summary.md` | MISRA rule counts + non-MISRA warnings + Next Steps |
| `cppcheck_raw.xml` | cppcheck stdout (XML) |
| `cppcheck_stderr.txt` | cppcheck stderr (may contain XML) |

**Exit codes**

| Code | Condition |
|------|-----------|
| 0 | Normal completion (even with violations) |
| 1 | Root missing / cppcheck unavailable / timeout |

### 6.3 CLI Tool 2: `tools/analyze_misra_impact.py`

```bash
python tools/analyze_misra_impact.py --xml <FILE> --out <FILE> [--csv <FILE>]
```

**Output**

| File | Content |
|------|---------|
| `<out>` | Impact analysis Markdown |
| `<csv>` | `codegen_source,rule_id,count` CSV |

**Mapping rules** (generated file → responsible codegen source):

| Generated pattern | Responsible codegen |
|-------------------|---------------------|
| `statable_role_functions` | `role_function_generator.py`, `code_templates.py` |
| `statable_transitions` | `transition_generator.py`, `code_templates.py` |
| `statable_types` | `struct_generator.py`, `enum_generator.py`, `variable_generator.py`, `code_templates.py` |
| `statable_init` | `variable_generator.py`, `c_code_generator.py` |
| `statable_event_queue` | `event_queue_generator.py` |
| `statable_interrupt` | `interrupt_generator.py` |
| `statable_timer` | `timer_generator.py` |
| `osal` | `osal_generator.py`, `code_templates.py` |
| `statable_all` | `c_code_generator.py` |
| `_run.c` | `c_code_generator.py` |

### 6.4 Suppression List

File: `misra/suppressions.txt`. One rule ID per line.

Current list (11 rules):

```
misra-c2012-2.3
misra-c2012-2.4
misra-c2012-2.5
misra-c2012-5.9
misra-c2012-8.4
misra-c2012-8.7
misra-c2012-8.9
misra-c2012-11.5
misra-c2012-15.5
misra-c2012-15.7
misra-c2012-18.4
```

**Suppression rationale** (all 11 rules):

| Rule | Rationale |
|------|-----------|
| `2.3` | Unused type declarations (reserved types) |
| `2.4` | Unused tags (struct tags) |
| `2.5` | Unused macros (reserved for future use) |
| `5.9` | Internal linkage identifier duplication (per-layer files) |
| `8.4` | Per-layer extern visibility; design decision to keep layer-crossing cooperation |
| `8.7` | External linkage function reference (cross-layer cooperation) |
| `8.9` | Object definition in a single translation unit (design decision) |
| `11.5` | bare-metal OSAL uses `void *` + `uint8_t *` casts to avoid `memcpy` |
| `15.5` | Single exit point not used (readability preferred) |
| `15.7` | `_handled` pattern: each `if` is an independent guard |
| `18.4` | OSAL queue pointer arithmetic (same as `11.5`) |

### 6.5 Current Baseline (v2.6.1)

| Metric | Value |
|--------|------:|
| MISRA hits | 10 |
| Distinct MISRA rules | 4 |
| Non-MISRA warnings | 9 |

**MISRA hits (all suppressed by design)**:

| Rule | Count |
|------|------:|
| `8.4` | 3 |
| `11.5` | 4 |
| `18.4` | 2 |
| `15.7` | 1 |

### 6.6 Baseline File

`misra/baseline.md` records:
- Recorded date
- StaTable version
- Source XML
- MISRA hits / distinct rules
- Top rules
- Action items

**Current status**: template only (no actual measurements recorded). See §9 L-13.

---

## 7. Utility API

### 7.1 `XmlIO` (Functions)

Module: `statable/xml_io.py`. **Function-based** (no class).

| Function | Signature |
|----------|-----------|
| `project_to_xml` | `(tabs, global_defs, filepath, role_function_library=None, condition_library=None, literal_library=None, project_settings=None) -> None` |
| `project_from_xml` | `(filepath) -> Tuple[List[Tuple[str, StateMachine]], GlobalDefinitions, Optional[RoleFunctionLibrary], Optional[ConditionLibrary], Optional[LiteralLibrary], dict]` |
| `state_machine_to_element` | `(sm: StateMachine) -> ET.Element` |
| `state_machine_from_element` | `(elem: ET.Element) -> StateMachine` |
| `global_defs_to_element` | `(gd: GlobalDefinitions) -> ET.Element` |
| `global_defs_from_element` | `(elem: ET.Element) -> GlobalDefinitions` |
| `role_function_library_to_element` | `(lib) -> Optional[ET.Element]` |
| `role_function_library_from_element` | `(elem) -> Optional[RoleFunctionLibrary]` |
| `condition_library_to_element` | `(lib) -> Optional[ET.Element]` |
| `condition_library_from_element` | `(elem) -> Optional[ConditionLibrary]` |
| `literal_library_to_element` | `(lib) -> Optional[ET.Element]` |
| `literal_library_from_element` | `(elem) -> Optional[LiteralLibrary]` |

**`project_settings` keys**:

| Key | Type | Default |
|-----|------|---------|
| `project_name` | `str` | `"MyProject"` |
| `table_type` | `str` | `"array"` |
| `generation_style` | `str` | `"table_driven"` |
| `os_type` | `str` | `"non_rtos"` |
| `folder_structure` | `str` | `"by_type"` |
| `include_dir_name` | `str` | `"include"` |
| `source_dir_name` | `str` | `"src"` |
| `common_dir_name` | `str` | `"common"` |
| `project_dir_name` | `str` | `"project"` |
| `generate_super_include` | `bool` | `True` |
| `super_include_file` | `str` | `"statable_all.h"` |
| `external_includes` | `List[str]` | `[]` |
| `external_includes_in_super` | `bool` | `True` |
| `external_includes_in_role` | `bool` | `True` |
| `external_includes_in_transitions` | `bool` | `False` |
| `external_includes_in_common` | `bool` | `False` |
| `max_consecutive_pending_events` | `int` | `16` |

**Note**: `super_include_dir` is **not persisted**. See §9 L-05.

**XML schema**: For the full XML structure (`<Project>`, `<StateMachine>`, `<Cells>`, etc.), see `SPEC_OVERVIEW_en.md` §3.5.2. This section documents only the Python API surface.

### 7.2 `MermaidGenerator` (Function)

Module: `statable/mermaid_gen.py`.

```python
from statable.mermaid_gen import generate_mermaid

mermaid: str = generate_mermaid(sm)
```

**Output format**:

```
stateDiagram-v2
    direction LR
    [*] --> InitialState
    Source --> Target : Title (Event) [Condition] [Commit]
    Source --> ElseTarget : (Event) else [Commit]
    note right of State : internal: Title (Event)
```

**Label rules**:

| Element | Condition | Output |
|---------|-----------|--------|
| Title | `title` is not `"(untitled transition)"` | `Startup` |
| Target | `title` empty | `Active` |
| `(internal)` | Both empty | `(internal)` |
| `(Event)` | `event` non-empty | `(START)` |
| `[Condition]` | `condition` non-empty (truncated to 50 chars) | `[err_code != 0]` |
| ` [Commit]` | `early_return == True` | – |

**Sanitization**: `:` → `-`, `[` → `(`, `]` → `)`, `"` → `'`, backtick → `'`, newlines → space.

### 7.3 `SampleData` (Functions)

Module: `statable/sample_data.py`.

| Function | Description |
|----------|-------------|
| `create_sample_state_machine() -> StateMachine` | 4 states, 5 events, 6 transitions, 9 role functions, 4 cell actions, 2 cell relations |
| `create_sample_global_defs() -> GlobalDefinitions` | 4 variables, 2 flags, 2 types, 1 interrupt, 2 timer groups, 1 queue |

### 7.4 Marker-based Merge Specification

Module: `codegen/code_merger.py` (`CodeMerger` class).

#### 7.4.1 Marker Types (4)

| # | Marker | Purpose | Placement |
|---|--------|---------|-----------|
| 1 | `[[STABLE_USER_CODE_START]]` / `END` | File-level user area | After includes |
| 2 | `[[STABLE_USER_CODE_START:<name>]]` / `END:<name>` | Function-level user area | Inside each role function / ISR |
| 3 | `[[STABLE_USER_CODE_TAIL_START]]` / `END` | File-tail user area | End of file |
| 4 | `[[STABLE_AUTO_GENERATED_START]]` / `END` | Auto-generated region (reserved) | – |

#### 7.4.2 Function-level Marker Naming

| Function | Marker name |
|----------|-------------|
| `RoleFunc_<NS>_<Name>` | `<NS>_<Name>` |
| `RoleFunc_<Name>` (no NS) | `<Name>` |
| `ISR_<Name>` | `<Name>` (no layer) |

**Extraction patterns**:

```python
FUNC_NAME_PATTERNS = [
    r'RoleFunc_(\w+)\s*\(',
    r'ISR_(\w+)\s*\(',
]
```

#### 7.4.3 Merge Flow

```
merge_file(generated_content, existing_content)
  ├── if existing_content is None/empty: return generated_content
  ├── 1. Extract user code
  │   ├── extract_file_user_code()
  │   ├── extract_all_func_user_codes()
  │   └── extract_file_tail_user_code()
  ├── 2. Inject into generated code
  │   ├── inject_file_user_code()
  │   ├── inject_func_user_code()  (per function)
  │   └── inject_file_tail_user_code()
  └── 3. Return merged content
```

**`inject_file_user_code` (v2.0)**: If an existing block is present, **replace its contents** (not insert new). If absent, insert after the last `#include`.

#### 7.4.4 `merge_all_files`

```python
def merge_all_files(
    self,
    generated_files: Dict[str, str],
    existing_dir: str,
    path_resolver: Optional[Callable] = None,
    layer_name: str = '',
) -> Dict[str, str]
```

`path_resolver(filename, layer_name) -> rel_path` is passed from `CCodeGenerator._resolve_output_path`.

### 7.5 Shared Libraries (`statable_gui/libcntrl/`)

**Note**: Requires PySide6.

#### 7.5.1 `RoleFunctionLibrary`

| Method | Signature |
|--------|-----------|
| `_key` | `(rf) -> str` (returns `rf.qualified_name`) |
| `add` | `(rf: RoleFunction) -> None` (ValueError on duplicate) |
| `remove` | `(name: str) -> None` |
| `get` | `(name: str) -> Optional[RoleFunction]` |
| `list_all` | `() -> List[RoleFunction]` |
| `to_dict` | `() -> dict` |
| `from_dict` | `(data: dict) -> RoleFunctionLibrary` |

#### 7.5.2 `RoleFunction` (libcntrl version)

| Field | Type | Default |
|-------|------|---------|
| `name` | `str` | – |
| `namespace` | `str` | `""` |
| `description` | `str` | `""` |
| `title` | `str` | `""` |
| `used_global_vars` | `List[str]` | `[]` |
| `used_events` | `List[str]` | `[]` |
| `used_literals` | `List[str]` | `[]` |
| `return_type` | `str` | `""` (Reserved, v1.5) |
| `arg1_type` | `str` | `""` (Reserved, v1.5) |
| `arg1_name` | `str` | `""` (Reserved, v1.5) |
| `arg2_type` | `str` | `""` (Reserved, v1.5) |
| `arg2_name` | `str` | `""` (Reserved, v1.5) |

**Reserved fields note (v1.5)**: `return_type` / `arg1_*` / `arg2_*` are not exposed in the GUI and not consumed by codegen. They are preserved through XML I/O for backward compatibility with pre-v3.7 project files.

**Property**: `qualified_name`.

**Note**: Different from `statable.RoleFunction`. See §9 L-28.

#### 7.5.3 `ConditionLibrary` / `ConditionTemplate`

| Method | Signature |
|--------|-----------|
| `add` | `(ct: ConditionTemplate) -> None` |
| `remove` | `(name: str) -> None` |
| `get` | `(name: str) -> Optional[ConditionTemplate]` |
| `list_all` | `() -> List[ConditionTemplate]` |
| `to_dict` / `from_dict` | – |

#### 7.5.4 `LiteralLibrary` / `LiteralDefinition`

Same API pattern as `ConditionLibrary`.

---

## 8. Error Codes

### 8.1 Exceptions

| # | Exception | Location | Condition |
|---|-----------|----------|-----------|
| 1 | `ValueError` | `StateMachine.add_state` | Duplicate state name |
| 2 | `ValueError` | `StateMachine.add_event` | Duplicate event name |
| 3 | `ValueError` | `StateMachine.add_transition` | source/target/event undefined |
| 4 | `ValueError` | `StateMachine.set_initial` | Undefined state |
| 5 | `ValueError` | `StateMachine.add_role_function` | Duplicate `rf.name` |
| 6 | `ValueError` | `RoleFunctionLibrary.add` | Duplicate `qualified_name` |
| 7 | `ValueError` | `ConditionLibrary.add` | Duplicate `name` |
| 8 | `ValueError` | `LiteralLibrary.add` | Duplicate `name` |
| 9 | `ValueError` | `CCodeGenerator.generate_file` | Unknown filename |
| 10 | `ValueError` | `CStructGenerator.generate_struct` | Unknown struct_type |
| 11 | `ValueError` | `VariableGenerator.generate_variable` | Unknown var_type |
| 12 | `FileNotFoundError` | `project_from_xml` | File missing |
| 13 | `ET.ParseError` | `project_from_xml` | Malformed XML |
| 14 | `OSError` | `save_generated_code` | Write failure |
| 15 | `ImportError` | Module imports | Dependency missing (with fallback) |

### 8.2 Validation Issue Codes

See §5.4 for the full list of 35 codes. Prefixes:

| Prefix | Category |
|--------|----------|
| `STATE_` | State |
| `EVENT_` | Event |
| `TRANSITION_` | Transition |
| `ROLE_FUNC_` | Role function |
| `VAR_` | Variable |
| `FLAG_` | Flag |
| `QUEUE_` | Queue |
| `INTERRUPT_` | Interrupt |
| `TIMER_` | Timer |
| `TYPE_` | Custom type |
| `CELL_` | Cell (v2.2) |

### 8.3 Log Levels

| Level | Purpose |
|-------|---------|
| `DEBUG` | Internal trace |
| `INFO` | Normal completion |
| `WARNING` | Non-fatal issues (duplicates, unknown types) |
| `ERROR` | Failures (validator exceptions, XML parse) |

---

## 9. Limitations

### 9.1 Code Generation

| # | Limitation |
|---|------------|
| L-01 | `generation_style="switch_case"` is effectively disabled (forced to `table_driven`) |
| L-02 | `table_type="switch"/"dictionary"` is effectively disabled (forced to `array`) |
| L-03 | `project_dir_name` reserved, unused |
| L-04 | `external_includes_in_role/transitions/common` not implemented |
| L-05 | `super_include_dir` not persisted in XML |
| L-06 | Multi-layer `by_type` merges into a single file (layer separation invisible) |
| L-07 | `generate_all` is for single state machine; use `generate_all_layers` for multiple |

### 9.2 Marker Merge

| # | Limitation |
|---|------------|
| L-08 | Modified markers cause extraction failure (warning only, data loss) |
| L-09 | `inject_func_user_code` does not insert new markers if absent |
| L-10 | Same-named function in multiple files uses only the first match |

### 9.3 MISRA Integration

| # | Limitation |
|---|------------|
| L-11 | `cppcheck + MISRA addon` is not a certified checker |
| L-12 | `SUPPRESSED_RULES` (in `analyze_misra_impact.py`) and `suppressions.txt` are inconsistent |
| L-13 | `baseline.md` is empty (no actual measurements) |
| L-14 | Output XML filename `cppcheck_raw.xml` differs from SPEC naming (`cppcheck_stderr.txt`) |
| L-15 | Suppression reasons are documented in this SDK reference for all 11 rules (§6.4), but only 4 of 11 are covered in `SPEC_OVERVIEW_en.md` §7.4.4 |
| L-16 | cppcheck dependency (PATH required, 600s timeout) |

### 9.4 Validation

| # | Limitation |
|---|------------|
| L-17 | `codegen/validate/` was not shared at S7 time |
| L-18 | `AIResponseParser` does not parse v2.2 cell-level 7 actions |
| L-19 | `ChangeApplier._add_variable/_add_flag` **now reject duplicates** (fixed in v2.4.1, C-28) |
| L-20 | `AIPromptGenerator._format_data` does not output v2.2 `pre_actions` etc. |
| L-21 | `CellValidator` uses a different design (no `validate()` override, no `suggestion`) |
| L-22 | `EventValidator` `EVENT_UNUSED` and `EVENT_NO_TRANSITION` are semantically duplicated |
| L-23 | `RoleFunctionValidator.ROLE_FUNC_UNUSED` uses exact string match on `Transition.action` / `.condition` only; v2.2 `pre_actions` / `else_actions` / cell actions are not considered |

### 9.5 Data Model

| # | Limitation |
|---|------------|
| L-24 | `StateMachine.role_functions` uses bare-name keys → cross-namespace collision |
| L-25 | `StateMachine` role function keys and `RoleFunctionLibrary` keys differ (bare vs qualified) |

### 9.6 Structure

| # | Limitation |
|---|------------|
| L-26 | `TransitionContext_t` and `TransitionContext_<Layer>_t` are both emitted (same layout) |
| L-27 | `statable/xml_io.py` reverse-depends on `statable_gui.libcntrl` (try/except fallback) |
| L-28 | Two distinct `RoleFunction` classes (`statable.model` vs `libcntrl`) |
| L-29 | Two distinct `GlobalDefinitions` classes (`statable` vs `statable_gui`) |
| L-30 | `CellValidator` uses a different design pattern (no `validate()` override, `suggestion` unset) |
| L-31 | `EventValidator` has semantically duplicated rules (`EVENT_UNUSED` ≡ `EVENT_NO_TRANSITION`) |

---

## 10. Appendix

### 10.1 File Tree (`code/` root)

```
code/
├── statable/
│   ├── __init__.py
│   ├── model.py
│   ├── state_machine.py
│   ├── global_defs.py
│   ├── xml_io.py
│   ├── mermaid_gen.py
│   ├── sample_data.py
│   └── parser.py
├── codegen/
│   ├── __init__.py
│   ├── c_code_generator.py
│   ├── config.py
│   ├── code_templates.py
│   ├── code_merger.py
│   ├── type_mapper.py
│   ├── naming_convention.py
│   ├── struct_generator.py
│   ├── enum_generator.py
│   ├── transition_generator.py
│   ├── role_function_generator.py
│   ├── variable_generator.py
│   ├── event_queue_generator.py
│   ├── interrupt_generator.py
│   ├── timer_generator.py
│   ├── osal_generator.py
│   ├── sample_data.py
│   └── validate/
│       ├── __init__.py
│       ├── validator.py
│       ├── models.py
│       ├── change_actions.py
│       ├── change_applier.py
│       ├── prompt_generator.py
│       ├── response_parser.py
│       ├── clipboard_manager.py
│       ├── validation_dialog.py
│       ├── logger.py
│       ├── data/
│       │   ├── __init__.py
│       │   ├── validation_rules.py
│       │   ├── prompt_templates.py
│       │   ├── action_definitions.py
│       │   └── keywords.py
│       └── items/
│           ├── __init__.py
│           ├── base_validator.py
│           ├── state_validator.py
│           ├── event_validator.py
│           ├── transition_validator.py
│           ├── role_function_validator.py
│           ├── variable_validator.py
│           ├── flag_validator.py
│           ├── queue_validator.py
│           ├── interrupt_validator.py
│           ├── timer_validator.py
│           ├── custom_type_validator.py
│           └── cell_validator.py
├── statable_gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── widgets.py
│   ├── matrix_table.py
│   ├── dialogs.py
│   ├── code_generation_dialog.py
│   ├── code_generation_settings_dialog.py
│   ├── validation_dialog.py
│   ├── condition_builder_dialog.py
│   ├── condition_edit_dialog.py
│   ├── global_defs_dialog.py
│   ├── event_definition_dialog.py
│   ├── event_delivery_settings_dialog.py
│   ├── event_queue_dialog.py
│   ├── interrupt_handler_edit_dialog.py
│   ├── layer_settings_dialog.py
│   ├── common_widgets.py
│   ├── action_edit_dialog.py
│   ├── role_function_dialog.py
│   ├── symbol_picker.py
│   ├── logger.py
│   ├── preferences.py
│   ├── preference_keys.py
│   ├── config.py
│   ├── traceball.py
│   ├── sample_data.py
│   ├── global_defs.py
│   ├── libcntrl/
│   │   ├── __init__.py
│   │   ├── role_function_library.py
│   │   ├── condition_library.py
│   │   ├── literal_library.py
│   │   ├── role_function_edit_dialog.py
│   │   └── literal_management_dialog.py
│   └── transition_editor_direct/
│       ├── __init__.py
│       ├── dialog.py
│       ├── draft.py
│       ├── palette_widget.py
│       ├── canvas_widget.py
│       ├── code_widget.py
│       ├── system_global_dialog.py
│       ├── transitions_tab.py
│       ├── actions_tab.py
│       ├── relations_tab.py
│       ├── relations_edit_dialog.py
│       ├── transition_actions_dialog.py
│       ├── overview_tab.py
│       ├── coverage_analyzer.py
│       ├── flow_widget.py       (legacy)
│       └── edit_dialogs.py      (legacy)
├── tools/
│   ├── run_misra_check.py
│   ├── analyze_misra_impact.py
│   ├── find_all_japanese.py
│   └── verify_generated_code.py
├── misra/
│   ├── suppressions.txt
│   └── baseline.md
├── tests/
│   ├── test_v2_2_p1.py
│   ├── test_v2_2_p2.py
│   ├── test_v2_2_p3.py
│   ├── test_v2_2_p4a.py
│   ├── test_v2_2_p4b.py
│   ├── test_v2_2_p12_2.py
│   ├── test_v2_2_p12_5.py
│   ├── test_v2_2_p12_6.py
│   ├── test_v2_2_p12_7.py
│   ├── test_v2_2_p12_8.py
│   ├── test_v2_2_p12_9.py
│   └── test_v2_2_p12_10.py
└── sdk_doc_tools/
    ├── class_index.py
    ├── class_index.json
    └── class_index.md
```

### 10.2 Test Suites

| # | Suite | Target | Expected |
|---|-------|--------|----------|
| 1 | `test_v2_2_p1.py` | Data model | 94 PASS |
| 2 | `test_v2_2_p2.py` | Code generation | 67 PASS |
| 3 | `test_v2_2_p3.py` | Display layer | 37 PASS |
| 4 | `test_v2_2_p4a.py` | Editor UI | 82 PASS |
| 5 | `test_v2_2_p4b.py` | Overview | 30 PASS |
| 6 | `test_v2_2_p12_2.py` | Stage 2 | 31 PASS |
| 7 | `test_v2_2_p12_5.py` | Stage 5 | 37 PASS |
| 8 | `test_v2_2_p12_6.py` | Stage 6 | 55 PASS |
| 9 | `test_v2_2_p12_7.py` | Stage 7 | 9 PASS |
| 10 | `test_v2_2_p12_8.py` | Stage 8 | 25 PASS |
| 11 | `test_v2_2_p12_9.py` | Stage 9 | 41 PASS |
| 12 | `test_v2_2_p12_10.py` | Stage 10 | 29 PASS / 2 SKIP |
| 13 | `test_v2_3_p1.py` | New Project (v2.3) | 14 PASS |
| **Total** | | | **551 PASS / 2 SKIP** |

### 10.3 Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `QT_QPA_PLATFORM` | `offscreen` | GUI headless |
| `STATABLE_DISABLE_MERMAID` | `1` | Mermaid suppression |
| `PYTHONIOENCODING` | `utf-8` | Prevent encoding issues |

### 10.4 MISRA Artifacts

| Artifact | Path |
|----------|------|
| Suppression list | `misra/suppressions.txt` |
| Baseline | `misra/baseline.md` |
| cppcheck output (stdout) | `misra_report/cppcheck_raw.xml` |
| cppcheck output (stderr) | `misra_report/cppcheck_stderr.txt` |
| Summary | `misra_report/summary.md` |
| Impact analysis | `misra_report/impact.md` |
| Impact CSV | `misra_report/impact.csv` |

### 10.5 Version Matrix

| Component | Version |
|-----------|---------|
| StaTable | 2.4.1 |
| `c_code_generator.py` | 2.2.9 |
| `role_function_generator.py` | 3.3 |
| `transition_generator.py` | 2.6 |
| `code_templates.py` | 2.2.5 |
| `struct_generator.py` | 2.2.1 |
| `enum_generator.py` | 1.5 |
| `variable_generator.py` | 2.0 |
| `timer_generator.py` | 2.2 |
| `osal_generator.py` | 2.2 |
| `naming_convention.py` | 2.2.5 |
| `code_merger.py` | 2.0 |
| `widgets.py` | 3.11 |
| `main_window.py` | 2.4 |
| `role_function_dialog.py` | 3.9 |
| `model.py` | 3.8 |
| `xml_io.py` | 3.8.2 |
| `sample_data.py` | 3.12 |
| `libcntrl/role_function_library.py` | 1.5 |
| `validate/change_applier.py` | 2.4.1 (C-28 fix) |

### 10.6 Revision History

| Version | Date | Content |
|---------|------|---------|
| 1.0 | 2026-09-21 | Initial English master |
| 1.1 | 2026-09-21 | Review fixes (R-1〜R-7): |
| | | - R-1: §7.5.2 cross-reference corrected (§9 L-35 → §9 L-28) |
| | | - R-2: §5.4 `ROLE_FUNC_UNUSED` v2.2 behavior note added |
| | | - R-3: §3.5 / §3.7 `__post_init__` behavior documented |
| | | - R-4: §9 L-15 reworded to distinguish SDK reference vs SPEC_OVERVIEW coverage |
| | | - R-5: §10.1 file tree completed (all GUI and libcntrl files enumerated) |
| | | - R-6: §7.1 XML schema cross-reference to `SPEC_OVERVIEW_en.md` §3.5.2 added |
| | | - R-7: §5.3 `BaseValidator` pattern A / pattern B distinction added |
| 1.2 | 2026-09-22 | Sync with v2.4.1 fixes: |
| | | - C-28 now implemented (§5.7.3, §9 L-19) |
| | | - L-30 / L-31 added (§5.3, §5.4, §9) |

---

**End of Document**
```

---

