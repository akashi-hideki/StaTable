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

**Window title**: `StaTable - State Transition Editor`

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

#### 4.3.1 Structure

```
StateMachineTab (QWidget)
  └── QHBoxLayout
      ├── QSplitter(Qt.Vertical)  [stretch=3]
      │   ├── MatrixTableWidget
      │   └── MermaidWidget
      └── SettingsPanel            [stretch=1]
```

Splitter sizes:

```python
table_height   = int(WINDOW_HEIGHT * TABLE_PREVIEW_RATIO)
mermaid_height = WINDOW_HEIGHT - table_height
left_split.setSizes([table_height, mermaid_height])
```

Minimum sizes:
- `MatrixTableWidget`: `setMinimumHeight(300)`
- `MermaidWidget`: `setMinimumHeight(MERMAID_PREVIEW_MIN_HEIGHT)`

#### 4.3.2 Methods

| Method | Description |
|--------|-------------|
| `__init__(sm, gd, lib..., parent)` | Initialization |
| `update_mermaid()` | Apply settings + update Mermaid |

`update_mermaid()` execution order:
1. `settings.apply_changes()`
2. `table.populate()`
3. `generate_mermaid(sm)`
4. `mermaid.set_mermaid_code(code)`

#### 4.3.3 Signal Connections

| Signal | Source | → Slot |
|--------|--------|--------|
| `transition_changed` | `MatrixTableWidget` | `update_mermaid` |
| `settings_changed` | `SettingsPanel` | `update_mermaid` |

### 4.4 `MermaidWidget`

A read-only widget that displays the state transition diagram. See `SPEC_SCREENS_en.md` §2 for details.

| Item | Value |
|------|-------|
| Rendering engine | Mermaid.js (`mermaidwin.js`) |
| Rendering host | `QWebEngineView` (PySide6-Addons) |
| Output format | `stateDiagram-v2` |
| Env variable | `STATABLE_DISABLE_MERMAID=1` to disable |

### 4.5 `MatrixTableWidget`

| Method | Description |
|--------|-------------|
| `populate()` | Rebuild the transition matrix |
| `open_transition_dialog(row, col)` | Launch D&D editor |
| `keyPressEvent(event)` | Enter/F2: edit, Delete: remove |
| `_find_transitions(state, event)` | Get cell transitions |
| `_generate_cell_label(trans, event)` | Cell display string |

### 4.6 `SettingsPanel` (v2.2)

#### 4.6.1 Structure

`SettingsPanel` contains a `QTabWidget` with two tabs.

| Tab name | Columns |
|----------|---------|
| `State list` | Name / Description / entry function / exit function / do function / Type |
| `Role function` | Title / Function name / **Namespace** / Description / Return type / Arg 1 type / Arg 1 name / Arg 2 type / Arg 2 name |

| Tab | Buttons |
|-----|---------|
| `State list` | `Add` / `Delete` |
| `Role function` | `Add` / `Delete` / `Event definitions...` |

#### 4.6.2 entry / exit Handling (v2.2)

`State.entry` and `State.exit` are **`List[str]`**. The UI displays them as `"; "`-joined strings.

| Function | Purpose |
|----------|---------|
| `_list_to_display(items)` | `List[str]` → `"A; B; C"` |
| `_display_to_list(text)` | `"A; B; C"` → `List[str]` |

- Populate: `_list_to_display(state.entry)`
- Apply: `_display_to_list(item.text())`
- Tooltip: `"Multiple functions: separate with '; '\nDouble-click to edit via action dialog"`

In `apply_changes()`:

```python
entry_list = _display_to_list(entry_text)   # "A; B" -> ["A", "B"]
exit_list  = _display_to_list(exit_text)
```

`do` remains a single `str` (not `List[str]`).

#### 4.6.3 Debounce

`state_table.itemChanged` and `role_table.itemChanged` trigger a 300 ms debounce timer:

```python
self._debounce_timer = QTimer()
self._debounce_timer.setSingleShot(True)
self._debounce_timer.setInterval(300)
self._debounce_timer.timeout.connect(self._emit_settings_changed)
```

#### 4.6.4 `apply_changes()` Behavior

- **State table**: `entry` / `exit` go through `_display_to_list` → `List[str]`; `do` stays `str`
- **Role function table**: `self.sm.role_functions.clear()` then rebuild all rows via `RoleFunction(...)`, including the `namespace` argument

#### 4.6.5 Signal

| Signal | Fired when |
|--------|------------|
| `settings_changed` | After debounce, or after a direct action |

### 4.7 `CodeGenerationDialog`

| Method | Description |
|--------|-------------|
| `_load_saved_settings()` | Load `codegen_settings.json` |
| `_save_settings()` | Save only 4 fields |
| `_generate_code()` | Run generation |
| `_save_code()` | Run save |
| `_show_warnings(records)` | Show warnings (deduplicated) |
| `_update_preview()` | Update preview |

**Attribute `all_layers`**: set externally by `MainWindow`.

### 4.8 `WarningCollector`

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

### 4.9 `ConditionBuilderDialog`

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