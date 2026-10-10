"""v3.4.3 doc alignment — Stage B-2g: update §3 design theory.

Replaces §3.1-3.3 (from `### 3.1 为什么需要七层` to `## 4. 实现详解`)
with a 7-layer version (Driver -> DriverInput / DriverOutput).
"""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "LAYER_DESIGN_zh.md")

START_MARKER = "### 3.1 为什么需要七层"
END_MARKER = "## 4. 实现详解"

NEW_BLOCK = """### 3.1 为什么需要七层

#### 3.1.1 单一状态机的问题

假设所有功能放入 1 个状态机：

```mermaid
flowchart LR
    S1[Idle] --> S2[Cooking]
    S2 --> S3[Microwave]
    S2 --> S4[Oven]
    S2 --> S5[Grill]
    S2 --> S6[Steam]
    S2 --> S7[Combo]
    S3 --> S8[Error]
    S4 --> S8
    S5 --> S8
    S6 --> S8
    S7 --> S8
```

问题点：

| # | 问题 |
|---|---|
| 1 | 状态数爆炸（各加热方式 × 各异常 = 数十状态） |
| 2 | 状态迁移条件复杂（`if (mode == MICROWAVE && temp > X && ...)`） |
| 3 | 测试困难（1 个状态变更影响全体） |
| 4 | 并列加热（微波 + 蒸汽）难以表达 |

#### 3.1.2 分层后的效果

```mermaid
flowchart TB
    App["Application<br/>5 状态"]
    Mw1["MwMicrowave<br/>4 状态"]
    Mw2["MwOven<br/>3 状态"]
    Mw3["MwGrill<br/>3 状态"]
    Mw4["MwSteam<br/>5 状态"]
    DrvIn["DriverInput<br/>5 状态"]
    DrvOut["DriverOutput<br/>6 状态"]

    App --> Mw1
    App --> Mw2
    App --> Mw3
    App --> Mw4
    Mw1 --> DrvIn
    Mw1 --> DrvOut
    Mw2 --> DrvIn
    Mw2 --> DrvOut
    Mw3 --> DrvIn
    Mw3 --> DrvOut
    Mw4 --> DrvIn
    Mw4 --> DrvOut
```

| # | 效果 |
|---|---|
| 1 | 状态数线性增长（5 + 4 + 3 + 3 + 5 + 5 + 6 = 31，而非 数十） |
| 2 | 各层独立测试可能 |
| 3 | 并列加热 = Application 层同时激活多个中间层 |
| 4 | 新加热方式 = 新中间层追加（既有层不变） |
| 5 | Driver 分离为输入系 / 输出系，责任明确 |

### 3.2 各层职责

#### 3.2.1 职责划分原则

| # | 原则 |
|---|---|
| 1 | **下层不知道上层存在**（单向依赖） |
| 2 | **中间层之间不直接通信**（通过 Application 层协调） |
| 3 | **DriverInput / DriverOutput 层只做 HW 抽象**（无业务逻辑） |
| 4 | **Application 层只做序列**（无 HW 操作） |

#### 3.2.2 职责一览

| 层 | 输入 | 处理 | 输出 |
|---|---|---|---|
| **DriverInput** | HW 信号（ADC / 门 / ZC）、串行数据 | 传感器读取、移动平均、事件发行 | 事件 → 中间层 |
| **DriverOutput** | 中间层指令 | 加热器 / 风扇 / 磁控管 PWM、串行发送 | HW 输出、状态报告 |
| **MwMicrowave** | Application 指令 | 磁控管起停、功率控制 | 加热、事件 |
| **MwOven** | Application 指令 | PID 温控、热风、加热管 | 加热、事件 |
| **MwGrill** | Application 指令 | 烧烤加热管控制 | 加热、事件 |
| **MwSteam** | Application 指令 | 锅炉控制、脉冲注水 | 蒸汽、事件 |
| **Application** | Android 序列 | 序列解析、阶段推进 | 中间层指令、报告 |

### 3.3 层间通信原则

#### 3.3.1 通信方式：事件驱动

```mermaid
sequenceDiagram
    participant Android
    participant DrvIn as DriverInput
    participant DrvOut as DriverOutput
    participant App as Application
    participant Mw as MwMicrowave

    Android->>DrvIn: 序列数据（串行 RX）
    DrvIn->>App: SEQ_RECEIVED 事件
    App->>Mw: MW_START 事件
    Mw->>DrvOut: 加热器 PWM 设置
    DrvIn->>DrvIn: 传感器读取 + 移动平均
    DrvIn->>Mw: THERM_UPDATE 事件
    Mw->>App: STAGE_DONE 事件
    App->>DrvOut: 状态报告（串行 TX）
    DrvOut->>Android: 状态报告
```

#### 3.3.2 事件类型

| 方向 | 事件示例 | delivery |
|---|---|---|
| DriverInput → 中间层 | `THERM_UPDATE`, `IR_READY` | queue |
| DriverInput → 中间层 | `HW_FAULT` | queue |
| 中间层 → DriverOutput | （通过 RoleFunc 直接调用） | — |
| 中间层 → Application | `STAGE_DONE`, `OVERHEAT` | direct |
| Application → DriverOutput | （通过 RoleFunc 直接调用） | — |

#### 3.3.3 数据流：共享变量

除了事件之外，通过 **GlobalDefinitions 的变量**共享数据：

| 变量 | 更新元 | 参照元 |
|---|---|---|
| `thermistor_top` | DriverInput | MwOven, MwGrill |
| `ir_value` | DriverInput | Application |
| `steam_sensor` | DriverInput | MwSteam |
| `oven_target_temp` | Application | MwOven |
| `mw_power` | Application | MwMicrowave |

**原则**：**更新仅由 1 层负责，参照可由多层进行**（读写分离）。

---
"""


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")

    # Idempotency: check for new markers
    if "DriverInput / DriverOutput 层只做 HW 抽象" in text:
        print("[SKIP] §3 already updated")
        return 0

    s = text.find(START_MARKER)
    e = text.find(END_MARKER)
    if s == -1 or e == -1 or e <= s:
        print(f"[ERR] markers not found or out of order (s={s}, e={e})")
        return 1

    old_block = text[s:e]
    new_text = text[:s] + NEW_BLOCK + text[e:]
    DOC.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK] LAYER_DESIGN_zh.md: §3.1-3.3 updated")
    print(f"     old: {len(old_block)} chars")
    print(f"     new: {len(NEW_BLOCK)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())