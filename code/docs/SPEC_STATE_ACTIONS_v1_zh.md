# StaTable 状态动作规格书 v1.1

Version: 1.1

Date: 2026-09-26

Status: 设计已确定（实现准备完成）

Target: StaTable v2.7.0 以后

Related: C-57, TUTORIAL_ja §7, SPEC_OVERVIEW_ja §3.2.2

---

## 目录

1. 背景与目的

2. 术语定义

3. 与 UML 的对应

4. 数据模型

5. XML I/O

6. 代码生成

7. GUI

8. 用户编辑区域

9. 与既有实现的兼容性

10. 实现阶段

11. 测试计划

12. 设计决策事项

13. 未解决问题

14. 修订历史

---

## 1. 背景与目的

### 1.1 背景

StaTable 采用纯事件驱动设计，未采用 UML 状态机的

**do 活动**（状态滞留中的持续处理）这一概念。

因此存在以下约束：

- 无法表达状态滞留中的常规定时处理

- 周期性监视使用 TIME 事件 + 自迁移代替（参见 TUTORIAL §7）

- entry / exit 为 `List[str]`（仅 RoleFunc 名），无法条件执行

### 1.2 目的

实现以下内容：

| # | 目的 | 效果 |

|---|------|------|

| 1 | 集成与状态绑定的处理（entry / exit / do） | 编辑位置统一化 |

| 2 | 正式支持 do 活动 | 满足 UML 语义 |

| 3 | 使用 ActionEditorDialog 风格的 GUI 编辑 | 提升可操作性 |

| 4 | 为各函数附加用户编辑区域 | 确保自由度 |

| 5 | GUI 编辑与自定义代码共存 | 重新生成时保持 |

### 1.3 不在范围内

以下不在本规格范围内：

- internal transition（以自迁移代替）

- completion transition（保持既有实现）

- 并行状态（CONCURRENT 型）的特殊处理

---

## 2. 术语定义

| 术语 | 定义 |

|------|------|

| **状态动作** | 与状态绑定的处理。entry / exit / do 的总称 |

| **Entry 动作** | 进入状态瞬间执行 1 次 |

| **Exit 动作** | 离开状态瞬间执行 1 次 |

| **Do 活动** | 状态滞留中每循环执行 |

| **ActionStep** | 1 个动作单位。RoleFunc 调用 or 事件触发 + 条件 |

| **GUI 编辑区域** | 通过 GUI 编辑的动作列表（重新生成时覆盖） |

| **自定义代码区域** | 用户自由编写的 C 代码（以 `[[STABLE_USER_CODE]]` 保持） |

| **StateActionsDialog** | 用于编辑状态动作的新对话框 |

| **`STATE_<Layer>_MAX`** | 既有 enum 的哨兵。用于表大小 |

---

## 3. 与 UML 的对应

| UML 概念 | StaTable 中的实现 | 执行时机 |

|---------|-----------------|--------------|

| entry action | `State.entry`（`List[ActionStep]`） | 状态迁移时，进入新状态瞬间 |

| exit action | `State.exit`（`List[ActionStep]`） | 状态迁移时，离开旧状态瞬间 |

| do activity | `State.do_actions`（`List[ActionStep]`） | 每循环（事件处理之前） |

| internal transition | （以自迁移代替） | — |

| completion transition | 空事件名 | — |

### 3.1 执行顺序（状态迁移时）

```

[事件到达]

&#x20; ↓

[旧状态的 Exit 动作执行]

&#x20; ↓

[迁移的 pre_actions 执行]

&#x20; ↓

[迁移的条件评估 → 确定 target]

&#x20; ↓

[新状态的 Entry 动作执行]

&#x20; ↓

[每循环的 Do 活动执行]（从下个循环开始）

```

---

## 4. 数据模型

### 4.1 `ActionStep` 的扩展

```python

@dataclass(kw_only=True)

class ActionStep:

&#x20;   """状态动作（v2.7.0 扩展）"""

&#x20;   role_function: str = ""      # RoleFunc 的 qualified_name

&#x20;   trigger: str = "before_transitions"  # 既有字段（用于单元格动作）

&#x20;   title: str = ""

&#x20;   # ---- v2.7.0 追加 ----

&#x20;   condition: str = ""          # 执行条件（C 表达式，空则无条件）

&#x20;   action_type: str = "role"    # "role" | "fire_event" | "custom"

&#x20;   event_name: str = ""         # action_type="fire_event" 时的事件名

```

### 4.2 `State` 的扩展

```python

@dataclass

class State:

&#x20;   name: str

&#x20;   type: StateType = StateType.NORMAL

&#x20;   parent: Optional[str] = None

&#x20;   # ---- 扩展: List[str] → List[ActionStep] ----

&#x20;   entry: List[ActionStep] = field(default_factory=list)

&#x20;   exit: List[ActionStep] = field(default_factory=list)

&#x20;   # ---- 新规 ----

&#x20;   do_actions: List[ActionStep] = field(default_factory=list)

&#x20;   do: str = ""  # [Reserved] 向后兼容用（v2.7.0 以后未使用）

&#x20;   description: str = ""

&#x20;   def __post_init__(self):

&#x20;       # 向后兼容: List[str] → List[ActionStep] 自动转换

&#x20;       self.entry = _normalize_action_list(self.entry)

&#x20;       self.exit = _normalize_action_list(self.exit)

&#x20;       self.do_actions = _normalize_action_list(self.do_actions)

```

### 4.3 向后兼容辅助函数

```python

def _normalize_action_list(value) -> List[ActionStep]:

&#x20;   """将旧格式（str / List[str]）规范化为 List[ActionStep]。"""

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

### 5.1 新 XML 结构

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

### 5.2 向后兼容

旧格式：

```xml

<Entry>

&#x20; <Action name="Driver.IdleEntry"/>

</Entry>

```

由 `from_dict` 规范化为以下形式：

```python

ActionStep(role_function="Driver.IdleEntry", action_type="role")

```

### 5.3 属性列表

| 属性 | 必须 | 型 | 说明 |

|------|:---:|-----|------|

| `role_function` | △ | str | `action_type="role"` 时必须 |

| `event_name` | △ | str | `action_type="fire_event"` 时必须 |

| `condition` | – | str | 执行条件（C 表达式） |

| `action_type` | – | str | `"role"` / `"fire_event"` / `"custom"`（省略时 `"role"`） |

| `title` | – | str | 显示名（未设置时自动生成） |

### 5.4 空属性的抑制

当 `condition` / `action_type` 为空 or 默认值时，**不输出属性**

（沿用既有 v3.8.1 的方针）。

---

## 6. 代码生成

### 6.1 生成文件结构

```

output_vending/

├── Driver/

│   ├── statable_state_actions_Driver.h    ← 新规

│   ├── statable_state_actions_Driver.c    ← 新规

│   ├── ...

├── Middleware/

│   ├── statable_state_actions_Middleware.h ← 新规

│   ├── statable_state_actions_Middleware.c ← 新规

│   ├── ...

└── Vending/

&#x20;   ├── statable_state_actions_Vending.h    ← 新规

&#x20;   ├── statable_state_actions_Vending.c    ← 新规

&#x20;   ├── ...

```

### 6.2 头文件（`statable_state_actions_<Layer>.h`）

```c

#ifndef STATABLE_STATE_ACTIONS_DRIVER_H

#define STATABLE_STATE_ACTIONS_DRIVER_H

#include "statable_types_common.h"

#include "statable_types_Driver.h"

/* Entry / Exit / Do 分发 */

void Driver_Entry(STATE_Driver_t state, SystemContext_t *ctx);

void Driver_Exit(STATE_Driver_t state, SystemContext_t *ctx);

void Driver_Do(STATE_Driver_t state, SystemContext_t *ctx);

#endif /* STATABLE_STATE_ACTIONS_DRIVER_H */

```

### 6.3 实现（`statable_state_actions_<Layer>.c`）

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

/* ... 各状态 ... */

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

### 6.4 动作生成模式

| `action_type` | 条件 | 生成代码 |

|--------------|:---:|-----------|

| `role` | 无 | `(void)RoleFunc_<NS>_<Name>(NULL, ctx);` |

| `role` | 有 | `if (<condition>) { (void)RoleFunc_<NS>_<Name>(NULL, ctx); }` |

| `fire_event` | 无 | `FIRE_EVENT_<Layer>(<EVENT>);` |

| `fire_event` | 有 | `if (<condition>) { FIRE_EVENT_<Layer>(<EVENT>); }` |

| `custom` | — | GUI 不生成，由 Custom Code 标签编辑 |

**RoleFunc 调用的第 1 参数为 `NULL`**（设计决策 #1 / 方案 A）。

直接使用既有 RoleFunc 的签名。

### 6.5 `{project}_run.c` 的变更

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

&#x20;       /* ... 其他层 ... */

&#x20;   }

}

```

### 6.6 Entry / Exit 的调用

在既有的 `StateMachine_Process_<Layer>` 内，于迁移前后调用：

```c

/* statable_transitions_Driver.c（嵌入生成代码） */

STATE_Driver_t StateMachine_Process_Driver(

&#x20;   STATE_Driver_t from_state, EVENT_Driver_t event, SystemContext_t *ctx)

{

&#x20;   STATE_Driver_t next_state = from_state;

&#x20;   /* ... 通过单元格函数确定 next_state ... */

&#x20;   if (next_state != from_state) {

&#x20;       Driver_Exit(from_state, ctx);       /* Exit 动作 */

&#x20;       Driver_Entry(next_state, ctx);      /* Entry 动作 */

&#x20;   }

&#x20;   return next_state;

}

```

---

## 7. GUI

### 7.1 启动入口

| 方案 | 操作 | 采用 |

|:---:|------|:---:|

| **A** | SettingsPanel 状态行**双击** | ✅ |

| **B** | 右键 → 上下文菜单 `Edit Actions...` | 辅助 |

| **C** | 专用按钮列 | 将来讨论 |

**冲突规避**：状态行**Name 列以外**双击启动。

Name 列保留内联编辑（维持既有行为）。

### 7.2 StateActionsDialog 的结构

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

### 7.3 标签结构

| # | 标签 | 内容 |

|---|------|------|

| 1 | **Entry** | 进入状态瞬间的动作 |

| 2 | **Exit** | 离开状态瞬间的动作 |

| 3 | **Do** | 状态滞留中的周期动作 |

| 4 | **Preview** | 实时显示生成代码 |

### 7.4 动作编辑控件

| # | 要素 | 内容 |

|---|------|------|

| 1 | 动作类型 | `RoleFunc` / `FIRE_EVENT` |

| 2 | 对象选择 | RoleFunc 下拉框 or 事件下拉框 |

| 3 | Condition | 条件表达式输入栏（空则无条件） |

| 4 | 顺序变更 | ↑↓ 按钮 |

| 5 | 追加 / 删除 | `[+]` / `[−]` 按钮 |

### 7.5 Custom Code 标签

在各动作标签的底部配置**可折叠的 Custom Code 区域**。

| 项目 | 内容 |

|------|------|

| 编辑对象 | `[[STABLE_USER_CODE_START:<state>_<kind>_custom]]` 内 |

| 保存位置 | XML 中 `<Entry>` / `<Exit>` / `<Do>` 的 `custom_code` 属性 |

| 重新生成时 | 由 `code_merger` 保持 |

### 7.6 生成代码预览

在 Preview 标签中，显示由当前设置生成的 C 代码：

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

### 7.7 与既有 ActionEditorDialog 的共通化

| # | 共通化对象 | 抽出目标 |

|---|-----------|-------|

| 1 | 动作编辑行控件 | `ActionStepWidget` |

| 2 | RoleFunc 选择下拉框 | 沿用既有 |

| 3 | 事件选择下拉框 | 新规（用于 `FIRE_EVENT`） |

| 4 | Preview 功能 | 沿用 `CodeWidget` |

| 5 | Custom Code 编辑器 | 新规 |

**共通控件抽出在 Phase 5 判断**（设计决策 #6）。

---

## 8. 用户编辑区域

### 8.1 2 层结构

各状态动作函数具有**2 层编辑区域**：

| 层 | 标记 | 编辑来源 | 重新生成时 |

|:---:|---------|--------|:---:|

| 1 | （无，函数本体） | GUI | 覆盖 |

| 2 | `<State>_<Kind>_custom` | 手写 | **保持** |

### 8.2 生成代码的结构

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

### 8.3 标记命名规则

```

[[STABLE_USER_CODE_START:<Layer>_<Kind>_<State>_custom]]

[[STABLE_USER_CODE_END:<Layer>_<Kind>_<State>_custom]]

```

| 要素 | 值 |

|------|-----|

| `<Layer>` | 层名（Driver / Middleware / Vending 等） |

| `<Kind>` | `Entry` / `Exit` / `Do` |

| `<State>` | 状态名（仅英数字，空格以 `_` 代替） |

### 8.4 与既有标记的冲突规避

为**不与**既有的 `[[STABLE_USER_CODE_START:<func_name>]]` 冲突，

附加 `_custom` 后缀。

---

## 9. 与既有实现的兼容性

### 9.1 数据模型

| 项目 | 旧 | 新 | 兼容性 |

|------|:---:|:---:|:---:|

| `State.entry` | `List[str]` | `List[ActionStep]` | 向后兼容（`__post_init__` 中自动转换） |

| `State.exit` | `List[str]` | `List[ActionStep]` | 同上 |

| `State.do_actions` | 无 | `List[ActionStep]` | 新规 |

| `State.do` | `str`（保留） | `str`（保持保留） | 维持 |

```

### 9.2 XML

旧格式的 `<Entry><Action name="..."/></Entry>` 由

`from_dict` 规范化为 `ActionStep(role_function="...")`。

### 9.3 代码生成

既有的 entry / exit 生成代码**完全迁移到新的基于函数的形式**（设计决策 #3）。

但是，旧 XML 的读取保持向后兼容。

### 9.4 GUI

既有的 SettingsPanel entry / exit 列变更为**只读显示**

（编辑统一到 StateActionsDialog）。

---

## 10. 实现阶段

| Phase | 内容 | 依赖 | 工数 |

|:---:|------|:---:|:---:|

| **1** | 数据模型扩展（`ActionStep` / `State`） | — | 小 |

| **2** | XML I/O 扩展（`<Entry>` / `<Exit>` / `<Do>`） | Phase 1 | 小 |

| **3** | codegen: StateActions 生成（Entry / Exit / Do + 表） | Phase 1 | 中 |

| **4** | codegen: `{project}_run.c` 更新 | Phase 3 | 小 |

| **5** | GUI: StateActionsDialog 骨架（4 标签） | Phase 2 | 大 |

| **6** | GUI: 动作编辑（顺序・条件） | Phase 5 | 中 |

| **7** | GUI: Preview / Custom Code | Phase 5 | 中 |

| **8** | 测试 / TUTORIAL / SPEC | 全 Phase | 中 |

### 10.1 各 Phase 的完成条件

| Phase | 完成条件 |

|:---:|---------|

| 1 | `test_v2_7_p1.py` PASS（数据模型） |

| 2 | `test_v2_7_p2.py` PASS（XML round-trip） |

| 3 | `test_v2_7_p3.py` PASS（codegen） + gcc / arm 语法检查 |

| 4 | 生成的 `_run.c` 语法检查 PASS |

| 5 | `test_v2_7_p5.py` PASS（GUI 启动・标签显示） |

| 6 | `test_v2_7_p6.py` PASS（编辑操作） |

| 7 | `test_v2_7_p7.py` PASS（Preview / Custom） |

| 8 | 全部测试 PASS + CI green |

---

## 11. 测试计划

### 11.1 单元测试

| # | 测试 | 对象 |

|---|--------|------|

| 1 | `ActionStep` 的 `to_dict` / `from_dict` | 数据模型 |

| 2 | `State.entry` 的向后兼容转换 | 数据模型 |

| 3 | `<Do>` XML round-trip | XML I/O |

| 4 | 空 `condition` 的属性抑制 | XML I/O |

| 5 | StateActions 代码生成（无条件） | codegen |

| 6 | StateActions 代码生成（有条件） | codegen |

| 7 | `FIRE_EVENT` 生成 | codegen |

| 8 | 表顺序一致性验证 | codegen |

| 9 | `{project}_run.c` 的 Do 调用 | codegen |

| 10 | StateActionsDialog 的启动 | GUI |

### 11.2 集成测试

| # | 测试 | 内容 |

|---|--------|------|

| 1 | 向 `vending_machine.xml` 添加 Do 动作 → 生成 → 语法检查 | E2E |

| 2 | 重新生成时 Custom Code 是否被保持 | Merge |

| 3 | 既有 XML（entry / exit 为 `List[str]`）的读取 | 向后兼容 |

### 11.3 语法检查

| # | 工具链 | 对象 |

|---|--------------|------|

| 1 | gcc | 全部生成文件 |

| 2 | arm-none-eabi-gcc | 全部生成文件 |

---

## 12. 设计决策事项

| # | 项目 | 决定 | 理由 |

|---|------|------|------|

| 1 | RoleFunc 签名 | **传递 `transition=NULL`（保持既有签名）** | 生成代码变更最小。RoleFunc 实现侧不使用 `transition` 则无问题 |

| 2 | `custom` 动作类型 | **GUI 不处理，由 Custom Code 标签编辑** | 规避 GUI 复杂化 |

| 3 | Entry / Exit 兼容模式 | **完全迁移**（仅旧 XML 向后兼容） | 作为 v2.7.0 的破坏性变更文档化 |

| 4 | GUI 启动入口 | **SettingsPanel 状态行双击（Name 列以外）** | 与 ActionEditorDialog 统一感 |

| 5 | 状态名 C 标识符化 | **非 ASCII 在生成时报错** | 非 ASCII 状态名不推荐 |

| 6 | 共通控件抽出 | **Phase 5 判断** | 先独立实现 → 之后再抽出 |

| 7 | MISRA 对应 | **Phase 3 完成时测定** | 目标在既有水平（10 hits）以内 |

| 8 | 表大小 | **使用 `STATE_<Layer>_MAX`** | 既有 enum 的哨兵。无需添加 `#define` |

---

## 13. 未解决问题

| # | 项目 | 内容 | 讨论时期 |

|---|------|------|:---:|

| 1 | 状态名 C 标识符化细节 | 含非 ASCII 时的**具体错误消息与检测时机** | Phase 1 |

| 2 | `_MAX` 的 C89 兼容性 | 将 `[STATE_Driver_MAX]` 用作数组大小时的严格 C89 符合性 | Phase 1（验证） |

| 3 | Custom Code 的 XML 保存 | 将 `custom_code` 属性保存到 XML，或仅用标记管理 | Phase 2 |

| 4 | Preview 标签的编辑联动 | 编辑内容是否实时反映到 Preview | Phase 7 |

---

## 14. 修订历史

| 版本 | 日期 | 内容 |

|-----------|------|------|

| 1.0 | 2026-09-26 | 初版（设计阶段） |

| 1.1 | 2026-09-26 | 确定 8 项设计决策事项。追记 `STATE_<Layer>_MAX` 的使用。新设 §12，旧 §12 顺延为 §13 |

---
