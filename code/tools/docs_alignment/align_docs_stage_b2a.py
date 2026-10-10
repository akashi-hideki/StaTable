"""v3.4.3 doc alignment — Stage B-2a: split LAYER_DESIGN §4.1.

Replaces the old §4.1 Driver 层 with:
  - §4.1 DriverInput 层（输入系）  5 states / 9 events / 6 roles
  - §4.2 DriverOutput 层（输出系） 6 states / 11 events / 13 roles

Uses marker-based replacement (no exact old-text match required).
Stage B-2b (renumber old §4.2 ... §4.6 -> §4.3 ... §4.7) runs separately.
"""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "LAYER_DESIGN_zh.md")

START_MARKER = "### 4.1 Driver 层"
END_MARKER = "### 4.2 MwMicrowave 层"

NEW_SECTION = """### 4.1 DriverInput 层（输入系）

#### 4.1.1 职责

DriverInput 层负责**输入系硬件**的读取与事件发行：

- ADC 传感器读取（IR / 蒸汽 / 热敏电阻 × 3 / 湿度）
- 移动平均计算
- AC 零交叉同步 UART 接收（ZC_RX）
- 门开关监控（安全）
- 输入事件发行（IR_READY / STEAM_READY / THERM_READY）

#### 4.1.2 状态（5）

| # | 状态 | 说明 |
|---|---|---|
| 1 | `InIdle` | 待机（等待中断） |
| 2 | `InSensing` | ADC 读取 + 移动平均 |
| 3 | `InTxRx` | 零交叉同步 UART 接收 |
| 4 | `InDoorOpen` | 门开启（安全） |
| 5 | `InError` | 输入错误 |

#### 4.1.3 状态迁移图

```mermaid
stateDiagram-v2
    direction LR
    [*] --> InIdle
    InIdle --> InSensing : SENSOR_TICK
    InSensing --> InIdle : ADC_DONE
    InIdle --> InTxRx : ZC_PULSE
    InTxRx --> InIdle : RX_DONE
    InTxRx --> InError : RX_TIMEOUT
    InIdle --> InDoorOpen : DOOR_OPEN
    InDoorOpen --> InIdle : DOOR_CLOSE
    InIdle --> InError : HW_FAULT
    InSensing --> InError : HW_FAULT
    InTxRx --> InError : HW_FAULT
    InDoorOpen --> InError : HW_FAULT
    InError --> InIdle : CLEAR_FAULT
```

#### 4.1.4 事件（9）

| # | 事件 | delivery | priority | 说明 |
|---|---|---|---|---:|---|
| 1 | `SENSOR_TICK` | queue | 0 | 周期传感器触发 |
| 2 | `ADC_DONE` | direct | 0 | ADC 转换完成 |
| 3 | `ZC_PULSE` | direct | 9 | AC 零交叉脉冲 |
| 4 | `RX_DONE` | direct | 0 | UART 接收完成 |
| 5 | `RX_TIMEOUT` | direct | 5 | UART 接收超时 |
| 6 | `DOOR_OPEN` | direct | 9 | 门开启（安全） |
| 7 | `DOOR_CLOSE` | direct | 9 | 门关闭 |
| 8 | `HW_FAULT` | queue | 9 | 硬件故障 |
| 9 | `CLEAR_FAULT` | direct | 0 | 清除故障 |

#### 4.1.5 主要 Role 函数（6）

| # | 函数 | 用途 |
|---|---|---|
| 1 | `ReadSensorsMovingAvg` | 传感器读取 + 移动平均 |
| 2 | `EmitIrReady` | 发布 IR_READY 事件 |
| 3 | `EmitSteamReady` | 发布 STEAM_READY 事件 |
| 4 | `EmitThermReady` | 发布 THERM_READY 事件 |
| 5 | `ReceiveCommand` | 从面板接收命令 |
| 6 | `OnDoorOpen` | 门开启时立即停止（安全） |

---

### 4.2 DriverOutput 层（输出系）

#### 4.2.1 职责

DriverOutput 层负责**输出系硬件**的控制：

- 加热器 PWM / ON-OFF（上部 / 中部 / 下部）
- 对流风扇 PWM / ON-OFF
- 蒸汽泵 ON-OFF
- 磁控管 PWM / ON-OFF（逆变器控制）
- AC 零交叉同步 UART 发送（ZC_TX）
- 阳极电流监控

#### 4.2.2 状态（6）

| # | 状态 | 说明 |
|---|---|---|
| 1 | `OutIdle` | 全输出 OFF |
| 2 | `OutHeating` | 加热器输出中 |
| 3 | `OutFanPump` | 风扇 / 泵运行中 |
| 4 | `OutMag` | 磁控管运行中 |
| 5 | `OutTx` | UART 发送中 |
| 6 | `OutError` | 输出错误 |

#### 4.2.3 状态迁移图

```mermaid
stateDiagram-v2
    direction LR
    [*] --> OutIdle
    OutIdle --> OutHeating : HEAT_START
    OutHeating --> OutIdle : HEAT_STOP
    OutIdle --> OutFanPump : FAN_PUMP_START
    OutFanPump --> OutIdle : FAN_PUMP_STOP
    OutIdle --> OutMag : MAG_START
    OutMag --> OutIdle : MAG_STOP
    OutIdle --> OutTx : ZC_TX_START
    OutTx --> OutIdle : TX_DONE
    OutTx --> OutError : TX_TIMEOUT
    OutIdle --> OutError : HW_FAULT
    OutHeating --> OutError : HW_FAULT
    OutFanPump --> OutError : HW_FAULT
    OutMag --> OutError : HW_FAULT
    OutTx --> OutError : HW_FAULT
    OutError --> OutIdle : CLEAR_FAULT
```

#### 4.2.4 事件（11）

| # | 事件 | delivery | priority | 说明 |
|---|---|---|---|---:|---|
| 1 | `HEAT_START` | direct | 0 | 开始加热 |
| 2 | `HEAT_STOP` | direct | 0 | 停止加热 |
| 3 | `FAN_PUMP_START` | direct | 0 | 风扇 / 泵启动 |
| 4 | `FAN_PUMP_STOP` | direct | 0 | 风扇 / 泵停止 |
| 5 | `MAG_START` | direct | 0 | 磁控管启动 |
| 6 | `MAG_STOP` | direct | 0 | 磁控管停止 |
| 7 | `ZC_TX_START` | direct | 9 | 零交叉同步发送开始 |
| 8 | `TX_DONE` | direct | 0 | UART 发送完成 |
| 9 | `TX_TIMEOUT` | direct | 5 | UART 发送超时 |
| 10 | `HW_FAULT` | queue | 9 | 硬件故障 |
| 11 | `CLEAR_FAULT` | direct | 0 | 清除故障 |

#### 4.2.5 主要 Role 函数（13）

| # | 函数 | 用途 |
|---|---|---|
| 1 | `SetHeaterOn` | 加热器 ON（全功率） |
| 2 | `SetHeaterOff` | 加热器 OFF |
| 3 | `SetHeaterPwm` | 加热器 PWM duty 设置 |
| 4 | `SetFanOn` | 风扇 ON |
| 5 | `SetFanOff` | 风扇 OFF |
| 6 | `SetFanPwm` | 风扇 PWM duty 设置 |
| 7 | `SetPumpOn` | 泵 ON |
| 8 | `SetPumpOff` | 泵 OFF |
| 9 | `SetMagOn` | 磁控管 ON（全功率） |
| 10 | `SetMagOff` | 磁控管 OFF |
| 11 | `SetMagPwm` | 磁控管 PWM（逆变器电力控制） |
| 12 | `SendStatusMaster` | 向面板发送状态 |
| 13 | `CheckAnodeCurrent` | 磁控管阳极电流监控 |

---

"""


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1
    text = DOC.read_text(encoding="utf-8")

    if "### 4.1 DriverInput 层" in text:
        print("[SKIP] LAYER_DESIGN_zh.md: already has DriverInput section")
        return 0

    start = text.find(START_MARKER)
    end = text.find(END_MARKER)
    if start == -1:
        print(f"[ERR] start marker not found: {START_MARKER!r}")
        return 1
    if end == -1:
        print(f"[ERR] end marker not found: {END_MARKER!r}")
        return 1
    if end <= start:
        print(f"[ERR] markers out of order")
        return 1

    new_text = text[:start] + NEW_SECTION + text[end:]
    DOC.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK] LAYER_DESIGN_zh.md: replaced §4.1 with §4.1 / §4.2")
    print(f"     old: {end - start} chars")
    print(f"     new: {len(NEW_SECTION)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())