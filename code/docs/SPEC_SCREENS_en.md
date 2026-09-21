# `docs/SPEC_SCREENS_en.md` v2.4 (English, Screen Specification)

**Note**: Since the existing `SPEC_SCREENS_en.md` content is not available, this is a **reconstructed complete version** based on `SPEC_OVERVIEW_en.md` v2.3 and the pre-implementation investigation results. If it differs from the existing file, apply only the relevant diffs.

```markdown
# StaTable Screen Specification v2.4 (English)

Version: 2.4
Date: 2026-09-22
Scope: StaTable GUI screens (whole)
Prerequisite: See `SPEC_OVERVIEW_en.md` v2.3

---

## Table of Contents

1. Screen List
2. MainWindow
3. Menu Bar
4. Toolbar
5. Tab Widget
6. Dialog List
7. New Project Feature (v2.3)
8. Unsaved Changes Dialog (v2.3)
9. Window Title (v2.3)
10. Status Bar (v2.3)
11. Revision History

---

## 1. Screen List

| # | Screen / Widget | Class | File | Modal |
|---|-----------------|-------|------|-------|
| 1 | Main window | `MainWindow` | `statable_gui/main_window.py` | – |
| 2 | State machine tab | `StateMachineTab` | `statable_gui/widgets.py` | – |
| 3 | Settings panel | `SettingsPanel` | `statable_gui/widgets.py` | – |
| 4 | Mermaid preview | `MermaidWidget` | `statable_gui/widgets.py` | – |
| 5 | Transition matrix | `MatrixTableWidget` | `statable_gui/matrix_table.py` | – |
| 6 | Global definitions | `GlobalDefinitionsDialog` | `statable_gui/global_defs_dialog.py` | Modal |
| 7 | Type manager | `TypeManagerDialog` | `statable_gui/common_widgets.py` | Modal |
| 8 | Event definitions | `EventDefinitionDialog` | `statable_gui/event_definition_dialog.py` | Modal |
| 9 | Event delivery settings | `EventDeliverySettingsDialog` | `statable_gui/event_delivery_settings_dialog.py` | Modal |
| 10 | Interrupt handler edit | `InterruptHandlerEditDialog` | `statable_gui/interrupt_handler_edit_dialog.py` | Modal |
| 11 | Layer settings | `LayerSettingsDialog` | `statable_gui/layer_settings_dialog.py` | Modal |
| 12 | Validation dialog | `ValidationDialog` | `statable_gui/validation_dialog.py` | Modal |
| 13 | Code generation | `CodeGenerationDialog` | `statable_gui/code_generation_dialog.py` | Modal |
| 14 | Code generation settings | `CodeGenerationSettingsDialog` | `statable_gui/code_generation_settings_dialog.py` | Modal |
| 15 | Transition editor | `ActionEditorDialog` | `statable_gui/transition_editor_direct/dialog.py` | Modal |
| 16 | TraceBall log | `TraceBallWidget` | `statable_gui/traceball.py` | Dock |
| 17 | **Unsaved Changes dialog (v2.3)** | `QMessageBox` | (Qt standard) | Modal |
| 18 | **Tab name input (v2.3, existing)** | `QInputDialog` | (Qt standard) | Modal |

---

## 2. MainWindow

### 2.1 Overall Layout

```
┌────────────────────────────────────────────────────────────┐
│ MainWindow (QMainWindow)                                   │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Menu bar (File / Edit / Validate / Code generation / View)│
│ ├────────────────────────────────────────────────────────┤ │
│ │ Toolbar                                                │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ ┌────────────────────────────────────────────────────┐ │ │
│ │ │ QTabWidget                                          │ │ │
│ │ │ ┌─────────────────────────────────────────────────┐│ │ │
│ │ │ │ StateMachineTab "Application"                   ││ │ │
│ │ │ │ ┌──────────────────────────┬──────────────────┐││ │ │
│ │ │ │ │ MatrixTableWidget        │ SettingsPanel    │││ │ │
│ │ │ │ │ (transition matrix)      │ (states / roles) │││ │ │
│ │ │ │ ├──────────────────────────┤                  │││ │ │
│ │ │ │ │ MermaidWidget            │                  │││ │ │
│ │ │ │ │ (state diagram preview)  │                  │││ │ │
│ │ │ │ └──────────────────────────┴──────────────────┘││ │ │
│ │ │ └─────────────────────────────────────────────────┘│ │ │
│ │ └────────────────────────────────────────────────────┘ │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ TraceBall dock (hidden by default, toggleable)         │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ Status bar                                             │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 2.2 Attributes

| Attribute | Value |
|-----------|-------|
| Base class | `QMainWindow` |
| Initial size | `WINDOW_WIDTH × WINDOW_HEIGHT` |
| Window title | `Untitled[*] - StaTable` (v2.3) |
| Menu bar | 5 menus (see §3) |
| Toolbar | `TopToolBarArea` |
| Central widget | `QTabWidget` |
| Dock widget | `TraceBallWidget` (`BottomDockWidgetArea`, initially hidden) |
| Status bar | `QStatusBar` (used from v2.3) |

---

## 3. Menu Bar

### 3.1 Menu Structure (v2.3)

```
File
├── New Project...          (Ctrl+N)        ★v2.3 added
├── ─────────────
├── Open Project...         (none)
├── Save Project...         (none)
├── Rename Tab...           (none)
├── ─────────────
└── New State Machine       (none)

Edit
├── Global Definitions...   (none)
├── Type Definitions...     (none)
├── Event Definitions...    (none)
├── Event Delivery Settings... (none)
├── Interrupt Handlers...   (none)
└── Layer Settings...       (none)

Validate(&V)
└── Validate Project...     (Ctrl+Shift+V)

Code generation(&G)
├── Generate Code...        (Ctrl+G)
├── Generation Settings...  (Ctrl+Shift+G)
└── Save Generated Code...  (Ctrl+Shift+S)

View
└── TraceBall               (checkable)
```

### 3.2 File Menu Details

| # | Item | Shortcut | Connected to | v2.3 |
|---|------|----------|--------------|------|
| 1 | **New Project...** | `Ctrl+N` | `MainWindow.new_project` | ★Added |
| 2 | ───────────── | – | – | ★Added |
| 3 | Open Project... | none | `MainWindow.open_project` | Existing |
| 4 | Save Project... | none | `MainWindow.save_project` | Existing |
| 5 | Rename Tab... | none | `MainWindow.rename_current_tab` | Existing |
| 6 | ───────────── | – | – | Existing |
| 7 | New State Machine | none | `MainWindow.add_new_tab` | Existing |

### 3.3 Existing Shortcuts (v2.3)

| Shortcut | Menu | Purpose |
|----------|------|---------|
| `Ctrl+N` | File | New Project ★Added |
| `Ctrl+Shift+V` | Validate | Run validation |
| `Ctrl+G` | Code generation | Generate code |
| `Ctrl+Shift+G` | Code generation | Generation settings |
| `Ctrl+Shift+S` | Code generation | Save generated code |

**No conflict**: `Ctrl+N` is unused until v2.3. It does not collide with any existing shortcut.

---

## 4. Toolbar

### 4.1 Toolbar Layout

Placed in `TopToolBarArea`. Built by `MainWindow.create_toolbar()`.

| # | Button | Connected to |
|---|--------|--------------|
| 1 | Global definitions | `open_global_defs_dialog` |
| 2 | Type definitions | `open_type_manager` |
| 3 | Event definitions | `open_event_definition_dialog` |
| 4 | Event delivery | `open_event_delivery_settings` |
| 5 | Interrupts | `open_interrupt_settings` |
| 6 | Layer settings | `open_layer_settings` |
| 7 | Validate | `open_validation_dialog` |
| 8 | Generate | `open_code_generation_dialog` |
| 9 | Generation settings | `open_code_generation_settings` |
| 10 | Save generated code | `save_generated_code_direct` |
| 11 | Show log | `toggle_traceball` (checkable) |

**v2.3 change**: No `New Project` button is added to the toolbar (menu only). Reason: preserve toolbar consistency (editing/generation categories only).

---

## 5. Tab Widget

### 5.1 Tab Structure

Each layer is a tab in `QTabWidget`. Each tab is a `StateMachineTab` instance.

### 5.2 StateMachineTab Layout

```
┌──────────────────────────────────────────────────────────┐
│ QHBoxLayout                                              │
│ ┌────────────────────────────────┬──────────────────────┐│
│ │ QSplitter (Vertical)           │ SettingsPanel        ││
│ │ ┌────────────────────────────┐ │ ┌──────────────────┐││
│ │ │ MatrixTableWidget          │ │ │ State list tab   │││
│ │ │ (transition matrix)        │ │ │ Role function tab│││
│ │ │ min height 300px           │ │ └──────────────────┘││
│ │ ├────────────────────────────┤ │                      ││
│ │ │ MermaidWidget              │ │                      ││
│ │ │ (state diagram preview)    │ │                      ││
│ │ │ min height MERMAID_PREVIEW_MIN_HEIGHT                ││
│ │ └────────────────────────────┘ │                      ││
│ └────────────────────────────────┴──────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

### 5.3 v2.3 Added Signal

| Signal | Emitted from | Connected to |
|--------|-------------|--------------|
| `dataModified` | signal-to-signal connection in `__init__` | `MainWindow._on_tab_data_modified` |

Internal connection (end of `__init__`):
```python
self.table.transition_changed.connect(self.dataModified)
self.settings.settings_changed.connect(self.dataModified)

```

### 5.4 v3.11 Wiring Addition

| Item | Content |
|------|---------|
| `layer_names_provider` | Forwarded by `StateMachineTab` to `SettingsPanel` |
| Purpose | Populate the Namespace combo box with all tab names |
| Source | `MainWindow._get_all_layer_names()` (v2.4) |

---

## 6. Dialog List

| # | Dialog | Modal | `exec()` return used | v2.3 modified-flag |
|---|--------|-------|---------------------|-------------------|
| 1 | `GlobalDefinitionsDialog` | Modal | **No** (C-36) | Not reflected |
| 2 | `TypeManagerDialog` | Modal | **No** (C-37) | Not reflected |
| 3 | `EventDefinitionDialog` | Modal | Yes (`QDialog.Accepted`) | Not reflected (C-36) |
| 4 | `EventDeliverySettingsDialog` | Modal | Yes | Not reflected (C-37) |
| 5 | `InterruptHandlerEditDialog` | Modal | **No** (C-37) | Not reflected |
| 6 | `LayerSettingsDialog` | Modal | Yes (`_on_ok` → `accept`) | Not reflected (C-37) |
| 7 | `ValidationDialog` | Modal | No | – |
| 8 | `CodeGenerationDialog` | Modal | No | – |
| 9 | `CodeGenerationSettingsDialog` | Modal | No | – |
| 10 | `ActionEditorDialog` | Modal | – | In-tab edits reflected |

**v2.3 scope**: Dialog-driven edits are not reflected in `windowModified` (C-36〜C-39). Only in-tab edits are reflected.

---

## 7. New Project Feature (v2.3 / F-15)

### 7.1 Screen Transition

```
┌─────────────────────────┐
│ MainWindow              │
│ (showing sample project)│
└───────────┬─────────────┘
            │
            │ File > New Project... or Ctrl+N
            ▼
┌─────────────────────────┐
│ Unsaved Changes dialog  │ ← Only when windowModified == True
│ (Save / Discard / Cancel)│
└───────────┬─────────────┘
            │
            ├── Cancel ────→ MainWindow (unchanged)
            │
            ├── Save ────→ Save dialog ──→ Save OK ──┐
            │                            └── Save failed ──→ MainWindow (unchanged)
            │
            └── Discard ───────────────────────────────┐
                                                       │
                                                       ▼
                                        ┌─────────────────────────┐
                                        │ MainWindow (new project) │
                                        │ ・One Application tab    │
                                        │ ・states/events/trans 0  │
                                        │ ・GlobalDefinitions empty│
                                        │ ・Shared libraries empty │
                                        │ ・ConfigManager default  │
                                        │ ・windowModified = False │
                                        │ ・Title: Untitled        │
                                        │ ・Status bar: 3s notice  │
                                        └─────────────────────────┘
```

### 7.2 State Changes on New Project

| Target | Change | Decision # |
|--------|--------|-----------|
| Tabs | All removed → one `Application` tab | #2 |
| States / events / transitions | All cleared (0) | – |
| `StateMachine.role_functions` | All cleared (0) | – |
| `cell_actions` / `cell_relations` | All cleared (`{}`) | – |
| GlobalDefinitions | Regenerated (empty) | – |
| **RoleFunctionLibrary** | **Regenerated (empty)** | **#5 revised** |
| **ConditionLibrary** | **Regenerated (empty)** | **#5 revised** |
| **LiteralLibrary** | **Regenerated (empty)** | **#5 revised** |
| ConfigManager | `reset()` | #6 |
| Preferences | Preserved | #7 |
| TraceBall log | Preserved | #8 |
| `windowModified` | `False` | #4 |

### 7.3 Menu Item Display

| Item | Display text | Shortcut | Tooltip |
|------|-------------|----------|---------|
| New Project | `New Project...` | `Ctrl+N` | None (default) |

### 7.4 Comparison with Startup

| Aspect | At startup | On New Project |
|--------|-----------|---------------|
| Tabs | `Application` (sample) | `Application` (empty) |
| States/events/transitions | Sample data | Empty |
| GlobalDefinitions | Demo data | Empty |
| Shared libraries | Sample registered | Empty |
| ConfigManager | Default | Default (`reset()`) |
| Preferences | Loaded | Preserved |
| TraceBall log | Startup log | Preserved (previous log) |
| Title | Initially `StaTable - State Transition Editor` | `Untitled[*] - StaTable` |

**Note**: At startup the title remains `StaTable - State Transition Editor` in v2.3. `_update_window_title()` is called only on `new_project` / `open_project` / successful `save_project` / tab edit.

---

## 8. Unsaved Changes Dialog (v2.3)

### 8.1 Display Conditions

Called from `MainWindow._maybe_save()`. Invoked at three places:

| Trigger | Caller |
|---------|--------|
| `File > New Project...` / `Ctrl+N` | Start of `MainWindow.new_project` |
| `File > Open Project...` | Start of `MainWindow.open_project` |
| Window close | `MainWindow.closeEvent` |

### 8.2 Dialog Specification

| Item | Value |
|------|-------|
| Class | `QMessageBox` |
| Icon | `QMessageBox.Warning` |
| Title | `"Unsaved Changes"` |
| Message | `"The current project has unsaved changes.\nDo you want to save them before continuing?"` |
| Buttons | `Save` / `Discard` / `Cancel` |
| Default button | `Save` |

### 8.3 Per-Button Behavior

| Button | `_maybe_save()` return | Caller behavior |
|--------|----------------------|-----------------|
| Save | Return value of `save_project()` | Save OK → proceed; save cancelled/failed → abort |
| Discard | `True` | Proceed |
| Cancel | `False` | Abort |

### 8.4 No Changes

When `windowModified == False`, **no dialog is shown**; `_maybe_save()` returns `True`.

### 8.5 Text-based Mock-up

```
┌─────────────────────────────────────────────────┐
│  ⚠  Unsaved Changes                             │
│                                                 │
│  The current project has unsaved changes.       │
│  Do you want to save them before continuing?    │
│                                                 │
│       [ Save ]  [ Discard ]  [ Cancel ]         │
└─────────────────────────────────────────────────┘
```

---

## 9. Window Title (v2.3)

### 9.1 Title Formats

| State | Title |
|-------|-------|
| At startup (unchanged from v2.0) | `StaTable - State Transition Editor` |
| After `new_project` | `Untitled[*] - StaTable` |
| After successful `open_project` | `Untitled[*] - StaTable` |
| After successful `save_project` | `Untitled[*] - StaTable` |
| When `windowModified == True` | `Untitled* - StaTable` (`[*]` replaced by `*`) |
| When `windowModified == False` | `Untitled - StaTable` (`[*]` removed) |

### 9.2 `[*]` Placeholder

Works in combination with Qt's `QMainWindow.setWindowTitle("[*] ...")` and `setWindowModified(bool)`:

```python
def _update_window_title(self) -> None:
    self.setWindowTitle("Untitled[*] - StaTable")
```

`setWindowModified(True)` → title becomes `Untitled* - StaTable`
`setWindowModified(False)` → title becomes `Untitled - StaTable`

### 9.3 Constraints

- The project file name (`project_path`) is not tracked in v2.3. The title is always `Untitled`.
- A future v2.4 could track `project_path` and expand to `<filename>[*] - StaTable`.

---

## 10. Status Bar (v2.3)

### 10.1 Usage

| Trigger | Message | Timeout |
|---------|---------|---------|
| On `new_project` completion | `"New project created"` | 3000 ms |
| On `open_project` completion | (not implemented / future) | – |
| On successful `save_project` | (not implemented / future) | – |

### 10.2 Mock-up

```
┌─────────────────────────────────────────────────┐
│ New project created                             │  ← 3 s display
└─────────────────────────────────────────────────┘
```

### 10.3 `QMainWindow` Base Class Confirmation

Since `MainWindow(QMainWindow)` is inherited, `statusBar()` is available automatically (confirmed in B-5).

---

## 11. Revision History

| Version | Date | Content |
|---------|------|---------|
| 1.0 | 2026-09-20 | Initial |
| 2.0 | 2026-09-20 | Detailed (dialog list, tab structure added) |
| 2.3 | 2026-09-21 | New Project feature (F-15): |
| | | - §1: Added "Unsaved Changes dialog" and "Tab name input" to screen list |
| | | - §3: Added `New Project...` (Ctrl+N) to File menu; shortcut list updated |
| | | - §4: Documented that no New Project button is added to the toolbar (menu only) |
| | | - §5: Added `StateMachineTab.dataModified` signal |
| | | - §6: Added table of dialog `windowModified` reflection status (C-36〜C-39) |
| | | - §7: New Project feature section added (screen transition, state changes, decision #5 reflected) |
| | | - §8: Unsaved Changes dialog specification added |
| | | - §9: Window title specification added (`Untitled[*] - StaTable`) |
| | | - §10: Status bar specification added (used from v2.3) |
| | | - §11: Revision history (this entry) |

| 2.4 | 2026-09-22 | UI cleanup / namespace combo: |
| | | - §5.4: documented `layer_names_provider` wiring |
| | | - §11: revision history (this entry) |
---

End of document.
```

---

**Note**: This file is a **reconstructed version**. If the existing `SPEC_SCREENS_en.md` differs, the following merge approach is recommended:

1. Check the existing file's structure (chapter organization, granularity)
2. Merge only the diffs into that structure
3. In particular, §3 (Menu Bar), §7 (New Project), and §8 (Unsaved Changes) are the substantive additions

## Summary of v2.3 Files Output

| # | File | Status |
|---|------|--------|
| 1 | `docs/IMPLEMENTATION_PLAN_v2_3.md` | ✅ Output |
| 2 | `docs/SPEC_OVERVIEW_ja.md` | ✅ Output |
| 3 | `docs/SPEC_OVERVIEW_en.md` | ✅ Output |
| 4 | `docs/SPEC_SCREENS_ja.md` | ✅ Output |
| 5 | `docs/SPEC_SCREENS_en.md` | ✅ Output (this response) |

## Next Action

All 5 documents are now available. The next steps are:

1. **Apply the documents to the actual files** in the repository
2. **Begin implementation** following `IMPLEMENTATION_PLAN_v2_3.md` Step 1
3. **Update CI** (`.github/workflows/check.yml`) to include `test_v2_3_p1.py`

If any document needs further refinement (e.g., existing `SPEC_SCREENS_*.md` structure integration), or if you want a **Step 1 implementation code diff**, let me know.