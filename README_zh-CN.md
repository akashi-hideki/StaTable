# StaTable

**面向嵌入式系统的 MISRA C:2012 状态机设计与 C 代码生成工具。**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)]()
[![Tests](https://img.shields.io/badge/Tests-1479%20PASS-green.svg)]()
[![MISRA](https://img.shields.io/badge/MISRA-C%3A2012-orange.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)]()

---

## v3.1 新功能

> **简体中文界面支持** — 2026-10-01 发布

StaTable 现已支持**简体中文**图形界面。

- **语言菜单** — 在 English 和简体中文之间切换
- **自动重启** — 点击「立即重启」应用新语言
- **97.4% 翻译完成率**（485 / 498 条）
- **统一启动方式** — `python -m statable` 和 `python gui_main.py` 均会应用已保存的语言

### 切换语言

1. 菜单栏：**Language / 语言** → **简体中文**
2. 在对话框中点击 **立即重启 / Restart now**
3. StaTable 以中文界面重新启动

---

## 为什么选择 StaTable？

大多数开源状态机工具忽略 **MISRA C:2012** 合规性，
而这在汽车、工业和医疗嵌入式软件中是硬性要求。

StaTable 专为需要 **MISRA C:2012 兼容 C 代码生成**的嵌入式团队打造，
无需手写状态机或从零构建自定义工具链。

### 主要特性

- 符合 **MISRA C:2012** 的 C 代码生成 — 通过 `cppcheck` + 官方 MISRA 插件验证（10 个抑制项，全部已文档化）
- **多层状态机** — Driver / Middleware / Application，按优先级顺序执行
- **状态动作（Entry / Exit / Do）** — 表驱动分发，支持用户代码标记
- **35 条验证规则** — 覆盖 11 个类别，支持 AI 辅助诊断
- **基于标记的用户代码保护** — 重新生成时不会覆盖你的自定义代码
- **单元格级动作与关系** — Pre/Post 动作，顺序/互斥/组关系
- **纯 Python 实现** — 易于集成到 CI/CD 流水线
- **35 个测试套件，1479 PASS / 0 FAIL / 2 SKIP**

### v3.1 亮点

- 简体中文界面（97.4%）
- Language 菜单（English ↔ 简体中文）
- 语言切换时自动重启
- 统一的启动方式

---

## 演示

![Demo](docs/demo.gif)

---

## 平台支持

| 平台 | 状态 |
|------|:---:|
| Windows 10 / 11 | ✅ 已验证 |
| Linux (Ubuntu 22.04+) | ✅ 已验证 |
| macOS | ⚠️ 未测试 |

**要求**：

- Python 3.10 以上
- PySide6 6.0 以上（GUI 必需）
- pycparser（可选，用于高级解析）

---

## 快速开始

### 环境要求

- Python 3.10 以上
- PySide6（GUI 必需）

### 安装

```
git clone https://github.com/akashi-hideki/StaTable.git
cd StaTable/code
pip install PySide6 pycparser
```

### 启动 GUI

从 `code/` 目录执行：

```
python -m statable
```

或等价方式：

```
python gui_main.py
```

### 语言切换

StaTable 支持 English 和简体中文。

1. 菜单栏：**Language / 语言**
2. 选择 **English** 或 **简体中文**
3. 在对话框中点击 **Restart now**

设置会被保存，并在下次启动时自动应用。

### 运行测试套件

```
cd code
python tests/test_v2_2_p1.py
python tests/test_v2_3_p1.py
# ... 其他 38 个套件
python tests/test_v3_0_g1_shared.py
```

预期结果：**40 个套件全部通过，1479 PASS / 0 FAIL / 2 SKIP**。

---

## StaTable 生成什么？

从 XML 设计文件生成以下 C 代码（默认单层项目 16 个文件）：

| 文件 | 说明 |
|------|------|
| `statable_types_common.h` | 公共类型定义 |
| `statable_init.c` | 状态机初始化 |
| `statable_transitions.c` | 状态转换逻辑 |
| `statable_state_actions.c` | 状态动作分发 |
| `statable_role_functions.c` | 角色函数实现 |
| `statable_event_queue.c` | 事件队列 |
| `statable_interrupt.c` | 中断处理 |
| `statable_timer.c` | 定时器 |
| `osal.c` / `osal.h` | OSAL 抽象层 |
| `statable_all.h` | 统一包含头 |
| `MyProject_run.c` | 用户主循环集成点 |

全部为 **C89 兼容**，并带有 **MISRA C:2012 抑制注释**。

### 生成代码示例

```c
/* statable_transitions_Application.c */
#include "statable_all.h"

static transition_result_t
t_idle_to_running(ctx_t *ctx)
{
    /* MISRA-C:2012 Rule 15.5: single exit point */
    transition_result_t result = TRANSITION_NONE;

    if (ctx->event == EVENT_START) {
        ctx->next_state = STATE_Running;
        result = TRANSITION_TAKEN;
    }

    return result;
}

const transition_entry_t
    APPLICATION_TRANSITION_TABLE[] = {
    { STATE_Idle, EVENT_START,
      t_idle_to_running, NULL, 0 },
    /* ... */
};
```

### 多层结构

```
generated/
├── common/
│   ├── osal.c / osal.h
│   └── statable_all.h
├── include/
│   ├── statable_types_common.h
│   ├── statable_types_Driver.h
│   ├── statable_types_Middleware.h
│   └── statable_types_Application.h
└── src/
    ├── Driver/
    │   ├── statable_transitions_Driver.c
    │   └── ...
    ├── Middleware/
    └── Application/
```

---

## 架构

```
┌─────────────────────────────────────────────────┐
│              StaTable (v3.0+)                    │
├─────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌──────────────┐             │
│  │ statable/     │  │ codegen/     │             │
│  │ (数据模型)    │  │ (代码生成)   │             │
│  ├───────────────┤  ├──────────────┤             │
│  │ model.py      │  │ c_generator  │             │
│  │ state_machine │  │ validators   │             │
│  │ global_defs   │  │ generators   │             │
│  │ shared/       │  │ validate/    │             │
│  └───────────────┘  └──────────────┘             │
│  ┌───────────────────────────────────┐           │
│  │ statable_gui/ (PySide6 GUI)       │           │
│  ├───────────────────────────────────┤           │
│  │ i18n/  → English / 简体中文       │           │
│  └───────────────────────────────────┘           │
└─────────────────────────────────────────────────┘
```

### 项目结构

```
StaTable/
├── README.md                 英文主文档
├── README_zh-CN.md           本文件（简体中文）
├── LICENSE                   Apache 2.0
├── code/
│   ├── statable/             SDK 数据模型层
│   ├── codegen/              代码生成层
│   │   └── validate/         验证 + AI 诊断
│   ├── statable_gui/         PySide6 GUI
│   │   └── i18n/             翻译资源（.ts / .qm）
│   ├── tools/                开发工具
│   ├── tests/                40 个测试套件
│   └── docs/                 规格文档
└── .github/
    └── workflows/check.yml   CI 设置
```

---

## 使用场景

### 嵌入式固件团队

- MISRA C:2012 合规的代码生成
- 从设计到部署的完整工作流
- 支持 Eclipse / CLI / SDK
- 通过标记保护用户代码

### 工具厂商 / OEM

- Python API（SDK）
- 可自定义模板
- 提供商用 / OEM 授权（请咨询）

### 汽车 / 工业 / 医疗

- 35 条验证规则覆盖安全关键场景
- 文档化的 MISRA 抑制清单
- XML 项目持久化，支持审计追溯

### 教育 / 研究机构

- 免费开源
- 适合教学状态机设计
- Pure Python，便于阅读理解

---

## 文档

| 文档 | 语言 | 说明 |
|------|------|------|
| [README.md](README.md) | English | 英文主文档 |
| [README_zh-CN.md](README_zh-CN.md) | 简体中文 | 本文件 |
| [SPEC_OVERVIEW_en.md](code/docs/SPEC_OVERVIEW_en.md) | English | 完整架构规格 |
| [SPEC_SDK_API_en.md](code/docs/SPEC_SDK_API_en.md) | English | SDK API 参考 |
| [OSAL_PORTING_GUIDE_ja.md](code/docs/OSAL_PORTING_GUIDE_ja.md) | 日本語 | OSAL 移植指南 |
| [TUTORIAL_ja.md](code/docs/TUTORIAL_ja.md) | 日本語 | 完整教程 |

---

## 测试套件

StaTable 包含 **40 个测试套件，共 1479 个断言**，全部通过 CI：

| 类别 | 数量 | 说明 |
|------|:---:|------|
| v2.2 | 12 | 基础功能 |
| v2.3 | 1 | 代码生成 |
| v2.4 | 1 | 合并 |
| v2.5 | 10 | 多层 / 定时器 / 中断 |
| v2.6 | 3 | 单元测试 |
| v2.7 | 3 | 验证 / State Actions |
| v2.8 | 4 | AI 诊断 |
| v3.0 | 5 | SDK / CLI / i18n |
| **总计** | **40** | **1479 PASS** |

---

## 路线图

### v3.0（已完成 — SDK Foundation）

- ✅ **CLI**（`statable-cli generate --xml ...`）
- ✅ **Python SDK**（pip install statable）
- ✅ Eclipse External Tools 集成
- ✅ 共享库（`statable.shared`）

### v3.1（进行中 — 中文本地化）

- ✅ **简体中文界面**（97.4%）
- ✅ **Language 菜单**（English ↔ 简体中文）
- ✅ **语言切换自动重启**
- ⏳ 中文文档

### v3.2+（规划中）

- 自定义模板支持
- 评估版二进制分发（Windows / Linux）
- OEM / 白标授权
- 企业特性（SSO、审计日志）
- 合作伙伴计划

---

## 兼容性

StaTable 在 v2.x → v3.0 之间保持**向后兼容**：

- 旧的 `statable_gui.libcntrl.*` 导入仍然有效（通过 shim）
- 现有 XML 项目文件无需修改
- 生成的 C 代码接口保持稳定

唯一的破坏性变更：v2.5.6 的 `FIRE_EVENT` → `FIRE_EVENT_<Layer>`
（详见英文 README 的 Breaking Changes 部分）

---

## 许可

- **核心**: [Apache License 2.0](LICENSE) — 商业和个人免费使用
- **商用 / OEM**: 提供定制授权

Apache 2.0 允许：

- 商业使用
- 修改
- 分发
- 专利使用
- 私人使用

要求：保留许可和版权声明

---

## 贡献

欢迎贡献！特别需要帮助的领域：

- 多语言文档（中文、英文）
- 新的代码生成模板
- 更多的 MISRA 验证规则
- 平台测试（macOS）

---

## 联系

- **GitHub Issues**: [报告 Bug 或请求功能](https://github.com/akashi-hideki/StaTable/issues)
- **Email**: akashi.hideki@gmail.com

---

## 致谢

- [PySide6](https://www.qt.io/qt-for-python) — Qt 6 for Python
- [cppcheck](https://cppcheck.sourceforge.io/) — 静态分析
- 以及所有贡献者和用户

---

如果 StaTable 对你有帮助，欢迎给个 ⭐
