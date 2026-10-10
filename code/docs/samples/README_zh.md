# StaTable 复合烹饪器具示例包 — 七层架构

Version: 1.0
Date: 2026-10-04
适用：Galanz 等复合烹饪器具（微波炉 / 烤箱 / 蒸箱 / 组合机）

---

## 本包内容

本包为 **复合烹饪器具** 的 StaTable 使用示例，包含：

| 文件 | 内容 | 大小 |
|---|---|---|
| `cooking_heater_controller.xml` | 七层架构示例项目 | 53 KB |
| `LAYER_DESIGN_zh.md` | 七层架构设计指南 | 21 KB |
| `ROLE_FUNCTIONS_zh.md` | 60 个 Role 函数参考 | 32 KB |
| `ECLIPSE_INTEGRATION_zh.md` | Eclipse 集成指南 | 13 KB |
| `INSTALL_GUIDE_zh.md` | 安装指南 | 5 KB |
| `README_zh.md` | 本文件 | — |

---

## 目标用户

**中国本土复合烹饪器具的软件工程师**

典型场景：

- 使用 STM32 / GD32 等 32bit MCU
- 开发微波炉 / 烤箱 / 蒸箱 / 组合机
- 与 Android 面板通过串行通信
- 需要 MISRA C:2012 合规

---

## 七层架构概览

```
+-----------------------------------------------+
|  Android 面板（主控 / UI / IoT）              |
+-------------------+---------------------------+
                    | AC 零交叉同步串行
+-------------------v---------------------------+
|  Application 层（序列执行）                   |
+--+------+------+------+------------------------+
   |      |      |      |
+--v-+ +--v-+ +--v-+ +--v-+
|MwM | |MwO | |MwG | |MwS |  <- 中间层（并列运行）
+--+-+ +--+-+ +--+-+ +--+-+
   |      |      |      |
+--v------v------v------v----------------------+
|  DriverInput 层（传感器 / RX / 门）           |
|  DriverOutput 层（加热器 / 风扇 / TX）        |
+-----------------------------------------------+
```

**详细设计**: 请参阅 `LAYER_DESIGN_zh.md`

| 层 | 职责 | 状态数 |
|---|---|---:|
| Application | 序列执行 / 状态报告 | 5 |
| MwSteam | 蒸汽发生控制 | 5 |
| MwGrill | 烧烤加热控制 | 3 |
| MwOven | 烤箱 / 热风控制 | 3 |
| MwMicrowave | 微波控制 | 4 |
| DriverInput | 输入系（传感器 / RX / 门） | 5 |
| DriverOutput | 输出系（加热器 / 风扇 / TX） | 6 |
| **合计** | | **31** |

---

## 本包的使用方法（重要）

**本包为绿色便携版，无需安装即可使用。**

### 启动步骤

1. **解压** `StaTable-CookingHeater-Package-v3.4.3.zip`（一次即可）
2. **进入**解压后的文件夹 `StaTable-CookingHeater-Package-v3.4.3/`
3. **双击** `StaTable\\StaTable.exe` 启动

### 重要注意

- `StaTable.exe` 必须与其同目录下的 `_internal\\` 文件夹一起使用
- **请勿单独复制** `StaTable.exe`（会无法启动）
- 首次启动约需 2-3 秒

### 首次使用

1. **File > Open Project...**
2. 选择 `samples\\cooking_heater_controller.xml`
3. 七层架构示例加载（约 5 秒）
4. **Code generation > Generate Code... (Ctrl+G)** 生成 C 代码

## 快速开始

### 步骤 1: 安装 StaTable

请参阅 `INSTALL_GUIDE_zh.md`（推荐便携版 ZIP）。

### 步骤 2: 打开示例项目

1. 启动 StaTable GUI
2. **File -> Open Project...**
3. 选择 `cooking_heater_controller.xml`

### 步骤 3: 生成 C 代码

1. **Code generation -> Code generation...** (**Ctrl+G**)
2. 指定输出目录（如 `C:\projects\cooking\output`）
3. 点击 **Generate** 按钮

生成文件: 24 个 `.c` / 27 个 `.h`（共 51 个）

### 步骤 4: 编译验证

```powershell
cd C:\path\to\StaTable\code
python tools\verify_c_syntax.py `
    --root C:\projects\cooking\output `
    --compiler both --std c99 --strict
```

**预期**:

```
gcc      PASS     (24/24)
arm      PASS     (24/24)
Overall:  ALL PASS
```

### 步骤 5: 集成到 Eclipse

请参阅 `ECLIPSE_INTEGRATION_zh.md`（STM32CubeIDE 推荐）。

---

## 文档导航

### 设计阶段

| 目的 | 文档 |
|---|---|
| 理解七层架构 | `LAYER_DESIGN_zh.md` |
| 查看状态迁移图 | `LAYER_DESIGN_zh.md` 第 4 章 |
| 修改 / 扩展架构 | `LAYER_DESIGN_zh.md` 第 6 章 |

### 实现阶段

| 目的 | 文档 |
|---|---|
| 编写 Role 函数 | `ROLE_FUNCTIONS_zh.md` |
| 用户代码保护机制 | `ROLE_FUNCTIONS_zh.md` 1.4 节 |
| 通用实现模式 | `ROLE_FUNCTIONS_zh.md` 第 9 章 |

### 集成阶段

| 目的 | 文档 |
|---|---|
| Eclipse 项目创建 | `ECLIPSE_INTEGRATION_zh.md` 第 3 章 |
| ST-Link 调试 | `ECLIPSE_INTEGRATION_zh.md` 第 6 章 |
| 常见问题 | `ECLIPSE_INTEGRATION_zh.md` 第 7 章 |

---

## 七层架构的优势

### 1. 状态数线性增长

单一状态机: 数十状态 -> 七层架构: **31 状态**

### 2. 并列加热容易表达

Application 层同时激活多个中间层:

- 微波 + 蒸汽
- 烤箱 + 烧烤
- 3 阶段顺序调理

### 3. 独立测试可能

每层独立测试，无需依赖其他层。

### 4. 扩展容易

新加热方式（如油炸）只需追加新中间层，**现有层不变**。

### 5. 用户代码保护

`[[STABLE_USER_CODE_START/END]]` 标记间的代码在重新生成时保留。

---

## 环境要求

### 便携版 ZIP（推荐）

- Windows 10 / 11 (x64)
- 约 500 MB 磁盘空间

### Python 包（开发用）

- Python 3.10 以上
- PySide6（`pip install "statable[gui]"`）

### 目标 MCU

| 系列 | 内核 | 用途 |
|---|---|---|
| STM32G0 | Cortex-M0+ | 入门 / 单功能 |
| **STM32G4** | Cortex-M4 (FPU) | **推荐 / PID 控制** |
| STM32F4 | Cortex-M4 (FPU) | 高性能 |
| STM32F7 | Cortex-M7 | 高端 / HMI |
| GD32 | Cortex-M 兼容 | 国产替代 |

---

## 相关链接

| 资源 | URL |
|---|---|
| StaTable 主仓库 | `https://github.com/akashi-hideki/StaTable` |
| Release v3.3.0 | `https://github.com/akashi-hideki/StaTable/releases/tag/v3.3.0` |
| 用户代码指南 | `code/docs/USER_CODE_GUIDE_zh.md` |
| 完整教程 | `code/docs/tutorial/TUTORIAL_zh.md` |

---

## 重要注意

### 1. 项目路径使用全英文

ARM GCC 对非 ASCII 路径支持有限。

```
OK:   C:\projects\cooking\
NG:   C:\用户\文档\项目\
```

### 2. 用户代码不要放在标记外

```c
/* [[STABLE_USER_CODE_START:Driver_SetHeaterPwm]] */
/* 用户代码写在这里 <- 重新生成时保留 */
/* [[STABLE_USER_CODE_END:Driver_SetHeaterPwm]] */

/* 这行会被覆盖 <- 不要写在这里 */
```

### 3. 不要删除或重命名标记

标记删除后，用户代码在下次生成时会丢失。

---

## 问题反馈

如遇问题，请提供以下信息:

1. StaTable 版本
2. 错误消息完整内容
3. 相关 XML / C 文件片段

---

## 变更历史

| 版本 | 日期 | 内容 |
|---|---|---|
| 1.0 | 2026-10-04 | 初版（Galanz 复合烹饪器具示例包） |

---

*本包为 Galanz 复合烹饪器具的 StaTable 七层架构设计参考资料。*