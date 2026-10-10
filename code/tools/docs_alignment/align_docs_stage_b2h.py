"""v3.4.3 doc alignment — Stage B-2h: update §4.3 MwMicrowave + §4.6 MwSteam.

Reflects Phase 7 XML changes:
  - MwMicrowave: 3 -> 4 states (+Preheating)
  - MwSteam:     3 -> 5 states (+PumpOn / PumpOff)
"""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "LAYER_DESIGN_zh.md")

# --- MwMicrowave (§4.3) ---
MW_START = "### 4.3 MwMicrowave 层"
MW_END = "### 4.4 MwOven 层"

MW_NEW = """### 4.3 MwMicrowave 层

#### 4.3.1 职责

微波控制的专用层：

- 磁控管软启动 / 预热（Preheating）
- 功率级别设置（PWM 逆变器控制）
- 阳极电流监控（异常检测）

#### 4.3.2 状态（4）

| # | 状态 | 说明 |
|---|---|---|
| 1 | `MwIdle` | 待机 |
| 2 | `Preheating` | 磁控管预热（软启动） |
| 3 | `Heating` | 磁控管加热中 |
| 4 | `MwError` | 微波错误 |

#### 4.3.3 状态迁移图

```mermaid
stateDiagram-v2
    direction LR
    [*] --> MwIdle
    MwIdle --> Preheating : MW_START
    Preheating --> Heating : MW_ANODE_OK
    Preheating --> MwIdle : MW_STOP
    Heating --> MwIdle : MW_STOP
    MwIdle --> MwError : MW_ANODE_FAULT
    Preheating --> MwError : MW_ANODE_FAULT
    Heating --> MwError : MW_ANODE_FAULT
    MwIdle --> MwError : MW_OVERHEAT
    Preheating --> MwError : MW_OVERHEAT
    Heating --> MwError : MW_OVERHEAT
    MwError --> MwIdle : MW_CLEAR
```

#### 4.3.4 事件（6）

| # | 事件 | delivery | priority |
|---|---|---|---:|
| 1 | `MW_START` | direct | 0 |
| 2 | `MW_STOP` | direct | 0 |
| 3 | `MW_ANODE_OK` | direct | 0 |
| 4 | `MW_ANODE_FAULT` | queue | 9 |
| 5 | `MW_OVERHEAT` | queue | 9 |
| 6 | `MW_CLEAR` | direct | 0 |

#### 4.3.5 Role 函数（6）

| # | 函数 | 用途 |
|---|---|---|
| 1 | `StartMagnetron` | 磁控管软启动 |
| 2 | `StopMagnetron` | 磁控管停止 |
| 3 | `SetMwPower` | 功率级别设置 |
| 4 | `CheckAnodeCurrent` | 阳极电流监控 |
| 5 | `LogMwFault` | 微波故障记录 |
| 6 | `ClearMwFault` | 微波故障清除 |

---

"""


# --- MwSteam (§4.6) ---
ST_START = "### 4.6 MwSteam 层"
ST_END = "### 4.7 Application 层"

ST_NEW = """### 4.6 MwSteam 层

#### 4.6.1 职责

蒸汽发生控制：

- 锅炉加热器控制
- 脉冲注水（Pulse pump ON/OFF 交互）
- 锅炉温度 PID

#### 4.6.2 状态（5）

| # | 状态 | 说明 |
|---|---|---|
| 1 | `StIdle` | 待机 |
| 2 | `Steaming` | 蒸汽发生中 |
| 3 | `PumpOn` | 泵脉冲 ON |
| 4 | `PumpOff` | 泵脉冲 OFF |
| 5 | `StError` | 蒸汽错误 |

#### 4.6.3 状态迁移图

```mermaid
stateDiagram-v2
    direction LR
    [*] --> StIdle
    StIdle --> Steaming : ST_START
    Steaming --> StIdle : ST_STOP
    Steaming --> PumpOn : ST_PUMP_TICK
    PumpOn --> PumpOff : ST_PUMP_TICK
    PumpOff --> PumpOn : ST_PUMP_TICK
    PumpOn --> StIdle : ST_STOP
    PumpOff --> StIdle : ST_STOP
    StIdle --> StError : ST_OVERHEAT
    Steaming --> StError : ST_OVERHEAT
    PumpOn --> StError : ST_OVERHEAT
    PumpOff --> StError : ST_OVERHEAT
    StError --> StIdle : ST_CLEAR
```

#### 4.6.4 事件（6）

| # | 事件 | delivery | priority |
|---|---|---|---:|
| 1 | `ST_START` | direct | 0 |
| 2 | `ST_STOP` | direct | 0 |
| 3 | `ST_BOILER_READY` | direct | 0 |
| 4 | `ST_PUMP_TICK` | queue | 0 |
| 5 | `ST_OVERHEAT` | queue | 9 |
| 6 | `ST_CLEAR` | direct | 0 |

#### 4.6.5 Role 函数（9）

| # | 函数 | 用途 |
|---|---|---|
| 1 | `StartBoilerHeater` | 锅炉加热器开始 |
| 2 | `StopBoilerHeater` | 锅炉加热器停止 |
| 3 | `PulsePump` | 脉冲注水 |
| 4 | `SetPumpDuty` | 泵 duty 设置 |
| 5 | `ReadBoilerTemp` | 锅炉温度读取 |
| 6 | `CalculateSteamPID` | 蒸汽 PID 计算 |
| 7 | `CheckSteamOverheat` | 过热检测 |
| 8 | `LogStFault` | 蒸汽故障记录 |
| 9 | `ClearStFault` | 蒸汽故障清除 |

---

"""


def replace_block(text: str, start: str, end: str, new_block: str) -> tuple[str, int]:
    s = text.find(start)
    e = text.find(end)
    if s == -1 or e == -1 or e <= s:
        return text, -1
    old_len = e - s
    return text[:s] + new_block + text[e:], old_len


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")
    total = 0

    # --- MwMicrowave ---
    if "Preheating" in text and "MW_ANODE_OK\" --> Heating" not in text:
        # Look for our marker
        if "| 2 | `Preheating` |" in text:
            print("[SKIP] §4.3 already updated")
        else:
            pass
    if "| 2 | `Preheating` |" not in text:
        text, old_len = replace_block(text, MW_START, MW_END, MW_NEW)
        if old_len < 0:
            print("[ERR] §4.3 boundaries not found")
            return 1
        print(f"[OK]   §4.3 MwMicrowave updated (old {old_len} chars)")
        total += 1
    else:
        print("[SKIP] §4.3 already has Preheating")

    # --- MwSteam ---
    if "| 3 | `PumpOn` |" not in text:
        text, old_len = replace_block(text, ST_START, ST_END, ST_NEW)
        if old_len < 0:
            print("[ERR] §4.6 boundaries not found")
            return 1
        print(f"[OK]   §4.6 MwSteam updated (old {old_len} chars)")
        total += 1
    else:
        print("[SKIP] §4.6 already has PumpOn")

    if total == 0:
        print("[SKIP] nothing to change")
        return 0

    DOC.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK] LAYER_DESIGN_zh.md: {total} section(s) updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())