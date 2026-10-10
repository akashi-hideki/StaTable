"""v3.4.3 doc alignment — Stage B-3b: replace §3 with §3 DriverInput + §4 DriverOutput.

Boundary:
  start: `## 3. Driver 层（13 个）`
  end:   `## 4. MwMicrowave 层（6 个）`

After this, §4 MwMicrowave is duplicated (both DriverOutput and MwMicrowave
are numbered 4). B-3c will renumber §4 -> §5 etc.
"""
from __future__ import annotations
import sys
from pathlib import Path

DOC = (Path(__file__).resolve().parent.parent.parent
       / "code" / "docs" / "samples" / "ROLE_FUNCTIONS_zh.md")

START = "## 3. Driver 层（13 个）"
END = "## 4. MwMicrowave 层（6 个）"

NEW_BLOCK = """## 3. DriverInput 层（6 个）

### 3.1 ReadSensorsMovingAvg

| 项目 | 内容 |
|---|---|
| 用途 | 读取全部传感器并更新移动平均 |
| 调用时机 | `InSensing` 状态的入口 / 周期触发 |
| 关联变量 | `ir_value`, `steam_sensor`, `thermistor_top/middle/bottom`, `humidity` |

**实现例**:

```c
int RoleFunc_DriverInput_ReadSensorsMovingAvg(
    const TransitionContext_DriverInput_t *transition,
    SystemContext_t *ctx)
{
    (void)transition;
    /* [[STABLE_USER_CODE_START:DriverInput_ReadSensorsMovingAvg]] */
    static uint16_t buf_ir[8]  = {0};
    static uint16_t buf_stm[8] = {0};
    static uint8_t  idx = 0;

    uint16_t raw_ir  = ADC_Read(CH_IR);
    uint16_t raw_stm = ADC_Read(CH_STEAM);
    buf_ir[idx]  = raw_ir;
    buf_stm[idx] = raw_stm;
    idx = (idx + 1) & 0x07;

    uint32_t sum_ir = 0, sum_stm = 0;
    for (int i = 0; i < 8; i++) {
        sum_ir  += buf_ir[i];
        sum_stm += buf_stm[i];
    }
    ctx->data.ir_value     = (uint16_t)(sum_ir  / 8);
    ctx->data.steam_sensor = (uint16_t)(sum_stm / 8);

    ctx->data.thermistor_top    = Thermistor_Read(CH_TOP);
    ctx->data.thermistor_middle = Thermistor_Read(CH_MIDDLE);
    ctx->data.thermistor_bottom = Thermistor_Read(CH_BOTTOM);
    /* [[STABLE_USER_CODE_END:DriverInput_ReadSensorsMovingAvg]] */
    return 1;
}
```

### 3.2 EmitIrReady

| 项目 | 内容 |
|---|---|
| 用途 | 红外传感器移动平均完成后发布 IR_READY |
| 调用时机 | `InSensing` 完成时 |
| 关联变量 | `ir_value` |

**实现例**:

```c
int RoleFunc_DriverInput_EmitIrReady(...)
{
    /* [[STABLE_USER_CODE_START:DriverInput_EmitIrReady]] */
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_Middleware_IR_READY);
    /* [[STABLE_USER_CODE_END:DriverInput_EmitIrReady]] */
    return 1;
}
```

### 3.3 EmitSteamReady

| 项目 | 内容 |
|---|---|
| 用途 | 蒸汽传感器更新完成后发布 STEAM_READY |
| 关联变量 | `steam_sensor`, `humidity` |

**实现例**:

```c
int RoleFunc_DriverInput_EmitSteamReady(...)
{
    /* [[STABLE_USER_CODE_START:DriverInput_EmitSteamReady]] */
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_Middleware_STEAM_READY);
    /* [[STABLE_USER_CODE_END:DriverInput_EmitSteamReady]] */
    return 1;
}
```

### 3.4 EmitThermReady

| 项目 | 内容 |
|---|---|
| 用途 | 热敏电阻读取完成后发布 THERM_READY |
| 关联变量 | `thermistor_top/middle/bottom` |

**实现例**:

```c
int RoleFunc_DriverInput_EmitThermReady(...)
{
    /* [[STABLE_USER_CODE_START:DriverInput_EmitThermReady]] */
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_Middleware_THERM_READY);
    /* [[STABLE_USER_CODE_END:DriverInput_EmitThermReady]] */
    return 1;
}
```

### 3.5 ReceiveCommand

| 项目 | 内容 |
|---|---|
| 用途 | 从 Android 面板接收调理序列数据 |
| 调用时机 | `InTxRx` 状态入口 |
| 关联变量 | 序列数据结构 |

**实现例**:

```c
int RoleFunc_DriverInput_ReceiveCommand(...)
{
    /* [[STABLE_USER_CODE_START:DriverInput_ReceiveCommand]] */
    uint8_t frame[32];
    if (ZcSync_UartReceive(frame, sizeof(frame)) > 0) {
        if (Checksum(frame, 31) == frame[31]) {
            ParseSequenceFrame(frame);
            return 1;
        }
    }
    return 0;
    /* [[STABLE_USER_CODE_END:DriverInput_ReceiveCommand]] */
}
```

### 3.6 OnDoorOpen

| 项目 | 内容 |
|---|---|
| 用途 | 门开启时立即停止（安全） |
| 调用时机 | `InDoorOpen` 状态入口 |
| 关联变量 | `door_open` |

**实现例**:

```c
int RoleFunc_DriverInput_OnDoorOpen(...)
{
    /* [[STABLE_USER_CODE_START:DriverInput_OnDoorOpen]] */
    /* 停止全部输出（硬件级二重化） */
    HAL_GPIO_WritePin(HEATER_TOP_PORT, HEATER_TOP_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(HEATER_MIDDLE_PORT, HEATER_MIDDLE_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(HEATER_BOTTOM_PORT, HEATER_BOTTOM_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(MAG_EN_PORT, MAG_EN_PIN, GPIO_PIN_RESET);
    /* [[STABLE_USER_CODE_END:DriverInput_OnDoorOpen]] */
    return 1;
}
```

---

## 4. DriverOutput 层（13 个）

### 4.1 SetHeaterOn

| 项目 | 内容 |
|---|---|
| 用途 | 加热器 ON（全功率） |
| 关联变量 | `heater_top_on`, `heater_middle_on`, `heater_bottom_on` |

**实现例**:

```c
int RoleFunc_DriverOutput_SetHeaterOn(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetHeaterOn]] */
    if (ctx->data.heater_top_on) {
        HAL_GPIO_WritePin(HEATER_TOP_PORT, HEATER_TOP_PIN, GPIO_PIN_SET);
    }
    if (ctx->data.heater_middle_on) {
        HAL_GPIO_WritePin(HEATER_MIDDLE_PORT, HEATER_MIDDLE_PIN, GPIO_PIN_SET);
    }
    if (ctx->data.heater_bottom_on) {
        HAL_GPIO_WritePin(HEATER_BOTTOM_PORT, HEATER_BOTTOM_PIN, GPIO_PIN_SET);
    }
    /* [[STABLE_USER_CODE_END:DriverOutput_SetHeaterOn]] */
    return 1;
}
```

### 4.2 SetHeaterOff

| 项目 | 内容 |
|---|---|
| 用途 | 加热器 OFF |
| 关联变量 | `heater_top_on`, `heater_middle_on`, `heater_bottom_on` |

**实现例**:

```c
int RoleFunc_DriverOutput_SetHeaterOff(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetHeaterOff]] */
    HAL_GPIO_WritePin(HEATER_TOP_PORT, HEATER_TOP_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(HEATER_MIDDLE_PORT, HEATER_MIDDLE_PIN, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(HEATER_BOTTOM_PORT, HEATER_BOTTOM_PIN, GPIO_PIN_RESET);
    /* [[STABLE_USER_CODE_END:DriverOutput_SetHeaterOff]] */
    return 1;
}
```

### 4.3 SetHeaterPwm

| 项目 | 内容 |
|---|---|
| 用途 | 上部 / 中部 / 下部加热器的 PWM 输出 |
| 调用时机 | MwOven / MwGrill 层请求加热时 |
| 关联变量 | `heater_top_duty`, `heater_middle_duty`, `heater_bottom_duty` |

**实现例**:

```c
int RoleFunc_DriverOutput_SetHeaterPwm(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetHeaterPwm]] */
    uint32_t arr = TIM1->ARR;
    TIM1->CCR1 = (ctx->data.heater_top_duty    * arr) / 100;
    TIM1->CCR2 = (ctx->data.heater_middle_duty * arr) / 100;
    TIM1->CCR3 = (ctx->data.heater_bottom_duty * arr) / 100;
    TIM1->CCER |= (TIM_CCER_CC1E | TIM_CCER_CC2E | TIM_CCER_CC3E);
    /* [[STABLE_USER_CODE_END:DriverOutput_SetHeaterPwm]] */
    return 1;
}
```

### 4.4 SetFanOn

| 项目 | 内容 |
|---|---|
| 用途 | 风扇 ON |
| 关联变量 | `fan_on` |

**实现例**:

```c
int RoleFunc_DriverOutput_SetFanOn(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetFanOn]] */
    HAL_GPIO_WritePin(FAN_EN_PORT, FAN_EN_PIN, GPIO_PIN_SET);
    /* [[STABLE_USER_CODE_END:DriverOutput_SetFanOn]] */
    return 1;
}
```

### 4.5 SetFanOff

| 项目 | 内容 |
|---|---|
| 用途 | 风扇 OFF |

**实现例**:

```c
int RoleFunc_DriverOutput_SetFanOff(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetFanOff]] */
    HAL_GPIO_WritePin(FAN_EN_PORT, FAN_EN_PIN, GPIO_PIN_RESET);
    /* [[STABLE_USER_CODE_END:DriverOutput_SetFanOff]] */
    return 1;
}
```

### 4.6 SetFanPwm

| 项目 | 内容 |
|---|---|
| 用途 | 风扇 PWM duty 设置 |
| 关联变量 | `fan_duty` |

**实现例**:

```c
int RoleFunc_DriverOutput_SetFanPwm(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetFanPwm]] */
    TIM2->CCR1 = (ctx->data.fan_duty * TIM2->ARR) / 100;
    if (ctx->data.fan_duty > 0) {
        HAL_GPIO_WritePin(FAN_EN_PORT, FAN_EN_PIN, GPIO_PIN_SET);
    } else {
        HAL_GPIO_WritePin(FAN_EN_PORT, FAN_EN_PIN, GPIO_PIN_RESET);
    }
    /* [[STABLE_USER_CODE_END:DriverOutput_SetFanPwm]] */
    return 1;
}
```

### 4.7 SetPumpOn

| 项目 | 内容 |
|---|---|
| 用途 | 蒸汽泵 ON |
| 关联变量 | `pump_on` |

**实现例**:

```c
int RoleFunc_DriverOutput_SetPumpOn(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetPumpOn]] */
    HAL_GPIO_WritePin(PUMP_PORT, PUMP_PIN, GPIO_PIN_SET);
    /* [[STABLE_USER_CODE_END:DriverOutput_SetPumpOn]] */
    return 1;
}
```

### 4.8 SetPumpOff

| 项目 | 内容 |
|---|---|
| 用途 | 蒸汽泵 OFF |

**实现例**:

```c
int RoleFunc_DriverOutput_SetPumpOff(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetPumpOff]] */
    HAL_GPIO_WritePin(PUMP_PORT, PUMP_PIN, GPIO_PIN_RESET);
    /* [[STABLE_USER_CODE_END:DriverOutput_SetPumpOff]] */
    return 1;
}
```

### 4.9 SetMagOn

| 项目 | 内容 |
|---|---|
| 用途 | 磁控管 ON（全功率） |
| 关联变量 | `mag_on` |

**实现例**:

```c
int RoleFunc_DriverOutput_SetMagOn(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetMagOn]] */
    HAL_GPIO_WritePin(MAG_EN_PORT, MAG_EN_PIN, GPIO_PIN_SET);
    /* [[STABLE_USER_CODE_END:DriverOutput_SetMagOn]] */
    return 1;
}
```

### 4.10 SetMagOff

| 项目 | 内容 |
|---|---|
| 用途 | 磁控管 OFF |

**实现例**:

```c
int RoleFunc_DriverOutput_SetMagOff(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetMagOff]] */
    HAL_GPIO_WritePin(MAG_EN_PORT, MAG_EN_PIN, GPIO_PIN_RESET);
    /* [[STABLE_USER_CODE_END:DriverOutput_SetMagOff]] */
    return 1;
}
```

### 4.11 SetMagPwm

| 项目 | 内容 |
|---|---|
| 用途 | 磁控管 PWM 功率设置（逆变器控制） |
| 关联变量 | `mw_power` |

**实现例**:

```c
int RoleFunc_DriverOutput_SetMagPwm(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SetMagPwm]] */
    uint16_t power = ctx->data.mw_power;
    uint16_t duty  = (power * 100) / 1500;   /* 0-1500W -> 0-100% */
    if (duty > 100) duty = 100;

    TIM4->CCR1 = (duty * TIM4->ARR) / 100;
    TIM4->CCER |= TIM_CCER_CC1E;

    if (duty > 0) {
        HAL_GPIO_WritePin(MAG_EN_PORT, MAG_EN_PIN, GPIO_PIN_SET);
    } else {
        HAL_GPIO_WritePin(MAG_EN_PORT, MAG_EN_PIN, GPIO_PIN_RESET);
    }
    /* [[STABLE_USER_CODE_END:DriverOutput_SetMagPwm]] */
    return 1;
}
```

### 4.12 SendStatusMaster

| 项目 | 内容 |
|---|---|
| 用途 | 主模式：向 Android 面板发送状态（AC 零交叉同步） |
| 调用时机 | `OutTx` 状态入口 |
| 关联变量 | `seq_step`, `seq_total`, `stage_elapsed`, `error_code` |

**实现例**:

```c
int RoleFunc_DriverOutput_SendStatusMaster(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_SendStatusMaster]] */
    uint8_t frame[8];
    frame[0] = 0xA5;                       /* SOF */
    frame[1] = ctx->data.seq_step;
    frame[2] = ctx->data.seq_total;
    frame[3] = (uint8_t)(ctx->data.stage_elapsed >> 8);
    frame[4] = (uint8_t)(ctx->data.stage_elapsed & 0xFF);
    frame[5] = ctx->data.error_code;
    frame[6] = 0x00;                       /* reserved */
    frame[7] = Checksum(frame, 7);

    ZcSync_UartSend(frame, 8);
    /* [[STABLE_USER_CODE_END:DriverOutput_SendStatusMaster]] */
    return 1;
}
```

### 4.13 CheckAnodeCurrent

| 项目 | 内容 |
|---|---|
| 用途 | 磁控管阳极电流监控（异常检测） |
| 关联变量 | `mw_anode_current` |

**实现例**:

```c
int RoleFunc_DriverOutput_CheckAnodeCurrent(...)
{
    /* [[STABLE_USER_CODE_START:DriverOutput_CheckAnodeCurrent]] */
    static uint8_t fault_count = 0;
    uint16_t current = ADC_Read(CH_ANODE);
    ctx->data.mw_anode_current = current;

    if (ctx->data.mw_power == 0 && current > 500) {
        fault_count++;
        if (fault_count >= 3) {
            return 1;
        }
    } else {
        fault_count = 0;
    }
    return 0;
    /* [[STABLE_USER_CODE_END:DriverOutput_CheckAnodeCurrent]] */
}
```

---

"""


def main() -> int:
    if not DOC.exists():
        print(f"[ERR] {DOC} not found")
        return 1

    text = DOC.read_text(encoding="utf-8")

    if "## 3. DriverInput 层（6 个）" in text:
        print("[SKIP] already updated")
        return 0

    s = text.find(START)
    e = text.find(END)
    if s == -1 or e == -1 or e <= s:
        print(f"[ERR] markers not found (s={s}, e={e})")
        return 1

    old_block = text[s:e]
    new_text = text[:s] + NEW_BLOCK + text[e:]
    DOC.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK] ROLE_FUNCTIONS_zh.md: §3 replaced with §3 + §4")
    print(f"     old: {len(old_block)} chars")
    print(f"     new: {len(NEW_BLOCK)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())