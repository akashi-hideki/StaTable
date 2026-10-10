# StaTable State Actions Specification v1.1

Version: 1.1

Date: 2026-09-26

Status: Design finalized (ready for implementation)

Target: StaTable v2.7.0 and later

Related: C-57, TUTORIAL_ja §7, SPEC_OVERVIEW_ja §3.2.2

---

## Table of Contents

1. Background and Purpose

2. Terminology

3. Correspondence with UML

4. Data Model

5. XML I/O

6. Code Generation

7. GUI

8. User-Editable Regions

9. Backward Compatibility

10. Implementation Phases

11. Test Plan

12. Design Decisions

13. Open Issues

14. Revision History

---

## 1. Background and Purpose

### 1.1 Background

StaTable is designed as pure event-driven, and does not adopt the

UML state machine concept of **do activity** (continuous processing

while in a state). Therefore, the following constraints exist:

- Continuous processing during a state cannot be expressed

- Periodic monitoring is substituted by TIME events + self-transitions

&#x20; (see TUTORIAL §7)

- entry / exit are `List[str]` (RoleFunc names only), and conditional

&#x20; execution is not possible

### 1.2 Purpose

Achieve the following:

| # | Purpose | Effect |

|---|---------|--------|

| 1 | Integrate state-bound processing (entry / exit / do) | Unified editing location |

| 2 | Officially support do activity | Fulfill UML semantics |

| 3 | Edit via ActionEditorDialog-style GUI | Improved usability |

| 4 | Provide user-editable region per function | Ensure flexibility |

| 5 | Coexistence of GUI editing and custom code | Preservation across regeneration |

### 1.3 Out of Scope

The following are out of scope:

- internal transition (substituted by self-transitions)

- completion transition (unchanged from existing implementation)

- Special handling for concurrent states (CONCURRENT type)

---

## 2. Terminology

| Term | Definition |

|------|------------|

| **State action** | Processing bound to a state. Generic term for entry / exit / do |

| **Entry action** | Executed once upon entering a state |

| **Exit action** | Executed once upon leaving a state |

| **Do activity** | Executed every loop while in a state |

| **ActionStep** | A single action unit. RoleFunc call or event fire + condition |

| **GUI-edited region** | Action list edited by GUI (overwritten on regeneration) |

| **Custom code region** | C code freely written by user (preserved by `[[STABLE_USER_CODE]]`) |

| **StateActionsDialog** | New dialog for editing state actions |

| **`STATE_<Layer>_MAX`** | Sentinel of the existing enum. Used for table size |

---

## 3. Correspondence with UML

| UML Concept | StaTable Implementation | Execution Timing |

|-------------|-------------------------|------------------|

| entry action | `State.entry` (`List[ActionStep]`) | At state transition, on entering new state |

| exit action | `State.exit` (`List[ActionStep]`) | At state transition, on leaving old state |

| do activity | `State.do_actions` (`List[ActionStep]`) | Every loop (before event processing) |

| internal transition | (Substituted by self-transition) | — |

| completion transition | Empty event name | — |

### 3.1 Execution Order (at state transition)

```

[Event arrival]

&#x20; ↓

[Old state's Exit actions]

&#x20; ↓

[Transition pre_actions]

&#x20; ↓

[Condition evaluation → target determined]

&#x20; ↓

[New state's Entry actions]

&#x20; ↓

[Per-loop Do activity]（from next loop onward）

```

---

## 4. Data Model

### 4.1 `ActionStep` Extension

```python

@dataclass(kw_only=True)

class ActionStep:

&#x20;   """State action (v2.7.0 extension)"""

&#x20;   role_function: str = ""      # RoleFunc's qualified_name

&#x20;   trigger: str = "before_transitions"  # existing field (for cell actions)

&#x20;   title: str = ""

&#x20;   # ---- v2.7.0 additions ----

&#x20;   condition: str = ""          # execution condition (C expression; empty = unconditional)

&#x20;   action_type: str = "role"    # "role" | "fire_event" | "custom"

&#x20;   event_name: str = ""         # event name when action_type="fire_event"

```

### 4.2 `State` Extension

```python

@dataclass

class State:

&#x20;   name: str

&#x20;   type: StateType = StateType.NORMAL

&#x20;   parent: Optional[str] = None

&#x20;   # ---- Extension: List[str] → List[ActionStep] ----

&#x20;   entry: List[ActionStep] = field(default_factory=list)

&#x20;   exit: List[ActionStep] = field(default_factory=list)

&#x20;   # ---- New ----

&#x20;   do_actions: List[ActionStep] = field(default_factory=list)

&#x20;   do: str = ""  # [Reserved] backward compat (unused since v2.7.0)

&#x20;   description: str = ""

&#x20;   def __post_init__(self):

&#x20;       # Backward compat: List[str] → List[ActionStep] auto-conversion

&#x20;       self.entry = _normalize_action_list(self.entry)

&#x20;       self.exit = _normalize_action_list(self.exit)

&#x20;       self.do_actions = _normalize_action_list(self.do_actions)

```

### 4.3 Backward Compatibility Helper

```python

def _normalize_action_list(value) -> List[ActionStep]:

&#x20;   """Normalize legacy form (str / List[str]) to List[ActionStep]."""

&#x20;   if value is None:

&#x20;       return []

&#x20;   if isinstance(value, str):

&#x20;       return [ActionStep(role_function=value)] if value.strip() else []

&#x20;   if isinstance(value, list):

&#x20;       result = []

&#x20;       for item in value:

&#x20;           if isinstance(item, str):

&#x20;               if item.strip():

&#x20;                   result.append(ActionStep(role_function=item))

&#x20;           elif isinstance(item, ActionStep):

&#x20;               result.append(item)

&#x20;           elif isinstance(item, dict):

&#x20;               result.append(ActionStep.from_dict(item))

&#x20;       return result

&#x20;   return []

```

---

## 5. XML I/O

### 5.1 New XML Structure

```xml

<State name="Idle" type="initial" ...>

&#x20; <Entry>

&#x20;   <Action role_function="Driver.IdleEntry"

&#x20;           condition="" action_type="role" />

&#x20;   <Action role_function="Driver.ResetCounter"

&#x20;           condition="ctx->reset_needed" action_type="role" />

&#x20; </Entry>

&#x20; <Exit>

&#x20;   <Action role_function="Driver.IdleExit"

&#x20;           condition="" action_type="role" />

&#x20; </Exit>

&#x20; <Do>

&#x20;   <Action role_function="Driver.PollSensor"

&#x20;           condition="" action_type="role" />

&#x20;   <Action role_function="Driver.UpdateLed"

&#x20;           condition="ctx->led_dirty" action_type="role" />

&#x20;   <Action event_name="Driver.TICK_10MS"

&#x20;           condition="" action_type="fire_event" />

&#x20; </Do>

</State>

```

### 5.2 Backward Compatibility

Legacy form:

```xml

<Entry>

&#x20; <Action name="Driver.IdleEntry"/>

</Entry>

```

Normalized by `from_dict`:

```python

ActionStep(role_function="Driver.IdleEntry", action_type="role")

```

### 5.3 Attribute List

| Attribute | Required | Type | Description |

|-----------|:--------:|------|-------------|

| `role_function` | △ | str | Required when `action_type="role"` |

| `event_name` | △ | str | Required when `action_type="fire_event"` |

| `condition` | – | str | Execution condition (C expression) |

| `action_type` | – | str | `"role"` / `"fire_event"` / `"custom"` (default `"role"`) |

| `title` | – | str | Display name (auto-generated if unset) |

### 5.4 Suppression of Empty Attributes

When `condition` / `action_type` are empty or default values, the

**attribute is not emitted** (following the existing v3.8.1 policy).

---

## 6. Code Generation

### 6.1 Generated File Structure

```

output_vending/

├── Driver/

│   ├── statable_state_actions_Driver.h    ← New

│   ├── statable_state_actions_Driver.c    ← New

│   ├── ...

├── Middleware/

│   ├── statable_state_actions_Middleware.h ← New

│   ├── statable_state_actions_Middleware.c ← New

│   ├── ...

└── Vending/

&#x20;   ├── statable_state_actions_Vending.h    ← New

&#x20;   ├── statable_state_actions_Vending.c    ← New

&#x20;   ├── ...

```

### 6.2 Header (`statable_state_actions_<Layer>.h`)

```c

#ifndef STATABLE_STATE_ACTIONS_DRIVER_H

#define STATABLE_STATE_ACTIONS_DRIVER_H

#include "statable_types_common.h"

#include "statable_types_Driver.h"

/* Entry / Exit / Do dispatch */

void Driver_Entry(STATE_Driver_t state, SystemContext_t *ctx);

void Driver_Exit(STATE_Driver_t state, SystemContext_t *ctx);

void Driver_Do(STATE_Driver_t state, SystemContext_t *ctx);

#endif /* STATABLE_STATE_ACTIONS_DRIVER_H */

```

### 6.3 Implementation (`statable_state_actions_<Layer>.c`)

```c

/**

&#x20;* @file    statable_state_actions_Driver.c

&#x20;* @brief   Driver layer state actions (entry / exit / do)

&#x20;* @note    C89-compatible: ordered initializer only.

&#x20;*          Table order MUST match STATE_Driver_t enum order.

&#x20;*/

#include "statable_state_actions_Driver.h"

/* ---- forward declarations ---- */

static void Driver_Entry_Waiting(SystemContext_t *ctx);

static void Driver_Exit_Waiting(SystemContext_t *ctx);

static void Driver_Do_Waiting(SystemContext_t *ctx);

/* ... per state ... */

/* ---- dispatch tables ---- */

typedef void (*Driver_StateFunc_t)(SystemContext_t *ctx);

static const Driver_StateFunc_t g_Driver_EntryTable[STATE_Driver_MAX] = {

&#x20;   Driver_Entry_Waiting,        /* [0] STATE_Driver_Waiting */

&#x20;   Driver_Entry_CoinPulse,      /* [1] STATE_Driver_CoinPulse */

&#x20;   /* ... */

};

static const Driver_StateFunc_t g_Driver_ExitTable[STATE_Driver_MAX] = {

&#x20;   Driver_Exit_Waiting,         /* [0] */

&#x20;   Driver_Exit_CoinPulse,       /* [1] */

&#x20;   /* ... */

};

static const Driver_StateFunc_t g_Driver_DoTable[STATE_Driver_MAX] = {

&#x20;   Driver_Do_Waiting,           /* [0] */

&#x20;   Driver_Do_CoinPulse,         /* [1] */

&#x20;   /* ... */

};

/* ---- dispatchers ---- */

void Driver_Entry(STATE_Driver_t state, SystemContext_t *ctx)

{

&#x20;   if ((unsigned)state < (unsigned)STATE_Driver_MAX) {

&#x20;       Driver_StateFunc_t fn = g_Driver_EntryTable[state];

&#x20;       if (fn != NULL) { fn(ctx); }

&#x20;   }

}

void Driver_Exit(STATE_Driver_t state, SystemContext_t *ctx)

{

&#x20;   if ((unsigned)state < (unsigned)STATE_Driver_MAX) {

&#x20;       Driver_StateFunc_t fn = g_Driver_ExitTable[state];

&#x20;       if (fn != NULL) { fn(ctx); }

&#x20;   }

}

void Driver_Do(STATE_Driver_t state, SystemContext_t *ctx)

{

&#x20;   if ((unsigned)state < (unsigned)STATE_Driver_MAX) {

&#x20;       Driver_StateFunc_t fn = g_Driver_DoTable[state];

&#x20;       if (fn != NULL) { fn(ctx); }

&#x20;   }

}

/* ---- Entry functions (user-editable) ---- */

static void Driver_Entry_Waiting(SystemContext_t *ctx)

{

&#x20;   /* --- GUI-edited actions (regenerated) --- */

&#x20;   (void)RoleFunc_Driver_InitLed(NULL, ctx);

&#x20;   (void)RoleFunc_Driver_ResetCounter(NULL, ctx);

&#x20;   /* --- end GUI-edited actions --- */

&#x20;   /* --- user custom code (preserved) --- */

&#x20;   /* [[STABLE_USER_CODE_START:Driver_Entry_Waiting_custom]] */

&#x20;   (void)ctx;

&#x20;   /* [[STABLE_USER_CODE_END:Driver_Entry_Waiting_custom]] */

}

/* ---- Do functions (user-editable) ---- */

static void Driver_Do_Waiting(SystemContext_t *ctx)

{

&#x20;   /* --- GUI-edited actions (regenerated) --- */

&#x20;   (void)RoleFunc_Driver_PollSensor(NULL, ctx);

&#x20;   if (ctx->led_dirty) {

&#x20;       (void)RoleFunc_Driver_UpdateLed(NULL, ctx);

&#x20;   }

&#x20;   /* --- end GUI-edited actions --- */

&#x20;   /* --- user custom code (preserved) --- */

&#x20;   /* [[STABLE_USER_CODE_START:Driver_Do_Waiting_custom]] */

&#x20;   (void)ctx;

&#x20;   /* [[STABLE_USER_CODE_END:Driver_Do_Waiting_custom]] */

}

/* ---- Exit functions (user-editable) ---- */

static void Driver_Exit_Waiting(SystemContext_t *ctx)

{

&#x20;   /* --- GUI-edited actions (regenerated) --- */

&#x20;   (void)RoleFunc_Driver_SaveState(NULL, ctx);

&#x20;   /* --- end GUI-edited actions --- */

&#x20;   /* --- user custom code (preserved) --- */

&#x20;   /* [[STABLE_USER_CODE_START:Driver_Exit_Waiting_custom]] */

&#x20;   (void)ctx;

&#x20;   /* [[STABLE_USER_CODE_END:Driver_Exit_Waiting_custom]] */

}

```

### 6.4 Action Generation Patterns

| `action_type` | Condition | Generated Code |

|---------------|:---------:|----------------|

| `role` | none | `(void)RoleFunc_<NS>_<Name>(NULL, ctx);` |

| `role` | present | `if (<condition>) { (void)RoleFunc_<NS>_<Name>(NULL, ctx); }` |

| `fire_event` | none | `FIRE_EVENT_<Layer>(<EVENT>);` |

| `fire_event` | present | `if (<condition>) { FIRE_EVENT_<Layer>(<EVENT>); }` |

| `custom` | — | Not generated by GUI; edit via Custom Code tab |

**The first argument of RoleFunc call is `NULL`** (Design decision #1 / Option A).

The existing RoleFunc signature is used as-is.

### 6.5 Change to `{project}_run.c`

```c

void VendingMachineTutorial_Run(void)

{

&#x20;   while (1) {

&#x20;       /* Per-layer state-do dispatch (v2.7.0) */

&#x20;       Driver_Do(g_Driver_state, &g_ctx);

&#x20;       Middleware_Do(g_Middleware_state, &g_ctx);

&#x20;       Application_Do(g_Application_state, &g_ctx);

&#x20;       /* Existing event processing */

&#x20;       {

```

```

&#x20;           EVENT_Driver_t evt = StateMachine_GetNextEvent_Driver(&g_ctx);

&#x20;           if (evt != EVENT_Driver_NONE) {

&#x20;               g_Driver_state = StateMachine_Process_Driver(

&#x20;                   g_Driver_state, evt, &g_ctx);

&#x20;           }

&#x20;       }

&#x20;       /* ... other layers ... */

&#x20;   }

}

```

### 6.6 Calling Entry / Exit

Within the existing `StateMachine_Process_<Layer>`, call before and after

the transition:

```c

/* statable_transitions_Driver.c (embedded into generated code) */

STATE_Driver_t StateMachine_Process_Driver(

&#x20;   STATE_Driver_t from_state, EVENT_Driver_t event, SystemContext_t *ctx)

{

&#x20;   STATE_Driver_t next_state = from_state;

&#x20;   /* ... determine next_state via cell functions ... */

&#x20;   if (next_state != from_state) {

&#x20;       Driver_Exit(from_state, ctx);       /* Exit actions */

&#x20;       Driver_Entry(next_state, ctx);      /* Entry actions */

&#x20;   }

&#x20;   return next_state;

}

```

---

## 7. GUI

### 7.1 Entry Points

| Option | Operation | Adopted |

|:------:|-----------|:-------:|

| **A** | **Double-click** a state row in SettingsPanel | ✅ |

| **B** | Right-click → context menu `Edit Actions...` | Auxiliary |

| **C** | Dedicated button column | Future consideration |

**Conflict avoidance**: Trigger on double-click of **any column other

than the Name column**. The Name column retains inline editing

(existing behavior preserved).

### 7.2 StateActionsDialog Layout

```

┌──────────────────────────────────────────────────────────┐

│ State Actions — Driver.Waiting                           │

├──────────────────────────────────────────────────────────┤

│ [Entry] [Exit] [Do] [Preview]                            │

├──────────────────────────────────────────────────────────┤

│ Actions (executed every loop while in Waiting)           │

│ ┌──────────────────────────────────────────────────────┐ │

│ │ 1. [RoleFunc ▼] Driver.PollSensor                    │ │

│ │    Condition: (none)                                 │ │

│ │ 2. [RoleFunc ▼] Driver.UpdateLed                     │ │

│ │    Condition: ctx->led_dirty                         │ │

│ │ 3. [FIRE_EVENT ▼] Driver.TICK_10MS                   │ │

│ │    Condition: (none)                                 │ │

│ │ [+] [−] [↑] [↓]                                      │ │

│ └──────────────────────────────────────────────────────┘ │

│                                                          │

│ Custom Code (user-editable, preserved)                   │

│ ┌──────────────────────────────────────────────────────┐ │

│ │ /* [[STABLE_USER_CODE_START:..._custom]] */          │ │

│ │ /* Your code here */                                 │ │

│ │ /* [[STABLE_USER_CODE_END:..._custom]] */            │ │

│ └──────────────────────────────────────────────────────┘ │

│                                                          │

│                              [OK] [Cancel]               │

└──────────────────────────────────────────────────────────┘

```

### 7.3 Tab Structure

| # | Tab | Content |

|---|-----|---------|

| 1 | **Entry** | Actions on entering the state |

| 2 | **Exit** | Actions on leaving the state |

| 3 | **Do** | Periodic actions while in the state |

| 4 | **Preview** | Real-time display of generated code |

### 7.4 Action Editing Widget

| # | Element | Content |

|---|---------|---------|

| 1 | Action type | `RoleFunc` / `FIRE_EVENT` |

| 2 | Target selection | RoleFunc dropdown or event dropdown |

| 3 | Condition | Condition expression input (empty = unconditional) |

| 4 | Reorder | ↑↓ buttons |

| 5 | Add / Remove | `[+]` / `[−]` buttons |

### 7.5 Custom Code Tab

Place a **collapsible Custom Code area** at the bottom of each action tab.

| Item | Content |

|------|---------|

| Edit target | Inside `[[STABLE_USER_CODE_START:<state>_<kind>_custom]]` |

| Storage | `custom_code` attribute of `<Entry>` / `<Exit>` / `<Do>` in XML |

| On regeneration | Preserved by `code_merger` |

### 7.6 Generated Code Preview

In the Preview tab, display the C code generated from the current settings:

```c

static void Driver_Do_Waiting(SystemContext_t *ctx)

{

&#x20;   /* --- GUI-edited actions --- */

&#x20;   (void)RoleFunc_Driver_PollSensor(NULL, ctx);

&#x20;   if (ctx->led_dirty) {

&#x20;       (void)RoleFunc_Driver_UpdateLed(NULL, ctx);

&#x20;   }

&#x20;   /* --- end GUI-edited actions --- */

&#x20;   /* [[STABLE_USER_CODE_START:Driver_Do_Waiting_custom]] */

&#x20;   /* ... */

&#x20;   /* [[STABLE_USER_CODE_END:Driver_Do_Waiting_custom]] */

}

```

### 7.7 Commonization with Existing ActionEditorDialog

| # | Target for commonization | Extraction location |

|---|--------------------------|---------------------|

| 1 | Action edit row widget | `ActionStepWidget` |

| 2 | RoleFunc selection dropdown | Reuse existing |

| 3 | Event selection dropdown | New (for `FIRE_EVENT`) |

| 4 | Preview feature | Reuse `CodeWidget` |

| 5 | Custom Code editor | New |

**Common widget extraction decision is deferred to Phase 5**

(Design decision #6).

---

## 8. User-Editable Regions

### 8.1 Two-Layer Structure

Each state action function has **two layers of editable regions**:

| Layer | Marker | Edited via | On regeneration |

|:-----:|--------|------------|:---------------:|

| 1 | (none, function body) | GUI | Overwritten |

| 2 | `<State>_<Kind>_custom` | Hand-written | **Preserved** |

### 8.2 Structure of Generated Code

```c

static void Driver_Do_Waiting(SystemContext_t *ctx)

{

&#x20;   /* --- GUI-edited actions (regenerated) --- */

&#x20;   (void)RoleFunc_Driver_PollSensor(NULL, ctx);

&#x20;   if (ctx->led_dirty) {

&#x20;       (void)RoleFunc_Driver_UpdateLed(NULL, ctx);

&#x20;   }

&#x20;   /* --- end GUI-edited actions --- */

&#x20;   /* --- user custom code (preserved) --- */

&#x20;   /* [[STABLE_USER_CODE_START:Driver_Do_Waiting_custom]] */

&#x20;   (void)ctx;

&#x20;   /* [[STABLE_USER_CODE_END:Driver_Do_Waiting_custom]] */

}

```

### 8.3 Marker Naming Convention

```

[[STABLE_USER_CODE_START:<Layer>_<Kind>_<State>_custom]]

[[STABLE_USER_CODE_END:<Layer>_<Kind>_<State>_custom]]

```

| Element | Value |

|---------|-------|

| `<Layer>` | Layer name (Driver / Middleware / Vending, etc.) |

| `<Kind>` | `Entry` / `Exit` / `Do` |

| `<State>` | State name (alphanumeric only; whitespace → `_`) |

### 8.4 Avoiding Collision with Existing Markers

To avoid collision with the existing

`[[STABLE_USER_CODE_START:<func_name>]]`, the `_custom` suffix is added.

---

## 9. Backward Compatibility

### 9.1 Data Model

| Item | Old | New | Compatibility |

|------|:---:|:---:|:-------------:|

| `State.entry` | `List[str]` | `List[ActionStep]` | Backward-compatible (auto-converted in `__post_init__`) |

| `State.exit` | `List[str]` | `List[ActionStep]` | Same as above |

| `State.do_actions` | none | `List[ActionStep]` | New |

| `State.do` | `str` (reserved) | `str` (remains reserved) | Preserved |

```

### 9.2 XML

The legacy form `<Entry><Action name="..."/></Entry>` is normalized

by `from_dict` to `ActionStep(role_function="...")`.

### 9.3 Code Generation

Existing entry / exit generated code is **fully migrated to the new

function-based form** (Design decision #3). However, loading old XML

remains backward-compatible.

### 9.4 GUI

The existing SettingsPanel entry / exit columns are changed to

**read-only display** (editing is consolidated into StateActionsDialog).

---

## 10. Implementation Phases

| Phase | Content | Dependency | Effort |

|:-----:|---------|:----------:|:------:|

| **1** | Data model extension (`ActionStep` / `State`) | — | Small |

| **2** | XML I/O extension (`<Entry>` / `<Exit>` / `<Do>`) | Phase 1 | Small |

| **3** | codegen: StateActions generation (Entry / Exit / Do + tables) | Phase 1 | Medium |

| **4** | codegen: `{project}_run.c` update | Phase 3 | Small |

| **5** | GUI: StateActionsDialog skeleton (4 tabs) | Phase 2 | Large |

| **6** | GUI: Action editing (order / conditions) | Phase 5 | Medium |

| **7** | GUI: Preview / Custom Code | Phase 5 | Medium |

| **8** | Test / TUTORIAL / SPEC | All phases | Medium |

### 10.1 Phase Completion Criteria

| Phase | Completion Criteria |

|:-----:|---------------------|

| 1 | `test_v2_7_p1.py` PASS (data model) |

| 2 | `test_v2_7_p2.py` PASS (XML round-trip) |

| 3 | `test_v2_7_p3.py` PASS (codegen) + gcc / arm syntax check |

| 4 | Generated `_run.c` syntax check PASS |

| 5 | `test_v2_7_p5.py` PASS (GUI launch / tab display) |

| 6 | `test_v2_7_p6.py` PASS (editing operations) |

| 7 | `test_v2_7_p7.py` PASS (Preview / Custom) |

| 8 | All tests PASS + CI green |

---

## 11. Test Plan

### 11.1 Unit Tests

| # | Test | Target |

|---|------|--------|

| 1 | `ActionStep`'s `to_dict` / `from_dict` | Data model |

| 2 | Backward-compat conversion of `State.entry` | Data model |

| 3 | `<Do>` XML round-trip | XML I/O |

| 4 | Attribute suppression on empty `condition` | XML I/O |

| 5 | StateActions code generation (no condition) | codegen |

| 6 | StateActions code generation (with condition) | codegen |

| 7 | `FIRE_EVENT` generation | codegen |

| 8 | Table order consistency check | codegen |

| 9 | Do call in `{project}_run.c` | codegen |

| 10 | StateActionsDialog launch | GUI |

### 11.2 Integration Tests

| # | Test | Content |

|---|------|---------|

| 1 | Add Do action to `vending_machine.xml` → generate → syntax check | E2E |

| 2 | Whether Custom Code is preserved on regeneration | Merge |

| 3 | Load existing XML (entry / exit as `List[str]`) | Backward compat |

### 11.3 Syntax Verification

| # | Toolchain | Target |

|---|-----------|--------|

| 1 | gcc | All generated files |

| 2 | arm-none-eabi-gcc | All generated files |

---

## 12. Design Decisions

| # | Item | Decision | Reason |

|---|------|----------|--------|

| 1 | RoleFunc signature | **Pass `transition=NULL` (keep existing signature)** | Minimal change to generated code. No problem if RoleFunc implementation does not use `transition` |

| 2 | `custom` action type | **Not handled by GUI; edited via Custom Code tab** | Avoid GUI complexity |

| 3 | Entry / Exit compatibility mode | **Full migration** (backward compat only for old XML) | Documented as a v2.7.0 breaking change |

| 4 | GUI entry point | **Double-click on state row in SettingsPanel (excluding Name column)** | Consistency with ActionEditorDialog |

| 5 | State name C identifier conversion | **Non-ASCII raises a generation error** | Non-ASCII state names deprecated |

| 6 | Common widget extraction | **Decided in Phase 5** | Implement independently first; extract later |

| 7 | MISRA compliance | **Measured upon Phase 3 completion** | Aim within existing level (10 hits) |

| 8 | Table size | **Use `STATE_<Layer>_MAX`** | Existing enum sentinel. No `#define` needed |

---

## 13. Open Issues

| # | Item | Content | Consideration Timing |

|---|------|---------|:--------------------:|

| 1 | Details of state name C identifier conversion | **Concrete error message and detection timing** for non-ASCII states | Phase 1 |

| 2 | C89 compatibility of `_MAX` | Strict C89 conformance when using `[STATE_Driver_MAX]` as array size | Phase 1 (verify) |

| 3 | Custom Code XML persistence | Store `custom_code` attribute in XML, or manage by markers only | Phase 2 |

| 4 | Preview tab editing link | Whether edits reflect in Preview in real time | Phase 7 |

---

## 14. Revision History

| Version | Date | Content |

|---------|------|---------|

| 1.0 | 2026-09-26 | Initial (design stage) |

| 1.1 | 2026-09-26 | Finalized 8 design decisions. Added use of `STATE_<Layer>_MAX`. New §12, old §12 shifted to §13 |

---
