# StaTable 教程 — 完整版

Version: 2.0
Date: 2026-10-04
适用版本：StaTable v3.3.0 及以上
读者：初次使用 StaTable 的设计者

---

## 目录

### 序章
1. 工具的设计思想
2. 示例主题：自动售货机控制程序

### 正文 — 构建骨架
3. 步骤1：创建项目
4. 步骤2：构建骨架（状态 + 事件）

### 正文 — 填充矩阵
5. 步骤3：构建迁移（从 Driver 层开始）
6. 步骤4：完成单元格（首次注册 Role 函数）
7. 步骤5：完成状态
8. 步骤6：同样完成其他层

### 正文 — 完成
9. 步骤7：用图确认
10. 步骤8：生成 C 代码
11. 步骤9：集成到嵌入式
12. 步骤10：保存项目

### 应用篇
13. 复用现有项目
14. 迭代开发

### 总结
15. 作业 × 功能 对照表
16. 常见问题（FAQ）
17. 下一步

### 附录
A. 标记参考
B. 术语对照表
C. 术语集
D. 变更历史

---

# 序章

---

## 1. 工具的设计思想

### 1.1 StaTable 是什么工具

StaTable 是一个**定义程序部件，将其组装到状态迁移矩阵中，
并由此构建可运行程序的工具**。

- **部件** = Role 函数（系统能做什么）
- **组装** = 状态迁移（何时使用哪个部件）
- **成品** = 状态机（作为 C 代码输出）

它特别适合以下类型的程序：

| 适合的程序 | 示例 |
|---|---|
| 状态迁移明确 | 自动售货机、洗衣机、电梯 |
| 事件驱动 | 中断处理、通信协议 |
| 嵌入式系统 | MCU 固件全般 |
| 需要符合 MISRA C:2012 | 车载、医疗、工业设备 |

### 1.2 "部件"与"组装"的比喻

类似于制作电子电路板。

    +-----------------------------------------------+
    |  StaTable = 面包板                            |
    |                                               |
    |  +-------------+    +---------------+         |
    |  | 部件盒      |    | 配线板        |         |
    |  | (Role 函数) |    | (状态迁移     |         |
    |  |             |    |  矩阵)        |         |
    |  | - 硬币判定  |    |               |         |
    |  | - 商品出货  |    | 待机|选择|支付|         |
    |  | - 找零计算  |    | ----+---+---  |         |
    |  | - 错误显示  |    | 选择| O |     |         |
    |  | - 电机驱动  |    | 支付|   | O   |         |
    |  +-------------+    +---------------+         |
    +-----------------------------------------------+

1. 首先**在部件盒中准备好部件**（定义功能）
2. 然后**将部件放到配线板上**（填充迁移矩阵）
3. 电路图（状态机）就组装完成了

### 1.3 整体作业步骤（骨架 → 填充）

利用 StaTable 特性的**推荐作业步骤**如下：

    步骤1：创建项目
           |
    步骤2：构建骨架（状态 + 事件）
           |  -> 迁移矩阵的框架自动出现
           |
    步骤3：填充迁移（逐个单元格）
           |  -> 需要时当场添加 Role 函数
           |
    步骤4：完成单元格（动作、关系）
           |
    步骤5：完成状态（entry / exit）
           |
    步骤6：完成（确认 -> 生成 C 代码 -> 集成）

#### 为什么"骨架 → 填充"

| # | 理由 |
|---|---|
| 1 | 注册状态和事件后，**矩阵框架自动生成** |
| 2 | 可以**边看设计图边作业**（适合探索式设计） |
| 3 | 可以**在需要时添加 Role 函数**（不创建无用部件） |
| 4 | 即使纸面设计不完整也能开始 |

### 1.4 术语整理（Role 函数 = 部件）

本教程中，StaTable 的术语按下述方式使用：

| StaTable 术语 | 本教程称呼 | 含义 |
|---|---|---|
| **Role 函数** | **部件（功能）** | 系统能做的事情 |
| **State** | 状态 | 动作模式 |
| **Event** | 触发 | 改变状态的信号 |
| **Transition** | 迁移 | "A 状态下 X 事件到达则转到 B" |
| **Layer** | 层 | 按职责分类（Driver / Middleware / Application） |
| **Namespace** | 命名空间 | 部件所属的层 |

#### Role 函数 = 部件的示例（自动售货机）

| 抽象度 | 表现 | 示例 |
|---|---|---|
| 高 | 功能 | "判定硬币" |
| 中 | 动作 | ValidateCoin() |
| 低 | C 函数 | int RoleFunc_Middleware_ValidateCoin(...) |

本教程从**"功能"层级开始**，逐渐具体化。

#### 术语关系图

       层
          |
          | 属于
          v
    Role 函数（部件）
          |
          | 使用
          v
    迁移  <--  状态 x 事件
          |
          | 聚合为
          v
    状态机

### 1.5 前提条件

- **StaTable v3.3.0 及以上**（文件级标记功能在 v3.3.0 中添加）
- **Python 3.10 及以上**（用于运行 GUI 和 CLI）
- 已安装 **PySide6**（pip install "statable[gui]"）
- 具备 **C99** 和**状态机**的基础知识
- （可选）了解 **MISRA C:2012** 以应对合规项目

---

## 2. 示例主题：自动售货机控制程序

### 2.1 要制作什么（产品概要）

制作**自动售货机控制程序**。

#### 基本动作

1. 顾客选择商品
2. 投入硬币
3. 金额足够则出货
4. 有找零则退还
5. 完成后返回待机状态

#### 错误处理

- 商品卡住
- 找零不足
- 断电
- 非法硬币

#### 为什么选自动售货机作为题材

| # | 理由 |
|---|---|
| 1 | **状态迁移具体** — 待机、选择、支付、出货、完成 |
| 2 | **事件丰富** — 按钮、硬币、超时、错误 |
| 3 | **功能作为"部件"明确** — 硬币判定、商品出货、找零计算 |
| 4 | **容易画纸面草图** — 任何人都能想象动作 |
| 5 | **错误处理自然** — 卡住、找零不足、断电 |

### 2.2 三层架构

自动售货机由**三个层**组成。每个层**自包含**，不跨层共享 Role 函数。

    +-----------------------------------------------------+
    |  Application 层（销售逻辑）                          |
    |    与顾客的交互、销售流程整体控制                     |
    |                                                       |
    |    状态：Idle / ProductSelected / AwaitingPayment /  |
    |          Dispensing / ReturningChange / Error         |
    |    功能：SelectProduct, ConfirmPurchase, ...         |
    +-----------------------------------------------------+
    |  Middleware 层（设备处理）                            |
    |    硬币判定、商品出货、找零计算                       |
    |                                                       |
    |    状态：MwIdle / CoinAccepting / Dispensing / ..    |
    |    功能：ValidateCoin, DispenseProduct, ...          |
    +-----------------------------------------------------+
    |  Driver 层（硬件控制）                                |
    |    电机、传感器、LCD、键盘                            |
    |                                                       |
    |    状态：HwIdle / HwActive / HwError                 |
    |    功能：MotorStart, MotorStop, LcdWrite, ...        |
    +-----------------------------------------------------+

#### 各层的职责

| 层 | 职责 | 主要功能 |
|---|---|---|
| **Application** | 销售流程控制 | 商品选择受理、购买确认、找零处理指示 |
| **Middleware** | 设备抽象化 | 硬币判定、商品出货控制、找零计算 |
| **Driver** | 硬件控制 | 电机驱动、传感器读取、LCD 写入、按键读取 |

#### 层的独立性（重要）

各层的 Role 函数**只在该层内使用**。

    好的设计（层的独立性）
       Application 层：只使用 Application 内的 Role 函数
       Middleware 层：只使用 Middleware 内的 Role 函数
       Driver 层：只使用 Driver 内的 Role 函数

    应避免的设计（层间依赖）
       Application 层：直接调用 Driver 层的 Role 函数

**为什么层的独立性重要**：

| # | 理由 |
|---|---|
| 1 | **可以独立测试每一层** |
| 2 | **容易复用到其他产品** |
| 3 | **维护范围明确** |
| 4 | **有助于降低 MISRA C:2012 的复杂度** |

### 2.3 有哪些状态

在纸面上设计各层的状态。

#### Application 层状态

| # | 状态 | 说明 |
|---|---|---|
| 1 | Idle | 待机（等待顾客） |
| 2 | ProductSelected | 已选择商品 |
| 3 | AwaitingPayment | 等待付款 |
| 4 | Dispensing | 出货中 |
| 5 | ReturningChange | 找零退还中 |
| 6 | Error | 错误状态 |

#### Middleware 层状态

| # | 状态 | 说明 |
|---|---|---|
| 1 | MwIdle | 待机 |
| 2 | CoinAccepting | 硬币接收中 |
| 3 | Dispensing | 出货控制中 |
| 4 | ChangeCalculating | 找零计算中 |

#### Driver 层状态

| # | 状态 | 说明 |
|---|---|---|
| 1 | HwIdle | 硬件待机 |
| 2 | HwActive | 硬件运行中 |
| 3 | HwError | 硬件错误 |

### 2.4 什么会改变状态（事件）

在纸面上设计各层的事件。

#### Application 层事件

| # | 事件 | 说明 |
|---|---|---|
| 1 | SELECT | 商品选择按钮按下 |
| 2 | COIN_IN | 检测到投币 |
| 3 | CONFIRM | 购买确认 |
| 4 | DISPENSE_DONE | 出货完成 |
| 5 | CHANGE_DONE | 找零退还完成 |
| 6 | CANCEL | 取消 |
| 7 | ERROR | 发生错误 |
| 8 | RESET | 错误重置 |

#### Middleware 层事件

| # | 事件 | 说明 |
|---|---|---|
| 1 | MW_START_COIN | 硬币接收开始指示 |
| 2 | MW_COIN_VALID | 检测到有效硬币 |
| 3 | MW_COIN_INVALID | 检测到无效硬币 |
| 4 | MW_START_DISPENSE | 出货开始指示 |
| 5 | MW_DISPENSE_DONE | 出货完成 |
| 6 | MW_START_CHANGE | 找零退还开始指示 |
| 7 | MW_CHANGE_DONE | 找零退还完成 |

#### Driver 层事件

| # | 事件 | 说明 |
|---|---|---|
| 1 | HW_ENABLE | 启用硬件 |
| 2 | HW_DISABLE | 禁用硬件 |
| 3 | HW_MOTOR_START | 启动电机 |
| 4 | HW_MOTOR_STOP | 停止电机 |
| 5 | HW_ERROR | 检测到硬件错误 |

### 2.5 需要哪些功能（部件）

在纸面上列出各层所需的功能。

#### Application 层功能

| # | 功能 | 说明 |
|---|---|---|
| 1 | ShowProductList | 显示商品列表 |
| 2 | HighlightProduct | 高亮选中的商品 |
| 3 | CalculateTotal | 计算总金额 |
| 4 | CheckSufficientFunds | 判断金额是否足够 |
| 5 | RequestDispense | 请求出货 |
| 6 | RequestChange | 请求找零 |
| 7 | ShowError | 显示错误 |
| 8 | ResetSystem | 重置系统 |

#### Middleware 层功能

| # | 功能 | 说明 |
|---|---|---|
| 1 | ValidateCoin | 判定硬币 |
| 2 | AccumulateCoin | 累积投入金额 |
| 3 | DispenseProduct | 出货控制 |
| 4 | StopDispense | 停止出货 |
| 5 | CalculateChange | 计算找零 |
| 6 | DispenseChange | 退还找零 |

#### Driver 层功能

| # | 功能 | 说明 |
|---|---|---|
| 1 | InitHardware | 初始化硬件 |
| 2 | ReadCoinSensor | 读取硬币传感器 |
| 3 | DriveMotor | 驱动电机 |
| 4 | StopMotor | 停止电机 |
| 5 | WriteLcd | 写入 LCD |
| 6 | ReadKeypad | 读取键盘 |

### 2.6 完成意象（纸面草图）

#### Application 层状态迁移图

                         [SELECT]
                             |
    +----------+         +---------------+
    |   Idle   | ------> |ProductSelected|
    +----------+         +---------------+
         ^                     |
         | [RESET]             | [COIN_IN]
         |                     v
    +----------+         +---------------+
    |  Error   | <------ |AwaitingPayment|
    +----------+ [ERROR] +---------------+
         ^                     |
         |                     | [CONFIRM]
         |                     v
         |               +---------------+
         |               |  Dispensing   |
         |               +---------------+
         |                     |
         |                     | [DISPENSE_DONE]
         |                     v
         |               +---------------+
         |               |ReturningChange|
         |               +---------------+
         |                     |
         |                     | [CHANGE_DONE]
         |                     v
         +----------------- 返回 Idle

#### 三层的关系（执行顺序）

    1. Driver 层（最优先，硬件控制）
           |
    2. Middleware 层（设备处理）
           |
    3. Application 层（销售逻辑）

该顺序在 **Layer Settings** 中设置（步骤7 说明）。

---

# 正文 — 构建骨架

---
## 3. 步骤1：创建项目

### 3.1 启动 StaTable

#### 操作

在终端（或命令提示符）中执行：

    cd StaTable/code
    python -m statable

#### 结果

显示**示例项目**（Application 标签页）。

- 4 个状态（Idle / Active / Error / Halt）
- 5 个事件（START / STOP / ERROR / TIMER0_OVERFLOW / 完成）
- 6 个迁移
- 9 个 Role 函数

这些**在本教程中不使用**，因此在下一步中删除。

### 3.2 开始新项目

#### 操作

1. 选择菜单 **File > New Project...**（或 **Ctrl+N**）
2. 显示**未保存确认对话框**：

       +-------------------------------------------------+
       |  !  Unsaved Changes                             |
       |                                                 |
       |  The current project has unsaved changes.       |
       |  Do you want to save them before continuing?    |
       |                                                 |
       |       [ Save ]  [ Discard ]  [ Cancel ]         |
       +-------------------------------------------------+

   | 按钮 | 动作 |
   |-------|------|
   | **Save** | 保存当前项目后执行 |
   | **Discard** | 不保存直接执行（不需要示例时选此项） |
   | **Cancel** | 中止并返回原画面 |

3. 选择 **Discard**

#### 结果

| 项目 | 变化 |
|------|------|
| 标签页 | 只有 1 个空的 `Application` 标签页 |
| 状态 / 事件 / 迁移 | 全部为空（0 个） |
| 共享库 | 空 |
| 全局定义 | 空 |
| 代码生成设置 | 默认 |
| 窗口标题 | `Untitled[*] - StaTable` |
| 状态栏 | `New project created` 显示 3 秒 |

**现在是空白状态。**

### 3.3 准备三个标签页（层）

#### 3.3.1 标签页名 = 层名

**在 StaTable 中，标签页名直接作为"层名"使用。**

| 标签页名 | 自动设置的 `layer_name` |
|-------|--------------------------|
| `Application` | `"Application"` |
| `Driver` | `"Driver"` |
| `Middleware` | `"Middleware"` |

#### 为什么重要

| # | 理由 |
|---|---|
| 1 | **成为 Role 函数的 Namespace 候选** — Role function 对话框的下拉框中显示所有标签页名 |
| 2 | **用于生成的 C 代码文件名** — 例如 `statable_transitions_Driver.c` |
| 3 | **成为层优先级设置的对象** — 在 Layer Settings 中设置各层执行顺序 |

#### 命名推荐

- 简短、含义明确的名字
- 例：`Application`, `Driver`, `Middleware`
- 例：`App`, `Drv`, `Mw`（缩写也可以，但要保持一致）

#### 3.3.2 确认当前标签页

`Application` 标签页已经创建（新项目自动生成）。
自动设置为 **`layer_name = "Application"`**。

#### 3.3.3 添加 Driver 标签页

**操作**：

1. 菜单 **File > New State Machine**（或工具栏的 **New tab** 按钮）
2. 输入标签页名：`Driver`
3. 点击 OK
4. 新标签页 **Driver** 被添加

**自动设置的项**：
- `layer_name`: `Driver`（从标签页名自动设置）
- `layer_priority`: `5`（默认；稍后修改）

#### 3.3.4 添加 Middleware 标签页

同样操作：

1. 菜单 **File > New State Machine**
2. 标签页名：`Middleware`
3. OK

#### 结果

    +----------+----------+----------------+
    | Driver   |Middleware| Application    |
    +----------+----------+----------------+

三个标签页排列完成。

### 3.4 确认哪些是空的

切换各标签页，确认**全部为空**。

#### 确认项目

| 项目 | 期望值 |
|------|--------|
| State list 标签页 | 0 个 |
| Role function 标签页 | 0 个 |
| 迁移矩阵 | 空（0 列、0 行） |
| Mermaid 图 | 只有 `[*]`（无初始状态） |

#### 矩阵的显示（例：Application 标签页）

    （无列、无行）

因为未注册状态和事件，**矩阵为空**。

**步骤1 完成。接下来构建骨架。**

---

## 4. 步骤2：构建骨架（状态 + 事件）

### 4.1 为什么从状态和事件开始

StaTable 的**迁移矩阵是自动生成的**：

    迁移矩阵
    +-- 列 = State list 中的状态
    +-- 行 = Event definitions 中的事件

也就是说，**只要注册状态和事件，矩阵的框架就会出现**。

#### 先构建骨架的优点

| # | 优点 |
|---|---|
| 1 | **整体图景可见** — 可以目视确认哪些单元格应该有迁移 |
| 2 | **设计规模明确** — 知道状态数 × 事件数的规模 |
| 3 | **Role 函数可以后续处理** — 需要时添加 |
| 4 | **可以边看单元格边设计** — 适合探索式设计 |

#### 作业顺序

对每一层（Driver / Middleware / Application）重复：

    1. 注册状态       -> 矩阵的"列"出现
    2. 注册事件       -> 矩阵的"行"出现
    3. 查看矩阵       -> 确认整体图景

### 4.2 为什么从 Driver 层开始

构建三层的顺序，其理由根植于**自动售货机的实际动作**。

#### 分解自动售货机的动作

即使是"出货"这样一个动作，也可以按层分解。

    【Application 层】
      顾客按下"购买确认"
           |  "出货"
    【Middleware 层】
      库存减 1，指示出货机构
           |  "转动电机"
    【Driver 层】
      电机转动指定角度，通过传感器检测完成

**上层动作由下层动作组合而成。**

#### 具体例："出货"

| 层 | 做什么 | Role 函数示例 |
|---|---------|--------------|
| Application | 接收购买确认，请求出货 | `RequestDispense` |
| Middleware | 库存确认 -> 出货控制 -> 完成通知 | `DispenseProduct` |
| Driver | 电机转动 -> 传感器读取 -> 停止 | `DriveMotor`, `ReadSensor` |

**如果下层（Driver）的功能不确定，上层（Middleware / Application）
的功能就无法创建。**

#### Driver 层定义"机器能做什么"

Driver 层是定义**该机器物理上能做什么**的层。

| 层 | 定义什么 | 自动售货机的例子 |
|---|-------------|----------------|
| **Driver** | 机器的物理能力 | 转动电机、读取传感器、写 LCD |
| **Middleware** | 设备操作 | 判定硬币、出货、计算找零 |
| **Application** | 业务逻辑 | 商品选择、购买确认、找零退还 |

#### 比喻

    Driver 层     = "这台机器能转动电机、能读取传感器"
                    （＝机器能力的目录）
           | 组合
    Middleware 层 = "因此，可以判定硬币、出货"
           | 组合
    Application 层= "因此，可以销售商品"

**换言之**：
- Driver 层接近**硬件规格书**（贴近物理）
- Middleware 层是**设备操作手册**（功能的组合）
- Application 层是**业务流程**（作为产品的行为）

**从 Driver 层开始 = 首先确定机器的能力。**
一旦确定，上层就可以专注于"如何组合这些能力"。

#### 相反，从 Application 层开始的话

    【Application 层】"购买确认时要出货"
           | 但...
    【Middleware 层】"'出货'具体要做什么？"
           | 但...
    【Driver 层】"电机怎么转，还没决定"
           ^ 这里未确定

**在"出货"的实现方法未确定的情况下，推进上层设计，
之后会发生大幅返工。**

#### 自动售货机的设计顺序及依据

| 顺序 | 层 | 确定什么 | 一旦确定... |
|------|-----|-------------|----------|
| 1 | **Driver** | 电机、传感器、LCD 的控制方法 | Middleware 可以调用"转动电机" |
| 2 | **Middleware** | 硬币判定、出货、找零计算 | Application 可以调用"出货" |
| 3 | **Application** | 与顾客的交互、销售流程 | 整个程序完成 |

#### 每个阶段都能得到"可运行的东西"

从 Driver 层开始，**每个阶段都能进行动作确认**。

| 阶段 | 可确认的内容 |
|------|--------------|
| Driver 完成时 | 电机转动、LCD 显示文字、按键可读 |
| Middleware 完成时 | 投入硬币即被判定、商品出 1 个 |
| Application 完成时 | 实际销售流程可运行 |

**从 Application 层开始，到最后都没有"可运行的东西"。**

#### 团队开发的优势

多人开发自动售货机时：

| 负责 | 期间 | 内容 |
|------|------|------|
| Driver 负责 | 前半 | 完成硬件控制 |
| Middleware 负责 | 中盘 | 等 Driver 完成后开始 |
| Application 负责 | 后半 | 等 Middleware 完成后开始 |

**如果 Driver 负责先启动，其他就可以无等待地并行作业。**

#### 与层独立性的关系

该设计顺序与序章所述"层的独立性"一致。

- Driver 层不知道 Application 层的存在
- Middleware 层不知道 Application 层的存在
- Application 层不知道 Driver / Middleware 层的细节

**"从下层构建" = "从被依赖的一侧构建"**，
自然保持层的独立性。

### 4.3 注册 Driver 层的状态和事件

首先从最下层（Driver）开始。

#### 4.3.1 打开 Driver 标签页

**操作**：点击标签栏中的 **Driver**。

#### 4.3.2 注册 Driver 层的状态

**使用的功能**：SettingsPanel > **State list** 标签页 > **Add** 按钮

**注册的状态（3 个）**：

| # | Name | Description | entry function | exit function | Type |
|---|------|-------------|---------------|---------------|------|
| 1 | `HwIdle` | 硬件待机中 | （空） | （空） | `normal` |
| 2 | `HwActive` | 硬件运行中 | （空） | （空） | `normal` |
| 3 | `HwError` | 硬件错误 | （空） | （空） | `normal` |

**步骤**：

1. 点击 **Add** 按钮
2. 添加一行
3. 点击 **Name** 列并输入 `HwIdle`
4. 在 **Description** 列输入 `硬件待机中`
5. **Type** 保持 `normal`（默认）
6. 同样添加 `HwActive`, `HwError`

> **要点**：entry / exit **在此阶段保持为空**。
> 在步骤5 中根据需要添加 Role 函数。

#### 4.3.3 注册 Driver 层的事件

**使用的功能**：SettingsPanel > **Role function** 标签页中的
**Event definitions...** 按钮

**注册的事件（5 个）**：

| # | Event name | Delivery type | Description |
|---|-----------|--------------|-------------|
| 1 | `HW_ENABLE` | `DIRECT` | 启用硬件 |
| 2 | `HW_DISABLE` | `DIRECT` | 禁用硬件 |
| 3 | `HW_MOTOR_START` | `DIRECT` | 启动电机 |
| 4 | `HW_MOTOR_STOP` | `DIRECT` | 停止电机 |
| 5 | `HW_ERROR` | `QUEUE` | 检测到硬件错误 |

**步骤**：

1. 点击 **Event definitions...** 按钮
2. 打开 EventDefinitionDialog
3. 用 **Add** 添加上面 5 个
4. 点击 OK

> **Delivery type 的选择**：
> - `DIRECT`：从中断直接处理（重视响应性）
> - `QUEUE`：经由队列（可做优先级控制）
> - `DOUBLE`：两者
>
> Driver 层重视响应性，因此基本用 `DIRECT`，错误通知用 `QUEUE`。

#### 4.3.4 确认 Driver 层的矩阵

**操作**：关闭 SettingsPanel（或点击矩阵）

**结果**：

              | HwIdle | HwActive | HwError
    ----------+--------+----------+---------
    HW_ENABLE |
    HW_DISABLE|
    HW_MOTOR_ |
      START   |
    HW_MOTOR_ |
      STOP    |
    HW_ERROR  |

**空的矩阵（3 列 × 5 行）** 出现了。这就是骨架。

### 4.4 注册 Middleware 层的状态和事件

Middleware 层也按与 Driver 层相同的步骤注册。
详细操作步骤请参考 **4.3**。

#### 注册的状态（4 个）

| # | Name | Description | Type |
|---|------|-------------|------|
| 1 | `MwIdle` | 待机中 | `normal` |
| 2 | `CoinAccepting` | 硬币接收中 | `normal` |
| 3 | `Dispensing` | 出货控制中 | `normal` |
| 4 | `ChangeCalculating` | 找零计算中 | `normal` |

#### 注册的事件（7 个）

| # | Event name | Delivery type | Description |
|---|-----------|--------------|-------------|
| 1 | `MW_START_COIN` | `DIRECT` | 硬币接收开始指示 |
| 2 | `MW_COIN_VALID` | `DIRECT` | 检测到有效硬币 |
| 3 | `MW_COIN_INVALID` | `DIRECT` | 检测到无效硬币 |
| 4 | `MW_START_DISPENSE` | `DIRECT` | 出货开始指示 |
| 5 | `MW_DISPENSE_DONE` | `DIRECT` | 出货完成 |
| 6 | `MW_START_CHANGE` | `DIRECT` | 找零退还开始指示 |
| 7 | `MW_CHANGE_DONE` | `DIRECT` | 找零退还完成 |

#### 确认矩阵

注册后，出现空的 **4 列 × 7 行** 矩阵。

### 4.5 注册 Application 层的状态和事件

Application 层同样注册。
详细操作步骤请参考 **4.3**。

#### 注册的状态（6 个）

| # | Name | Description | Type |
|---|------|-------------|------|
| 1 | `Idle` | 待机（等待顾客） | `normal` |
| 2 | `ProductSelected` | 已选择商品 | `normal` |
| 3 | `AwaitingPayment` | 等待付款 | `normal` |
| 4 | `Dispensing` | 出货中 | `normal` |
| 5 | `ReturningChange` | 找零退还中 | `normal` |
| 6 | `Error` | 错误状态 | `normal` |

#### 注册的事件（8 个）

| # | Event name | Delivery type | Description |
|---|-----------|--------------|-------------|
| 1 | `SELECT` | `DIRECT` | 商品选择按钮按下 |
| 2 | `COIN_IN` | `DIRECT` | 检测到投币 |
| 3 | `CONFIRM` | `DIRECT` | 购买确认 |
| 4 | `DISPENSE_DONE` | `DIRECT` | 出货完成 |
| 5 | `CHANGE_DONE` | `DIRECT` | 找零退还完成 |
| 6 | `CANCEL` | `DIRECT` | 取消 |
| 7 | `ERROR` | `QUEUE` | 发生错误 |
| 8 | `RESET` | `DIRECT` | 错误重置 |

#### 确认矩阵

注册后，出现空的 **6 列 × 8 行** 矩阵。

### 4.6 确认各层的矩阵

切换三个标签页，确认**骨架是否齐全**。

#### 确认表

| 层 | 状态数 | 事件数 | 矩阵 |
|---|-------|-----------|-----------|
| Driver | 3 | 5 | 3 × 5 |
| Middleware | 4 | 7 | 4 × 7 |
| Application | 6 | 8 | 6 × 8 |
| **合计** | **13** | **20** | - |

#### 骨架完成的检查表

- [ ] Driver 标签页：注册了 3 个状态 + 5 个事件
- [ ] Middleware 标签页：注册了 4 个状态 + 7 个事件
- [ ] Application 标签页：注册了 6 个状态 + 8 个事件
- [ ] 各标签页中可见矩阵框架
- [ ] Mermaid 图在各标签页中只显示状态

#### 目前还未做的事

| 项目 | 在哪做 |
|------|---------|
| 添加迁移 | 步骤3（第 5 章） |
| 单元格动作 | 步骤4（第 6 章） |
| entry / exit | 步骤5（第 7 章） |
| 注册 Role 函数 | 步骤4 以后（需要时） |
| 层优先级设置 | 步骤7（第 9 章） |

**骨架完成。接下来填充矩阵。**

---

# 正文 — 填充矩阵

---
## 5. 步骤3：构建迁移（从 Driver 层开始）

### 5.1 如何阅读矩阵

确认 **MatrixTableWidget**：

              | HwIdle | HwActive | HwError
    ----------+--------+----------+---------
    HW_ENABLE |
    HW_DISABLE|
    HW_MOTOR_ |
      START   |
    HW_MOTOR_ |
      STOP    |
    HW_ERROR  |

- **列** = 状态（从 State list 自动生成）
- **行** = 事件（从 Event definitions 自动生成）
- **单元格** = 该（状态, 事件）下发生什么（即一个迁移）

### 5.2 在单元格中添加迁移

#### Driver 层要添加的迁移

| # | 状态 | 事件 | 目标 | 条件 | 模式 |
|---|------|---------|--------|------|--------|
| 1 | HwIdle | HW_ENABLE | HwActive | （无） | Commit |
| 2 | HwActive | HW_DISABLE | HwIdle | （无） | Commit |
| 3 | HwActive | HW_ERROR | HwError | （无） | Commit |
| 4 | HwError | HW_DISABLE | HwIdle | （无） | Commit |

> **注意**：`HW_MOTOR_START` / `HW_MOTOR_STOP` **不改变状态**，
> 因此不作为迁移添加。它们作为"单元格动作"处理（步骤4 说明）。

### 5.3 迁移模式（Commit / Tentative）

迁移有两种模式。

| 模式 | 含义 | 使用场合 |
|-------|------|---------|
| **Commit** | 该迁移成立后，不再评估同一单元格内的后续迁移 | 普通迁移（默认） |
| **Tentative** | 可被后续迁移覆盖 | 例外性迁移 |

**自动售货机中**：
- 全部使用 **Commit**
- 只有在同一单元格有多个迁移时才慎重考虑（本次不适用）

### 5.4 迁移条件表达式

迁移可以设置**条件表达式**。只有条件为 `true` 时才迁移。

| 例 | 含义 |
|----|------|
| （空） | 无条件（一定迁移） |
| `current_speed >= target_speed` | 速度达到目标值以上 |
| `coin_total >= price` | 投入金额达到价格以上 |
| `retry_count < 3` | 重试次数小于 3 |

**Driver 层中**：
- 本次无条件表达式（仅无条件迁移）
- 上层（Application）会使用条件表达式

### 5.5 迁移标签（T1, T2, ...）

同一单元格有多个迁移时，用**标签**识别。

| 标签 | 用途 |
|-------|------|
| `T1` | 第 1 个迁移 |
| `T2` | 第 2 个迁移 |

**Driver 层中**：
- 每个单元格只有一个，因此标签只有 `T1`

### 5.6 具体操作步骤

#### 编辑单元格 (HwIdle, HW_ENABLE)

1. **双击** **HwIdle** 列 × **HW_ENABLE** 行 的单元格
2. 打开 **ActionEditorDialog**（5 个标签页）
3. 选择 **Transitions** 标签页
4. 点击 **Add** 按钮
5. 输入以下值：

   | 字段 | 值 |
   |-----------|-----|
   | Source | `HwIdle` |
   | Event | `HW_ENABLE` |
   | Target | `HwActive` |
   | Condition | （空） |
   | Mode | `Commit` |
   | Title | `HW 启用` |
   | Label | `T1` |

6. 点击 OK
7. 矩阵单元格中显示 `HW 启用 (HW_ENABLE) [Commit] <T1>`

#### 同样添加剩余 3 个迁移

- (HwActive, HW_DISABLE) -> HwIdle
- (HwActive, HW_ERROR) -> HwError
- (HwError, HW_DISABLE) -> HwIdle

### 5.7 确认 Driver 层的矩阵

              | HwIdle              | HwActive             | HwError
    ----------+---------------------+----------------------+---------------------
    HW_ENABLE | HW 启用 [Commit]    |                      |
              | <T1>                |                      |
    HW_DISABLE|                     | HW 禁用 [Commit]     | HW 恢复 [Commit]
              |                     | <T1>                 | <T1>
    HW_MOTOR_ |                     | （单元格动作）        |
      START   |                     |                      |
    HW_MOTOR_ |                     | （单元格动作）        |
      STOP    |                     |                      |
    HW_ERROR  |                     | HW 错误 [Commit]     |
              |                     | <T1>                 |

**Driver 层的迁移完成。**

---

## 6. 步骤4：完成单元格（首次注册 Role 函数）

### 6.1 什么是单元格动作

**单元格动作** = 独立于迁移执行的附加处理。

| 种类 | 执行时机 |
|------|--------------|
| `before_transitions` | 该单元格的迁移评估**前** |
| `after_transitions` | 该单元格的迁移评估**后** |

#### 迁移与单元格动作的区别

| 项目 | 迁移 | 单元格动作 |
|------|------|--------------|
| 目的 | 改变状态 | 附带处理 |
| 例 | HwIdle → HwActive | 电机转动、日志输出 |
| 条件 | 可用表达式控制 | 总是执行 |
| 效果 | 决定次状态 | 仅副作用 |

### 6.2 添加单元格动作

#### Driver 层要添加的单元格动作

| # | 单元格 | 时机 | 功能 |
|---|------|-----------|------|
| 1 | (HwActive, HW_MOTOR_START) | before | `DriveMotor` |
| 2 | (HwActive, HW_MOTOR_STOP) | before | `StopMotor` |
| 3 | (HwError, HW_ERROR) | after | `WriteLcd` |

### 6.3 当场添加 Role 函数

**重要**：添加单元格动作时，如果 **Role 函数尚未注册**，
就在那里添加。

#### 操作步骤

1. 双击单元格 (HwActive, HW_MOTOR_START)
2. **ActionEditorDialog** → **Pre / Post Actions** 标签页
3. 点击 **Add (Pre)** 按钮
4. 打开 Role 函数选择对话框
5. 查找 **`DriveMotor`** → **找不到**
6. 点击 **Cancel** 关闭
7. 也 Cancel **ActionEditorDialog**
8. **SettingsPanel → Role function** 标签页
9. 用 **Add** 按钮添加 Role 函数：

   | 字段 | 值 |
   |-----------|-----|
   | Function name | `DriveMotor` |
   | Namespace | `Driver` |
   | Display name | 电机驱动 |
   | Description | 电机转动指定角度 |

10. OK
11. 再次双击单元格 → 在 Role 函数选择中选择 `DriveMotor`

> **要点**：实践"需要时添加"。
> 不必预先创建全部 Role 函数。

#### Driver 层需要的 Role 函数（5 个）

| # | Function name | Namespace | Display name |
|---|--------------|-----------|--------------|
| 1 | `InitHardware` | `Driver` | 初始化硬件 |
| 2 | `DriveMotor` | `Driver` | 电机驱动 |
| 3 | `StopMotor` | `Driver` | 停止电机 |
| 4 | `WriteLcd` | `Driver` | 写入 LCD |
| 5 | `ReadKeypad` | `Driver` | 读取键盘 |

#### Namespace 的作用

Role 函数有 **Namespace**。这表示**部件所属的层**。

| 设置 | 效果 |
|------|------|
| Namespace = `Driver` | 视为 `Driver.DriveMotor` |
| Namespace = （空） | 视为 `DriveMotor` |

**Namespace 下拉框中显示所有标签页的层名作为候选。**
这样可以明确选择部件属于哪一层。

### 6.4 添加单元格关系

**单元格关系** = 一个单元格内有多个迁移时的关系。

| 种类 | 含义 |
|------|------|
| `sequential` | 按顺序评估（默认） |
| `exclusive` | 最多只有 1 个触发 |
| `group` | 分组，共享条件外移 |

**Driver 层中**：
- 每个单元格只有一个，因此**不需要关系**

**Application 层中**：
- 在有多个迁移的单元格中使用（后述）

---

## 7. 步骤5：完成状态

### 7.1 什么是 entry / exit 动作

状态可以设置 **entry** 和 **exit** 动作。

| 动作 | 时机 |
|-----------|-----------|
| **entry** | **进入**该状态时 |
| **exit** | **离开**该状态时 |

#### 与迁移的区别

| 项目 | 迁移 | entry / exit |
|------|------|-------------|
| 执行时机 | 跨越状态时 | 状态进出时 |
| 执行顺序 | 迁移评估 → 执行 | exit → 迁移 → entry |

### 7.2 设置 entry / exit

#### Driver 层的 entry / exit

| # | 状态 | entry | exit |
|---|------|-------|------|
| 1 | HwIdle | `InitHardware` | （无） |
| 2 | HwActive | （无） | `StopMotor` |
| 3 | HwError | `WriteLcd` | （无） |

#### 操作步骤

1. **SettingsPanel → State list** 标签页
2. 双击 `HwIdle` 行的 **entry function** 列
3. 打开 **ActionEditDialog**
4. 选择 `InitHardware`
5. OK

### 7.3 Driver 层完成确认

#### 检查表

- [ ] 状态 3 个（HwIdle / HwActive / HwError）
- [ ] 事件 5 个（HW_ENABLE / HW_DISABLE / HW_MOTOR_START / HW_MOTOR_STOP / HW_ERROR）
- [ ] 迁移 4 个
- [ ] 单元格动作 3 个
- [ ] entry / exit 3 个
- [ ] Role 函数 5 个

**Driver 层完成。接下来是 Middleware 层。**

---

## 8. 步骤6：同样完成其他层

### 8.1 添加 Middleware 层的迁移

#### Middleware 层要添加的迁移

| # | 状态 | 事件 | 目标 | 条件 | 模式 |
|---|------|---------|--------|------|--------|
| 1 | MwIdle | MW_START_COIN | CoinAccepting | （无） | Commit |
| 2 | CoinAccepting | MW_COIN_VALID | MwIdle | （无） | Commit |
| 3 | CoinAccepting | MW_COIN_INVALID | MwIdle | （无） | Commit |
| 4 | MwIdle | MW_START_DISPENSE | Dispensing | （无） | Commit |
| 5 | Dispensing | MW_DISPENSE_DONE | MwIdle | （无） | Commit |
| 6 | MwIdle | MW_START_CHANGE | ChangeCalculating | （无） | Commit |
| 7 | ChangeCalculating | MW_CHANGE_DONE | MwIdle | （无） | Commit |

#### 单元格动作

| # | 单元格 | 时机 | 功能 |
|---|------|-----------|------|
| 1 | (CoinAccepting, MW_COIN_VALID) | before | `AccumulateCoin` |
| 2 | (Dispensing, MW_DISPENSE_DONE) | before | `StopDispense` |
| 3 | (ChangeCalculating, MW_CHANGE_DONE) | before | `DispenseChange` |

#### entry / exit

| # | 状态 | entry | exit |
|---|------|-------|------|
| 1 | CoinAccepting | `ValidateCoin` | （无） |
| 2 | Dispensing | `DispenseProduct` | （无） |
| 3 | ChangeCalculating | `CalculateChange` | （无） |

#### Middleware 层需要的 Role 函数（6 个）

| # | Function name | Namespace |
|---|--------------|-----------|
| 1 | `ValidateCoin` | `Middleware` |
| 2 | `AccumulateCoin` | `Middleware` |
| 3 | `DispenseProduct` | `Middleware` |
| 4 | `StopDispense` | `Middleware` |
| 5 | `CalculateChange` | `Middleware` |
| 6 | `DispenseChange` | `Middleware` |

### 8.2 添加 Application 层的迁移

#### Application 层要添加的迁移

| # | 状态 | 事件 | 目标 | 条件 | 模式 |
|---|------|---------|--------|------|--------|
| 1 | Idle | SELECT | ProductSelected | （无） | Commit |
| 2 | ProductSelected | COIN_IN | AwaitingPayment | （无） | Commit |
| 3 | AwaitingPayment | CONFIRM | Dispensing | （无） | Commit |
| 4 | Dispensing | DISPENSE_DONE | ReturningChange | `change_amount > 0` | Commit |
| 5 | Dispensing | DISPENSE_DONE | Idle | `change_amount == 0` | Commit |
| 6 | ReturningChange | CHANGE_DONE | Idle | （无） | Commit |
| 7 | （任意状态） | ERROR | Error | （无） | Commit |
| 8 | Error | RESET | Idle | （无） | Commit |

### 8.3 添加单元格关系（Application 层）

单元格 (Dispensing, DISPENSE_DONE) 有 2 个迁移：

- T1: ReturningChange（条件：`change_amount > 0`）
- T2: Idle（条件：`change_amount == 0`）

两者互斥，因此使用 `exclusive`。

| 单元格 | 关系 |
|------|---------|
| (Dispensing, DISPENSE_DONE) | exclusive |

### 8.4 Application 层需要的 Role 函数（8 个）

| # | Function name | Namespace |
|---|--------------|-----------|
| 1 | `ShowProductList` | `Application` |
| 2 | `HighlightProduct` | `Application` |
| 3 | `CalculateTotal` | `Application` |
| 4 | `CheckSufficientFunds` | `Application` |
| 5 | `RequestDispense` | `Application` |
| 6 | `RequestChange` | `Application` |
| 7 | `ShowError` | `Application` |
| 8 | `ResetSystem` | `Application` |

### 8.5 单元格动作 / entry / exit（Application 层）

#### 单元格动作

| # | 单元格 | 时机 | 功能 |
|---|------|-----------|------|
| 1 | (Idle, SELECT) | before | `ShowProductList` |
| 2 | (ProductSelected, COIN_IN) | after | `HighlightProduct` |
| 3 | (AwaitingPayment, CONFIRM) | before | `CheckSufficientFunds` |
| 4 | (Error, RESET) | before | `ResetSystem` |

#### entry / exit

| # | 状态 | entry | exit |
|---|------|-------|------|
| 1 | ProductSelected | `HighlightProduct` | （无） |
| 2 | Dispensing | `RequestDispense` | （无） |
| 3 | ReturningChange | `RequestChange` | （无） |
| 4 | Error | `ShowError` | （无） |

### 8.6 三层全部完成确认

| 层 | 状态 | 事件 | 迁移 | 单元格动作 | entry/exit | Role 函数 |
|---|-----|---------|------|--------------|-----------|----------|
| Driver | 3 | 5 | 4 | 3 | 3 | 5 |
| Middleware | 4 | 7 | 7 | 3 | 3 | 6 |
| Application | 6 | 8 | 8 | 4 | 4 | 8 |
| **合计** | **13** | **20** | **19** | **10** | **10** | **19** |

**三层的组装全部完成。**

---

## 9. 步骤7：用图确认

### 9.1 Mermaid 图的阅读方式

StaTable 的状态迁移图以**从左到右流动的横型**显示。

    +------+   START    +------+   TIMER   +------+
    | Idle | ---------> |Blink | --------> |Off   |
    +------+            +------+           +------+

#### 为什么是横型

| # | 理由 |
|---|------|
| 1 | **进行方向直观** — 时间流向用左→右表现 |
| 2 | **利用屏幕宽度** — 显示器是横向的 |
| 3 | **状态排列易看** — 同列状态易于比较 |
| 4 | **与矩阵对应** — 与矩阵的列（状态）顺序一致 |

### 9.2 确认各层的图

切换三个标签页，确认**与纸面草图是否一致**。

#### 确认项目

| # | 确认内容 |
|---|---------|
| 1 | 所有状态是否可达 |
| 2 | 是否有终止状态（无法离开的状态） |
| 3 | 是否画出了所有预期的迁移 |
| 4 | 条件表达式是否正确显示 |

### 9.3 设置层优先级

决定运行时各层的执行顺序。

#### 操作步骤

1. 菜单 **Edit → Layer Settings...**
2. 打开 LayerSettingsDialog
3. 设置各层优先级：

   | 层 | 优先级 | 含义 |
   |---|-------|------|
   | Driver | `1` | 最优先（硬件控制） |
   | Middleware | `5` | 中间 |
   | Application | `9` | 最下位（销售逻辑） |

   > **优先级的含义**：数值越小越优先（1～9）

4. OK

#### 执行顺序

    1. Driver 层的状态机处理
           |
    2. Middleware 层的状态机处理
           |
    3. Application 层的状态机处理

### 9.4 出现问题时如何修正

| 问题 | 原因 | 对策 |
|------|------|------|
| 图中无迁移 | 单元格为空 | 双击单元格添加迁移 |
| 有孤立状态 | 迁移未定义 | 添加进入该状态的迁移 |
| 条件表达式未显示 | 条件表达式为空 | 在迁移编辑中输入条件 |
| 标签重复 | 同一标签被多次使用 | 重新编号为 T1, T2, ... |

---
# 正文 — 完成

---

## 10. 步骤8：生成 C 代码

### 10.1 设置输出位置

1. 菜单 **Code generation → Generation settings...**（**Ctrl+Shift+G**）
2. 打开 CodeGenerationSettingsDialog
3. **Output settings** 标签页
4. 设置以下内容：

   | 项目 | 值 |
   |------|-----|
   | Output directory | （例：C:\projects\vending_machine\output） |
   | Folder structure | `by_layer`（推荐） |
   | Save with merge | ✅ 勾选 |

5. OK

### 10.2 生成

1. 菜单 **Code generation → Code generation...**（**Ctrl+G**）
2. 打开 CodeGenerationDialog
3. 点击 **Generate** 按钮
4. 确认生成完成的消息

### 10.3 确认生成的文件

#### by_layer 结构

    output/
    +-- Driver/
    |   +-- statable_types_Driver.h
    |   +-- statable_transitions_Driver.c / .h
    |   +-- statable_role_functions_Driver.c / .h
    +-- Middleware/
    |   +-- （同样的 5 个文件）
    +-- Application/
    |   +-- （同样的 5 个文件）
    +-- include/
    |   +-- statable_types_common.h
    +-- src/
    |   +-- statable_init.c
    |   +-- statable_event_queue.c
    |   +-- statable_interrupt.c
    |   +-- statable_timer.c
    |   +-- Untitled_run.c
    +-- common/
        +-- osal.h / osal.c
        +-- statable_all.h

> **注**：层别文件（15 个）+ 共通文件（10 个）= **共 25 个文件**。

### 10.4 单元格函数示例

来自 `statable_transitions_Driver.c`：

    static STATE_Driver_t t_HwIdle_HW_ENABLE(
        const Transition_t* transition,
        TransitionContext_Driver_t* ctx)
    {
        STATE_Driver_t next_state = STATE_Driver_HwIdle;
        if (1) {
            next_state = STATE_Driver_HwActive;  /* [Commit] */
        }
        return next_state;
    }

### 10.5 Role 函数中的用户代码区域

来自 `statable_role_functions_Driver.c`：

    int RoleFunc_Driver_DriveMotor(
        const TransitionContext_Driver_t *transition,
        SystemContext_t *ctx)
    {
        (void)ctx;
        /* [[STABLE_USER_CODE_START:Driver_DriveMotor]] */
        /* Write user implementation code here */
        /* [[STABLE_USER_CODE_END:Driver_DriveMotor]] */
        return 0;
    }

> **重要**：用户代码写在 `[[STABLE_USER_CODE_START:...]]` 与
> `[[STABLE_USER_CODE_END:...]]` 之间。
> **不要删除或重命名标记** — 重新生成时用户代码会丢失。

---

## 11. 步骤9：集成到嵌入式

### 11.1 集成整体图

    1. 在 main.c 中调用 SystemContext_Init
    2. 在主循环中按优先级顺序处理各层
    3. 在 Role 函数的标记内编写用户代码

### 11.2 main.c 的最小结构

    #include "statable_all.h"
    #include "board.h"

    int main(void)
    {
        SystemContext_t ctx;
        board_init();
        SystemContext_Init(&ctx);
        __enable_irq();
        while (1) {
            /* Driver 层（最优先） */
            EVENT_Driver_t drv_ev =
                StateMachine_GetNextEvent_Driver(&ctx);
            if (drv_ev != EVENT_Driver_NONE) {
                (void)StateMachine_Process_Driver(drv_ev, &ctx);
            }
            /* Middleware 层 */
            EVENT_Middleware_t mw_ev =
                StateMachine_GetNextEvent_Middleware(&ctx);
            if (mw_ev != EVENT_Middleware_NONE) {
                (void)StateMachine_Process_Middleware(mw_ev, &ctx);
            }
            /* Application 层 */
            EVENT_Application_t app_ev =
                StateMachine_GetNextEvent_Application(&ctx);
            if (app_ev != EVENT_Application_NONE) {
                (void)StateMachine_Process_Application(app_ev, &ctx);
            }
            /* 其他任务 */
            board_background_task();
        }
    }

### 11.3 中断与定时器设置概要

#### 投币 ISR 示例

    void COIN_IRQHandler(void)
    {
        COIN_SENSOR->SR = 0;
        StateMachine_EnqueueEvent(
            &g_system_ctx,
            EVENT_Application_COIN_IN
        );
    }

#### 定时器 ISR 示例

    void SysTick_Handler(void)
    {
        g_system_tick++;
        if ((g_system_tick % 1000) == 0) {
            StateMachine_EnqueueEvent(
                &g_system_ctx,
                EVENT_Application_TIMEOUT
            );
        }
    }

### 11.4 在 Role 函数中实现用户代码

    int RoleFunc_Driver_DriveMotor(
        const TransitionContext_Driver_t *transition,
        SystemContext_t *ctx)
    {
        (void)ctx;
        /* [[STABLE_USER_CODE_START:Driver_DriveMotor]] */
        Motor_SetDirection(MOTOR_FORWARD);
        Motor_SetSpeed(200);
        Motor_Start();
        /* [[STABLE_USER_CODE_END:Driver_DriveMotor]] */
        return 0;
    }

### 11.5 详细内容请参考 INTEGRATION_GUIDE_ja.md

集成细节（NonRTOS / FreeRTOS / ISR 设置等）请参考
INTEGRATION_GUIDE_ja.md。

---

## 12. 步骤10：保存项目

### 12.1 保存

1. 菜单 **File → Save Project...**
2. 指定保存位置（例：VendingMachine.xml）
3. 保存

### 12.2 保存的内容

| 保存对象 | 内容 |
|---------|------|
| 全部标签页的状态机 | 状态 / 事件 / 迁移 / Role 函数 |
| 全局定义 | 变量 / 标志 / 中断 / 定时器 |
| 共享库 | Role 函数 / 条件 / 字面量 |
| 项目设置 | 代码生成设置 |

### 12.3 用户代码的处理

**重要**：用户代码（标记内）**不保存在 XML 中，而保存在 C 文件中**。

    VendingMachine.xml        <- 设计信息（由 StaTable 读写）
    output/                   <- 生成的 C 代码（含用户代码）
      +-- Driver/
          +-- statable_role_functions_Driver.c  <- 用户代码

XML 中只有设计信息。用户代码保留在 C 文件中。

---

# 应用篇

---

## 13. 复用现有项目

### 13.1 复用设计的场景

**场景**：开发了饮料自动售货机后，
**复用同一 Driver / Middleware 来开发咖啡机**。

#### 产品差异

| 项目 | 饮料售货机（现有） | 咖啡机（新） |
|------|-----------------|---------------------|
| 商品 | 罐装饮料 | 咖啡（杯） |
| 选择方法 | 按钮（每种商品） | 按钮（种类选择） |
| 提供方法 | 商品滑道 | 杯子 + 萃取机构 |
| 附加功能 | 无 | 热水、牛奶、糖 |
| Application 层 | 饮料销售逻辑 | 咖啡萃取逻辑 |

#### 为什么以"咖啡机"为题材

| # | 理由 |
|---|---|
| 1 | **Driver / Middleware 完全可复用** — 电机、硬币处理、LCD 都相同 |
| 2 | **差异集中在 Application 层** — 层独立性的优势明确 |
| 3 | **产品现实性强** — 真实存在的产品构成 |
| 4 | **学习效果最大化** — "改哪里、不改哪里"一目了然 |

### 13.2 可复用 / 不可复用的内容

| 层 | 复用 | 理由 |
|---|---------|------|
| **Driver 层** | ✅ **完全复用** | 电机、硬币、LCD 都相同 |
| **Middleware 层** | ✅ **完全复用** | 商品出货、找零计算都相同 |
| **Application 层** | ❌ **新建** | 咖啡萃取逻辑不同 |

#### 开发周期缩短效果

| 层 | 新开发 | 复用 |
|---|---------|------|
| Driver | 0% | **100%** |
| Middleware | 0% | **100%** |
| Application | 100% | 0% |
| **整体** | **约 33%** | **约 67%** |

**这是复用设计的最大优势 —— 可以省略 2/3 的开发。**

### 13.3 打开现有项目

1. 菜单 **File → Open Project...**
2. 选择 VendingMachine.xml
3. 加载完成

**结果**：三层全部恢复。

### 13.4 只替换 Application 层

#### 操作步骤

1. 选择 **Application** 标签页
2. 编辑状态、事件、迁移
3. Role 函数也只编辑 Application 层的
4. **不要触碰** Driver / Middleware 标签页

### 13.5 层独立性带来的优势

| # | 优势 |
|---|---|
| 1 | **无需修改 Driver / Middleware** |
| 2 | **只需重写 Application 层的测试** |
| 3 | **可以原样使用硬件控制的实绩** |
| 4 | **大幅缩短开发周期** |

### 13.6 共享库的活用（可选）

项目整体使用的通用函数，注册到共享库。

| # | 例 | 用途 |
|---|---|---|
| 1 | Log | 日志输出 |
| 2 | Delay | 等待 |
| 3 | CheckSum | 校验和计算 |

#### 注册到共享库

1. **File → Open Project** 打开 XML 时，共享库也会恢复
2. 新建标签页时，共享库的函数会作为候选项显示
3. 通过分离 namespace 避免冲突

---

## 14. 迭代开发

### 14.1 设计变更 → 重新生成的流程

    1. 修改设计（添加功能 / 修正迁移）
           |
    2. 重新生成（Save Generated Code）
           |
    3. code_merger.py 自动合并
           |
    4. 用户代码被保留

### 14.2 用户代码保护（合并）

#### 标记机制

    /* [[STABLE_USER_CODE_START:Driver_DriveMotor]] */
    Motor_SetSpeed(200);   <- 用户编写的实现
    /* [[STABLE_USER_CODE_END:Driver_DriveMotor]] */

重新生成时，标记之间的代码会**保留**。

#### 标记类型

| 标记 | 用途 |
|---------|------|
| STABLE_USER_CODE_START / END | 文件级 |
| STABLE_USER_CODE_START:<name> / END:<name> | 函数级 |
| STABLE_USER_CODE_TAIL_START / END | 文件末尾 |

### 14.3 幂等性的保证

**同一设计多次重新生成，文件大小不会增加。**

已验证：tests/test_v2_4_p1_merge.py Test [3]

### 14.4 验证 / AI 诊断的活用

#### 验证功能

1. 菜单 **Validate → Validation / AI diagnosis...**（**Ctrl+Shift+V**）
2. 打开 ValidationDialog
3. 点击 **Validate** 运行验证

#### 验证项目（35 条规则）

| 类别 | 规则数 |
|---------|---------|
| state | 4 |
| event | 2 |
| transition | 5 |
| role_function | 3 |
| variable | 3 |
| flag | 2 |
| queue | 2 |
| interrupt | 2 |
| timer | 2 |
| custom_type | 2 |
| cell | 8 |
| **合计** | **35** |

---
# 总结

---

## 15. 作业 × 功能 对照表

### 15.1 步骤一览

| # | 步骤 | 章 |
|---|------|-----|
| 1 | 创建项目 | 3 |
| 2 | 构建骨架（状态 + 事件） | 4 |
| 3 | 构建迁移 | 5 |
| 4 | 完成单元格 | 6 |
| 5 | 完成状态 | 7 |
| 6 | 完成其他层 | 8 |
| 7 | 用图确认 | 9 |
| 8 | 生成 C 代码 | 10 |
| 9 | 集成到嵌入式 | 11 |
| 10 | 保存项目 | 12 |

### 15.2 功能一览

| 作业 | 使用的功能 |
|------|---------|
| 新建项目 | File → New Project |
| 打开项目 | File → Open Project |
| 保存项目 | File → Save Project |
| 添加新层（标签页） | File → New State Machine |
| 定义状态 | SettingsPanel → State list |
| 定义事件 | SettingsPanel → Event definitions |
| 定义 Role 函数 | SettingsPanel → Role function |
| 定义变量 | Edit → Global Definitions |
| 添加迁移 | MatrixTable → 双击单元格 |
| 添加单元格动作 | ActionEditorDialog → Pre/Post Actions |
| 添加单元格关系 | ActionEditorDialog → Relations |
| 设置 entry / exit | State list → 双击单元格 |
| 用图确认 | MermaidWidget（自动更新） |
| 生成 C 代码 | Code generation → Generate |
| 设置层优先级 | Edit → Layer Settings |
| 验证 | Validate → Validation |

### 15.3 快捷键一览

| 快捷键 | 功能 |
|--------------|------|
| Ctrl+N | New Project |
| Ctrl+G | Code generation |
| Ctrl+Shift+G | Generation settings |
| Ctrl+Shift+S | Save generated code |
| Ctrl+Shift+V | Validation / AI diagnosis |

---

## 16. 常见问题（FAQ）

**Q1. 为什么先注册全部状态和事件？**
A. 注册状态和事件后，迁移矩阵的框架会自动生成。
可以边看设计图边作业，适合探索式设计。

**Q2. 为什么从 Driver 层开始？**
A. 因为与依赖关系的方向一致。Driver 层不知道 Application 层的存在，
从下层构建可以减少返工。此外，Driver 层是"机器能做什么"的定义，
一旦确定，上层设计就会顺利推进。

**Q3. Role 函数什么时候注册？**
A. 需要时注册。不必预先创建全部。

**Q4. 可以把多个状态机放到一个项目里吗？**
A. 可以。每个标签页可以有独立的 StateMachine。

**Q5. 层间应该共享 Role 函数吗？**
A. 不推荐。为保持层的独立性，请按层定义函数。

**Q6. 图为什么是横型？**
A. 为了用左→右表达时间流向，并利用横向显示器。
排列顺序与矩阵的列（状态）一致，对应关系也容易看清。

---

## 17. 下一步

### 17.1 学习路径

    本教程（已完成）
           |
    INTEGRATION_GUIDE_ja.md（嵌入式集成）
           |
    SPEC_OVERVIEW_ja.md（详细规格）

### 17.2 参考文档

| # | 目的 | 参考文档 |
|---|------|-----------------|
| 1 | 将生成代码集成到嵌入式 | INTEGRATION_GUIDE_ja.md |
| 2 | 验证规则详情 | SPEC_OVERVIEW_ja.md 7.5 |
| 3 | MISRA 应对 | SPEC_OVERVIEW_ja.md 7.4 |
| 4 | GUI 画面详情 | SPEC_SCREENS_ja.md |
| 5 | 作为 SDK 使用 | SPEC_SDK_API_en.md |
| 6 | 用户代码指南 | USER_CODE_GUIDE_zh.md（本仓库） |

---

# 附录

---

## A. 标记参考

| 标记 | 用途 |
|---------|------|
| STABLE_USER_CODE_START / END | 文件级用户代码区域 |
| STABLE_USER_CODE_START:<name> / END:<name> | 函数级用户代码区域 |
| STABLE_USER_CODE_TAIL_START / END | 文件末尾用户代码区域 |

---

## B. 术语对照表

| StaTable 术语 | 一般称呼 | 本教程称呼 |
|--------------|-------------|----------------------|
| Role 函数 | 函数 / 方法 | 部件（功能） |
| State | 状态 | 状态 |
| Event | 事件 / 信号 | 触发 |
| Transition | 迁移 | 迁移 |
| Layer | 层 | 层 |
| Namespace | 命名空间 | 命名空间 |
| Cell | 单元格 | 单元格 |

---

## C. 术语集

### C.1 基本术语

| 术语 | 说明 | 出现章节 |
|------|------|-------|
| Layer（层） | 每个标签页的状态机群 | 2.2 |
| State（状态） | 动作模式 | 2.3 |
| Event（事件） | 改变状态的触发 | 2.4 |
| Transition（迁移） | "A 状态下 X 事件到达则转到 B" | 5.2 |
| Cell（单元格） | (状态, 事件) 的组合 | 5.1 |

### C.2 Role 函数相关

| 术语 | 说明 | 出现章节 |
|------|------|-------|
| Role 函数 | 用于条件评估和动作的函数（部件） | 1.4 |
| namespace | Role 函数所属的层 | 6.3 |
| qualified_name | namespace.name 形式 | 6.3 |
| 部件 | 本教程对 Role 函数的称呼 | 1.4 |

### C.3 迁移相关

| 术语 | 说明 | 出现章节 |
|------|------|-------|
| Commit | early_return=True（停止后续迁移） | 5.3 |
| Tentative | early_return=False（可被覆盖） | 5.3 |
| 条件表达式 | 迁移成立的条件 | 5.4 |
| 标签（T1, T2, ...） | 单元格内迁移的标识符 | 5.5 |

### C.4 单元格相关

| 术语 | 说明 | 出现章节 |
|------|------|-------|
| 单元格动作 | 独立于迁移的附带处理 | 6.1 |
| before_transitions | 迁移评估前 | 6.1 |
| after_transitions | 迁移评估后 | 6.1 |
| 单元格关系 | 单元格内迁移间的关系 | 6.4 |
| sequential | 按顺序评估 | 6.4 |
| exclusive | 最多只有 1 个触发 | 6.4 |
| group | 分组，共享条件外移 | 6.4 |

### C.5 状态动作

| 术语 | 说明 | 出现章节 |
|------|------|-------|
| entry | 进入状态时的动作 | 7.1 |
| exit | 离开状态时的动作 | 7.1 |

### C.6 代码生成相关

| 术语 | 说明 | 出现章节 |
|------|------|-------|
| 标记 | 用于保留用户代码的注释 | 10.5 |
| 合并 | 生成代码与既有代码的统合 | 14.2 |
| 幂等性 | 多次执行结果相同 | 14.3 |
| 单元格函数 | 处理一个单元格的 static 函数 | 10.4 |

### C.7 绘制相关

| 术语 | 说明 | 出现章节 |
|------|------|-------|
| Mermaid | 状态迁移图生成引擎 | 9.1 |
| 横型（LR） | 从左到右流动的状态迁移图 | 9.1 |

### C.8 规范相关

| 术语 | 说明 | 出现章节 |
|------|------|-------|
| MISRA C:2012 | 车载 C 语言规范 | 14.4 |
| cppcheck | 静态分析工具 | 14.4 |

### C.9 其他

| 术语 | 说明 | 出现章节 |
|------|------|-------|
| Tab（标签页） | 表示层的 UI 元素 | 3.3 |
| Matrix（矩阵） | 迁移矩阵（状态 × 事件） | 4.1 |
| SettingsPanel | 右侧的设置面板 | 3.3 |
| MermaidWidget | 下方的图显示控件 | 9.1 |
| ISR | 中断服务例程 | 11.3 |
| OSAL | OS 抽象层 | 10.4 |

---

## D. 变更历史

| 版本 | 日期 | 内容 |
|-----------|------|------|
| 2.0 | 2026-10-04 | 中文完整版。按骨架 → 矩阵 → 完成的结构编排 |
| 1.2 | 2026-09-26 | XML 参考版 |

---

End of TUTORIAL_zh.md v2.0