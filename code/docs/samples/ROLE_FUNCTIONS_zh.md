# StaTable Role 函数参考手册 — 复合烹饪器具

Version: 1.0
Date: 2026-10-04
适用：Galanz 等复合烹饪器具（微波炉 / 烤箱 / 蒸箱 / 组合机）
关联：`cooking_heater_controller.xml`, `LAYER_DESIGN_zh.md`

---

## 目录

1. 前言
2. 通用规范
3. Driver 层（13 个）
4. MwMicrowave 层（6 个）
5. MwOven 层（10 个）
6. MwGrill 层（6 个）
7. MwSteam 层（9 个）
8. Application 层（10 个）
9. 通用实现模式
10. 变更历史

---

## 1. 前言

### 1.1 本文目的

本文档详细说明 StaTable 生成的 54 个 **Role 函数** 的：

- 签名（参数 / 返回值）
- 用途与调用时机
- 关联全局变量
- 用户实现示例（C 代码）

### 1.2 Role 函数是什么

Role 函数 = 状态机中可以调用的**用户实现函数**。

| 用途 | 说明 |
|---|---|
| 迁移条件 | 返回值用于判定（`!= 0` = true） |
| Pre 动作 | 迁移评估前执行 |
| Post 动作 | 迁移评估后执行 |
| Entry 动作 | 状态进入时执行 |
| Exit 动作 | 状态退出时执行 |
| Do 动作 | 状态持续期间执行 |

### 1.3 标准签名

所有 Role 函数遵循统一签名：

```c
int RoleFunc_<Layer>_<Name>(
    const TransitionContext_<Layer>_t *transition,
    SystemContext_t *ctx
);
```

| 参数 | 用途 |
|---|---|
| `transition` | 迁移上下文（`from_state`, `event`） |
| `ctx` | 系统上下文（全局数据） |

**返回值**: `int`
- `0` = false / 失败
- `非 0` = true / 成功

### 1.4 用户代码标记

每个 Role 函数体内有用户代码区域：

```c
int RoleFunc_Driver_SetHeaterPwm(...) {
    (void)transition; (void)ctx;   /* 或局部指针 */
    /* [[STABLE_USER_CODE_START:Driver_SetHeaterPwm]] */
    /* 用户在此实现 */
    /* [[STABLE_USER_CODE_END:Driver_SetHeaterPwm]] */
    return 0;
}
```

**标记之间**的代码在重新生成时保留。

---

## 2. 通用规范

### 2.1 命名规范

| 要素 | 规范 | 示例 |
|---|---|---|
| 层名 | PascalCase | `Driver`, `MwMicrowave` |
| 函数名 | PascalCase | `SetHeaterPwm` |
| 完全名 | `<Layer>.<Name>` | `Driver.SetHeaterPwm` |
| C 函数名 | `RoleFunc_<Layer>_<Name>` | `RoleFunc_Driver_SetHeaterPwm` |

### 2.2 数据类型

| 用途 | 类型 | 范围 |
|---|---|---|
| 温度 | `uint16_t` | 0〜1000 (°C) |
| 功率 | `uint16_t` | 0〜1500 (W) |
| Duty | `uint8_t` | 0〜100 (%) |
| 时间 | `uint32_t` | 0〜4294967295 (ms) |
| 传感器 | `uint16_t` | 0〜4095 (12bit ADC) |
| 错误码 | `uint8_t` | 0〜255 |
| 步骤 | `uint8_t` | 0〜255 |

### 2.3 返回值约定

| 用途 | 返回 0 | 返回非 0 |
|---|---|---|
| 条件判定 | false | true |
| 动作执行 | 失败 | 成功 |
| 状态查询 | 无 / 正常 | 有 / 异常 |

### 2.4 全局变量访问

通过 `ctx->data.<name>` 访问全局变量：

```c
uint16_t t = ctx->data.thermistor_top;
ctx->data.heater_top_duty = 50;
```

---

## 3. Driver 层（13 个）

### 3.1 ReadSensorsMovingAvg

| 项目 | 内容 |
|---|---|
| 用途 | 读取全部传感器并更新移动平均 |
| 调用时机 | `HwSensing` 状态的入口 / 周期触发 |
| 关联变量 | `ir_value`, `steam_sensor`, `thermistor_top/bottom/back`, `humidity` |

**实现例**:

```c
int RoleFunc_Driver_ReadSensorsMovingAvg(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx)
{
    (void)transition;
    /* [[STABLE_USER_CODE_START:Driver_ReadSensorsMovingAvg]] */
    static uint16_t buf_ir[8]   = {0};
    static uint16_t buf_stm[8]  = {0};
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
    ctx->data.thermistor_bottom = Thermistor_Read(CH_BOTTOM);
    ctx->data.thermistor_back   = Thermistor_Read(CH_BACK);
    /* [[STABLE_USER_CODE_END:Driver_ReadSensorsMovingAvg]] */
    return 1;
}
```

### 3.2 EmitIrReady

| 项目 | 内容 |
|---|---|
| 用途 | 红外传感器移动平均完成后发布 IR_READY 事件 |
| 调用时机 | `HwSensing` 完成时 |
| 关联变量 | `ir_value` |

**实现例**:

```c
int RoleFunc_Driver_EmitIrReady(...)
{
    /* [[STABLE_USER_CODE_START:Driver_EmitIrReady]] */
    /* 通过事件队列通知中间层 */
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_Middleware_IR_READY);
    /* [[STABLE_USER_CODE_END:Driver_EmitIrReady]] */
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
int RoleFunc_Driver_EmitSteamReady(...)
{
    /* [[STABLE_USER_CODE_START:Driver_EmitSteamReady]] */
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_Middleware_STEAM_READY);
    /* [[STABLE_USER_CODE_END:Driver_EmitSteamReady]] */
    return 1;
}
```

### 3.4 EmitThermReady

| 项目 | 内容 |
|---|---|
| 用途 | 热敏电阻读取完成后发布 THERM_READY |
| 关联变量 | `thermistor_top/bottom/back` |

**实现例**:

```c
int RoleFunc_Driver_EmitThermReady(...)
{
    /* [[STABLE_USER_CODE_START:Driver_EmitThermReady]] */
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_Middleware_THERM_READY);
    /* [[STABLE_USER_CODE_END:Driver_EmitThermReady]] */
    return 1;
}
```

### 3.5 SendStatusMaster

| 项目 | 内容 |
|---|---|
| 用途 | 主模式：向 Android 面板发送状态（AC 零交叉同步） |
| 调用时机 | `HwTxStatus` 状态入口 |
| 关联变量 | `seq_step`, `seq_total`, `stage_elapsed`, `error_code` |

**实现例**:

```c
int RoleFunc_Driver_SendStatusMaster(...)
{
    /* [[STABLE_USER_CODE_START:Driver_SendStatusMaster]] */
    uint8_t frame[8];
    frame[0] = 0xA5;                       /* SOF */
    frame[1] = ctx->data.seq_step;
    frame[2] = ctx->data.seq_total;
    frame[3] = (uint8_t)(ctx->data.stage_elapsed >> 8);
    frame[4] = (uint8_t)(ctx->data.stage_elapsed & 0xFF);
    frame[5] = ctx->data.error_code;
    frame[6] = 0x00;                       /* reserved */
    frame[7] = Checksum(frame, 7);

    ZcSync_UartSend(frame, 8);             /* 零交叉同步发送 */
    /* [[STABLE_USER_CODE_END:Driver_SendStatusMaster]] */
    return 1;
}
```

### 3.6 ReceiveCommand

| 项目 | 内容 |
|---|---|
| 用途 | 从 Android 面板接收调理序列数据 |
| 调用时机 | `HwRxCommand` 状态入口 |
| 关联变量 | 序列数据结构 |

**实现例**:

```c
int RoleFunc_Driver_ReceiveCommand(...)
{
    /* [[STABLE_USER_CODE_START:Driver_ReceiveCommand]] */
    uint8_t frame[32];
    if (ZcSync_UartReceive(frame, sizeof(frame)) > 0) {
        if (Checksum(frame, 31) == frame[31]) {
            /* 解析并存入共享变量 */
            ParseSequenceFrame(frame);
            return 1;
        }
    }
    return 0;
    /* [[STABLE_USER_CODE_END:Driver_ReceiveCommand]] */
}
```

---
### 3.7 SetHeaterPwm

| 项目 | 内容 |
|---|---|
| 用途 | 上部 / 下部 / 背部加热器的 PWM 输出 |
| 调用时机 | MwOven / MwGrill 层请求加热时 |
| 关联变量 | `heater_top_duty`, `heater_bottom_duty`, `heater_back_duty` |

**实现例**:

```c
int RoleFunc_Driver_SetHeaterPwm(...)
{
    /* [[STABLE_USER_CODE_START:Driver_SetHeaterPwm]] */
    /* 使用 STM32 TIM1 输出 3 通道 PWM */
    uint32_t arr = TIM1->ARR;
    TIM1->CCR1 = (ctx->data.heater_top_duty    * arr) / 100;
    TIM1->CCR2 = (ctx->data.heater_bottom_duty * arr) / 100;
    TIM1->CCR3 = (ctx->data.heater_back_duty   * arr) / 100;
    /* [[STABLE_USER_CODE_END:Driver_SetHeaterPwm]] */
    return 1;
}
```

### 3.8 SetConvectionFan

| 项目 | 内容 |
|---|---|
| 用途 | 热风风扇 duty 设置 |
| 关联变量 | `fan_duty` |

**实现例**:

```c
int RoleFunc_Driver_SetConvectionFan(...)
{
    /* [[STABLE_USER_CODE_START:Driver_SetConvectionFan]] */
    TIM2->CCR1 = (ctx->data.fan_duty * TIM2->ARR) / 100;
    if (ctx->data.fan_duty > 0) {
        HAL_GPIO_WritePin(FAN_EN_PORT, FAN_EN_PIN, GPIO_PIN_SET);
    } else {
        HAL_GPIO_WritePin(FAN_EN_PORT, FAN_EN_PIN, GPIO_PIN_RESET);
    }
    /* [[STABLE_USER_CODE_END:Driver_SetConvectionFan]] */
    return 1;
}
```

### 3.9 SetMagnetronPower

| 项目 | 内容 |
|---|---|
| 用途 | 磁控管功率级别设置 |
| 关联变量 | `mw_power` |

**实现例**:

```c
int RoleFunc_Driver_SetMagnetronPower(...)
{
    /* [[STABLE_USER_CODE_START:Driver_SetMagnetronPower]] */
    /* 通过逆变器 PWM 占空比控制微波功率 */
    uint16_t power = ctx->data.mw_power;
    uint16_t duty  = (power * 100) / 1500;   /* 0-1500W → 0-100% */
    INV_SetDuty(duty);
    /* [[STABLE_USER_CODE_END:Driver_SetMagnetronPower]] */
    return 1;
}
```

### 3.10 PulseBoilerPump

| 项目 | 内容 |
|---|---|
| 用途 | 锅炉脉冲注水（避免过水） |
| 关联变量 | `pump_pulse_count` |

**实现例**:

```c
int RoleFunc_Driver_PulseBoilerPump(...)
{
    /* [[STABLE_USER_CODE_START:Driver_PulseBoilerPump]] */
    uint8_t pulses = ctx->data.pump_pulse_count;
    for (uint8_t i = 0; i < pulses; i++) {
        HAL_GPIO_WritePin(PUMP_PORT, PUMP_PIN, GPIO_PIN_SET);
        HAL_Delay(50);      /* 50ms 通水 */
        HAL_GPIO_WritePin(PUMP_PORT, PUMP_PIN, GPIO_PIN_RESET);
        HAL_Delay(150);     /* 150ms 待机 */
    }
    /* [[STABLE_USER_CODE_END:Driver_PulseBoilerPump]] */
    return 1;
}
```

### 3.11 CheckAnodeCurrent

| 项目 | 内容 |
|---|---|
| 用途 | 磁控管阳极电流监控（异常检测） |
| 关联变量 | `mw_anode_current` |

**实现例**:

```c
int RoleFunc_Driver_CheckAnodeCurrent(...)
{
    /* [[STABLE_USER_CODE_START:Driver_CheckAnodeCurrent]] */
    static uint8_t fault_count = 0;
    uint16_t current = ADC_Read(CH_ANODE);
    ctx->data.mw_anode_current = current;

    /* 无功率时电流异常高 → 故障 */
    if (ctx->data.mw_power == 0 && current > 500) {
        fault_count++;
        if (fault_count >= 3) {
            return 1;   /* 故障持续 3 次 */
        }
    } else {
        fault_count = 0;
    }
    return 0;
    /* [[STABLE_USER_CODE_END:Driver_CheckAnodeCurrent]] */
}
```

### 3.12 LogHwFault

| 项目 | 内容 |
|---|---|
| 用途 | 硬件故障记录 |
| 关联变量 | `error_code` |

**实现例**:

```c
int RoleFunc_Driver_LogHwFault(...)
{
    /* [[STABLE_USER_CODE_START:Driver_LogHwFault]] */
    Log_Write(LOG_LEVEL_ERROR, "HW fault: %d",
              ctx->data.error_code);
    /* 可扩展为闪存记录 / 云端上传 */
    /* [[STABLE_USER_CODE_END:Driver_LogHwFault]] */
    return 1;
}
```

### 3.13 ClearHwFault

| 项目 | 内容 |
|---|---|
| 用途 | 硬件故障清除 |
| 关联变量 | `error_code` |

**实现例**:

```c
int RoleFunc_Driver_ClearHwFault(...)
{
    /* [[STABLE_USER_CODE_START:Driver_ClearHwFault]] */
    ctx->data.error_code = 0;
    /* 复位相关外设 */
    INV_Reset();
    /* [[STABLE_USER_CODE_END:Driver_ClearHwFault]] */
    return 1;
}
```

---

## 4. MwMicrowave 层（6 个）

### 4.1 StartMagnetron

| 项目 | 内容 |
|---|---|
| 用途 | 磁控管软启动（避免浪涌电流） |
| 调用时机 | `Heating` 状态入口 |
| 关联变量 | `mw_power` |

**实现例**:

```c
int RoleFunc_MwMicrowave_StartMagnetron(...)
{
    /* [[STABLE_USER_CODE_START:MwMicrowave_StartMagnetron]] */
    /* 阶段 1: 预热（低功率） */
    INV_SetDuty(20);
    HAL_Delay(500);
    /* 阶段 2: 正常功率 */
    RoleFunc_Driver_SetMagnetronPower(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwMicrowave_StartMagnetron]] */
    return 1;
}
```

### 4.2 StopMagnetron

| 项目 | 内容 |
|---|---|
| 用途 | 磁控管停止 |
| 调用时机 | `Heating` → `MwIdle` 迁移前 |

**实现例**:

```c
int RoleFunc_MwMicrowave_StopMagnetron(...)
{
    /* [[STABLE_USER_CODE_START:MwMicrowave_StopMagnetron]] */
    INV_SetDuty(0);
    HAL_GPIO_WritePin(MAG_EN_PORT, MAG_EN_PIN, GPIO_PIN_RESET);
    /* [[STABLE_USER_CODE_END:MwMicrowave_StopMagnetron]] */
    return 1;
}
```

### 4.3 SetMwPower

| 项目 | 内容 |
|---|---|
| 用途 | 功率级别设置（由 Application 层指定） |
| 关联变量 | `mw_power` |

**实现例**:

```c
int RoleFunc_MwMicrowave_SetMwPower(...)
{
    /* [[STABLE_USER_CODE_START:MwMicrowave_SetMwPower]] */
    /* 校验功率范围 */
    if (ctx->data.mw_power > 1500) {
        ctx->data.mw_power = 1500;   /* 上限限幅 */
    }
    /* 转调 Driver 层 */
    RoleFunc_Driver_SetMagnetronPower(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwMicrowave_SetMwPower]] */
    return 1;
}
```

### 4.4 CheckAnodeCurrent

| 项目 | 内容 |
|---|---|
| 用途 | 异常检测（连续 3 次或持续 8 秒判定故障） |

**实现例**:

```c
int RoleFunc_MwMicrowave_CheckAnodeCurrent(...)
{
    /* [[STABLE_USER_CODE_START:MwMicrowave_CheckAnodeCurrent]] */
    return RoleFunc_Driver_CheckAnodeCurrent(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwMicrowave_CheckAnodeCurrent]] */
}
```

### 4.5 LogMwFault

| 项目 | 内容 |
|---|---|
| 用途 | 微波故障记录 |

**实现例**:

```c
int RoleFunc_MwMicrowave_LogMwFault(...)
{
    /* [[STABLE_USER_CODE_START:MwMicrowave_LogMwFault]] */
    Log_Write(LOG_LEVEL_ERROR, "MW fault, err=%d",
              ctx->data.error_code);
    /* [[STABLE_USER_CODE_END:MwMicrowave_LogMwFault]] */
    return 1;
}
```

### 4.6 ClearMwFault

| 项目 | 内容 |
|---|---|
| 用途 | 微波故障清除 |

**实现例**:

```c
int RoleFunc_MwMicrowave_ClearMwFault(...)
{
    /* [[STABLE_USER_CODE_START:MwMicrowave_ClearMwFault]] */
    ctx->data.error_code = 0;
    /* [[STABLE_USER_CODE_END:MwMicrowave_ClearMwFault]] */
    return 1;
}
```

---

## 5. MwOven 层（10 个）

### 5.1 StartOvenPid

| 项目 | 内容 |
|---|---|
| 用途 | PID 温控开始 |
| 调用时机 | `PidHeating` 状态入口 |
| 关联变量 | `oven_target_temp` |

**实现例**:

```c
int RoleFunc_MwOven_StartOvenPid(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_StartOvenPid]] */
    Pid_Init(&g_oven_pid,
             Kp, Ki, Kd,
             0, 100);              /* 输出范围 0-100% */
    Pid_SetTarget(&g_oven_pid, ctx->data.oven_target_temp);
    /* [[STABLE_USER_CODE_END:MwOven_StartOvenPid]] */
    return 1;
}
```

### 5.2 StopOvenPid

| 项目 | 内容 |
|---|---|
| 用途 | PID 温控停止 |

**实现例**:

```c
int RoleFunc_MwOven_StopOvenPid(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_StopOvenPid]] */
    ctx->data.heater_top_duty    = 0;
    ctx->data.heater_bottom_duty = 0;
    ctx->data.heater_back_duty   = 0;
    RoleFunc_Driver_SetHeaterPwm(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwOven_StopOvenPid]] */
    return 1;
}
```

### 5.3 SetTopHeaterDuty

| 项目 | 内容 |
|---|---|
| 用途 | 上部加热器 duty 设置 |
| 关联变量 | `heater_top_duty` |

**实现例**:

```c
int RoleFunc_MwOven_SetTopHeaterDuty(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_SetTopHeaterDuty]] */
    RoleFunc_Driver_SetHeaterPwm(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwOven_SetTopHeaterDuty]] */
    return 1;
}
```

### 5.4 SetBottomHeaterDuty

| 项目 | 内容 |
|---|---|
| 用途 | 下部加热器 duty 设置 |
| 关联变量 | `heater_bottom_duty` |

**实现例**:

```c
int RoleFunc_MwOven_SetBottomHeaterDuty(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_SetBottomHeaterDuty]] */
    RoleFunc_Driver_SetHeaterPwm(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwOven_SetBottomHeaterDuty]] */
    return 1;
}
```

### 5.5 SetBackHeaterDuty

| 项目 | 内容 |
|---|---|
| 用途 | 背部加热器 duty 设置 |
| 关联变量 | `heater_back_duty` |

**实现例**:

```c
int RoleFunc_MwOven_SetBackHeaterDuty(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_SetBackHeaterDuty]] */
    RoleFunc_Driver_SetHeaterPwm(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwOven_SetBackHeaterDuty]] */
    return 1;
}
```

### 5.6 SetConvectionFan

| 项目 | 内容 |
|---|---|
| 用途 | 热风风扇 duty 设置 |
| 关联变量 | `fan_duty` |

**实现例**:

```c
int RoleFunc_MwOven_SetConvectionFan(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_SetConvectionFan]] */
    RoleFunc_Driver_SetConvectionFan(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwOven_SetConvectionFan]] */
    return 1;
}
```

### 5.7 ReadThermistors

| 项目 | 内容 |
|---|---|
| 用途 | 全热敏电阻读取 |
| 关联变量 | `thermistor_top/bottom/back` |

**实现例**:

```c
int RoleFunc_MwOven_ReadThermistors(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_ReadThermistors]] */
    /* 直接读取 Driver 层已更新的值 */
    uint16_t t_top = ctx->data.thermistor_top;
    uint16_t t_btm = ctx->data.thermistor_bottom;
    uint16_t t_bak = ctx->data.thermistor_back;
    /* 可计算平均温度用于 PID 反馈 */
    ctx->data.oven_current_temp =
        (uint16_t)((t_top + t_btm + t_bak) / 3);
    /* [[STABLE_USER_CODE_END:MwOven_ReadThermistors]] */
    return 1;
}
```

### 5.8 CheckOvenOverheat

| 项目 | 内容 |
|---|---|
| 用途 | 过热检测 |

**实现例**:

```c
int RoleFunc_MwOven_CheckOvenOverheat(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_CheckOvenOverheat]] */
    if (ctx->data.oven_current_temp > OVEN_TEMP_LIMIT) {
        return 1;   /* 过热 */
    }
    return 0;
    /* [[STABLE_USER_CODE_END:MwOven_CheckOvenOverheat]] */
}
```

### 5.9 LogOvFault

| 项目 | 内容 |
|---|---|
| 用途 | 烤箱故障记录 |

**实现例**:

```c
int RoleFunc_MwOven_LogOvFault(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_LogOvFault]] */
    Log_Write(LOG_LEVEL_ERROR, "Oven fault, err=%d",
              ctx->data.error_code);
    /* [[STABLE_USER_CODE_END:MwOven_LogOvFault]] */
    return 1;
}
```

### 5.10 ClearOvFault

| 项目 | 内容 |
|---|---|
| 用途 | 烤箱故障清除 |

**实现例**:

```c
int RoleFunc_MwOven_ClearOvFault(...)
{
    /* [[STABLE_USER_CODE_START:MwOven_ClearOvFault]] */
    ctx->data.error_code = 0;
    RoleFunc_MwOven_StopOvenPid(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwOven_ClearOvFault]] */
    return 1;
}
```

---
## 6. MwGrill 层（6 个）

### 6.1 StartGrill

| 项目 | 内容 |
|---|---|
| 用途 | 烧烤加热开始（上部加热器专用） |
| 调用时机 | `Grilling` 状态入口 |
| 关联变量 | `heater_top_duty` |

**实现例**:

```c
int RoleFunc_MwGrill_StartGrill(...)
{
    /* [[STABLE_USER_CODE_START:MwGrill_StartGrill]] */
    RoleFunc_Driver_SetHeaterPwm(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwGrill_StartGrill]] */
    return 1;
}
```

### 6.2 StopGrill

| 项目 | 内容 |
|---|---|
| 用途 | 烧烤停止 |
| 关联变量 | `heater_top_duty` |

**实现例**:

```c
int RoleFunc_MwGrill_StopGrill(...)
{
    /* [[STABLE_USER_CODE_START:MwGrill_StopGrill]] */
    ctx->data.heater_top_duty = 0;
    RoleFunc_Driver_SetHeaterPwm(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwGrill_StopGrill]] */
    return 1;
}
```

### 6.3 SetGrillDuty

| 项目 | 内容 |
|---|---|
| 用途 | 烧烤 duty 设置 |
| 关联变量 | `heater_top_duty` |

**实现例**:

```c
int RoleFunc_MwGrill_SetGrillDuty(...)
{
    /* [[STABLE_USER_CODE_START:MwGrill_SetGrillDuty]] */
    if (ctx->data.heater_top_duty > 100) {
        ctx->data.heater_top_duty = 100;
    }
    RoleFunc_Driver_SetHeaterPwm(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwGrill_SetGrillDuty]] */
    return 1;
}
```

### 6.4 CheckGrillOverheat

| 项目 | 内容 |
|---|---|
| 用途 | 烧烤过热检测 |

**实现例**:

```c
int RoleFunc_MwGrill_CheckGrillOverheat(...)
{
    /* [[STABLE_USER_CODE_START:MwGrill_CheckGrillOverheat]] */
    if (ctx->data.thermistor_top > GRILL_TEMP_LIMIT) {
        return 1;
    }
    return 0;
    /* [[STABLE_USER_CODE_END:MwGrill_CheckGrillOverheat]] */
}
```

### 6.5 LogGrFault

| 项目 | 内容 |
|---|---|
| 用途 | 烧烤故障记录 |

**实现例**:

```c
int RoleFunc_MwGrill_LogGrFault(...)
{
    /* [[STABLE_USER_CODE_START:MwGrill_LogGrFault]] */
    Log_Write(LOG_LEVEL_ERROR, "Grill fault, err=%d",
              ctx->data.error_code);
    /* [[STABLE_USER_CODE_END:MwGrill_LogGrFault]] */
    return 1;
}
```

### 6.6 ClearGrFault

| 项目 | 内容 |
|---|---|
| 用途 | 烧烤故障清除 |

**实现例**:

```c
int RoleFunc_MwGrill_ClearGrFault(...)
{
    /* [[STABLE_USER_CODE_START:MwGrill_ClearGrFault]] */
    ctx->data.error_code = 0;
    RoleFunc_MwGrill_StopGrill(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwGrill_ClearGrFault]] */
    return 1;
}
```

---

## 7. MwSteam 层（9 个）

### 7.1 StartBoilerHeater

| 项目 | 内容 |
|---|---|
| 用途 | 锅炉加热器开始（温度目标 140°C） |
| 调用时机 | `Steaming` 状态入口 |
| 关联变量 | `steam_target_temp`, `boiler_temp` |

**实现例**:

```c
int RoleFunc_MwSteam_StartBoilerHeater(...)
{
    /* [[STABLE_USER_CODE_START:MwSteam_StartBoilerHeater]] */
    if (ctx->data.steam_target_temp == 0) {
        ctx->data.steam_target_temp = 140;   /* 默认值 */
    }
    Pid_Init(&g_boiler_pid, Kp, Ki, Kd, 0, 100);
    Pid_SetTarget(&g_boiler_pid, ctx->data.steam_target_temp);
    HAL_GPIO_WritePin(BOILER_HEAT_PORT, BOILER_HEAT_PIN,
                      GPIO_PIN_SET);
    /* [[STABLE_USER_CODE_END:MwSteam_StartBoilerHeater]] */
    return 1;
}
```

### 7.2 StopBoilerHeater

| 项目 | 内容 |
|---|---|
| 用途 | 锅炉加热器停止 |

**实现例**:

```c
int RoleFunc_MwSteam_StopBoilerHeater(...)
{
    /* [[STABLE_USER_CODE_START:MwSteam_StopBoilerHeater]] */
    HAL_GPIO_WritePin(BOILER_HEAT_PORT, BOILER_HEAT_PIN,
                      GPIO_PIN_RESET);
    /* [[STABLE_USER_CODE_END:MwSteam_StopBoilerHeater]] */
    return 1;
}
```

### 7.3 PulsePump

| 项目 | 内容 |
|---|---|
| 用途 | 脉冲注水（防止过水） |
| 调用时机 | `Steaming` 状态下 `ST_PUMP_TICK` |
| 关联变量 | `pump_pulse_count` |

**实现例**:

```c
int RoleFunc_MwSteam_PulsePump(...)
{
    /* [[STABLE_USER_CODE_START:MwSteam_PulsePump]] */
    /* PID 计算注水量 */
    uint8_t pulses = (uint8_t)Pid_Update(
        &g_boiler_pid, ctx->data.boiler_temp);
    ctx->data.pump_pulse_count = pulses;
    RoleFunc_Driver_PulseBoilerPump(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwSteam_PulsePump]] */
    return 1;
}
```

### 7.4 SetPumpDuty

| 项目 | 内容 |
|---|---|
| 用途 | 泵 duty 设置（脉冲宽度） |

**实现例**:

```c
int RoleFunc_MwSteam_SetPumpDuty(...)
{
    /* [[STABLE_USER_CODE_START:MwSteam_SetPumpDuty]] */
    /* 直接控制泵的 PWM */
    TIM3->CCR1 = (ctx->data.pump_pulse_count * TIM3->ARR) / 255;
    /* [[STABLE_USER_CODE_END:MwSteam_SetPumpDuty]] */
    return 1;
}
```

### 7.5 ReadBoilerTemp

| 项目 | 内容 |
|---|---|
| 用途 | 锅炉温度读取 |
| 关联变量 | `boiler_temp` |

**实现例**:

```c
int RoleFunc_MwSteam_ReadBoilerTemp(...)
{
    /* [[STABLE_USER_CODE_START:MwSteam_ReadBoilerTemp]] */
    ctx->data.boiler_temp = Thermistor_Read(CH_BOILER);
    /* [[STABLE_USER_CODE_END:MwSteam_ReadBoilerTemp]] */
    return 1;
}
```

### 7.6 CalculateSteamPID

| 项目 | 内容 |
|---|---|
| 用途 | 蒸汽 PID 计算 |
| 关联变量 | `boiler_temp`, `steam_target_temp` |

**实现例**:

```c
int RoleFunc_MwSteam_CalculateSteamPID(...)
{
    /* [[STABLE_USER_CODE_START:MwSteam_CalculateSteamPID]] */
    float output = Pid_Update(&g_boiler_pid,
                              ctx->data.boiler_temp);
    /* 将输出映射到泵脉冲数 */
    ctx->data.pump_pulse_count = (uint8_t)(output * 3.0f);
    /* [[STABLE_USER_CODE_END:MwSteam_CalculateSteamPID]] */
    return 1;
}
```

### 7.7 CheckSteamOverheat

| 项目 | 内容 |
|---|---|
| 用途 | 蒸汽过热检测 |

**实现例**:

```c
int RoleFunc_MwSteam_CheckSteamOverheat(...)
{
    /* [[STABLE_USER_CODE_START:MwSteam_CheckSteamOverheat]] */
    if (ctx->data.boiler_temp > BOILER_TEMP_LIMIT) {
        return 1;
    }
    return 0;
    /* [[STABLE_USER_CODE_END:MwSteam_CheckSteamOverheat]] */
}
```

### 7.8 LogStFault

| 项目 | 内容 |
|---|---|
| 用途 | 蒸汽故障记录 |

**实现例**:

```c
int RoleFunc_MwSteam_LogStFault(...)
{
    /* [[STABLE_USER_CODE_START:MwSteam_LogStFault]] */
    Log_Write(LOG_LEVEL_ERROR, "Steam fault, err=%d",
              ctx->data.error_code);
    /* [[STABLE_USER_CODE_END:MwSteam_LogStFault]] */
    return 1;
}
```

### 7.9 ClearStFault

| 项目 | 内容 |
|---|---|
| 用途 | 蒸汽故障清除 |

**实现例**:

```c
int RoleFunc_MwSteam_ClearStFault(...)
{
    /* [[STABLE_USER_CODE_START:MwSteam_ClearStFault]] */
    ctx->data.error_code = 0;
    RoleFunc_MwSteam_StopBoilerHeater(NULL, ctx);
    /* [[STABLE_USER_CODE_END:MwSteam_ClearStFault]] */
    return 1;
}
```

---

## 8. Application 层（10 个）

### 8.1 ReceiveSequence

| 项目 | 内容 |
|---|---|
| 用途 | 从 Android 面板接收调理序列 |
| 调用时机 | `Idle` 状态下 `SEQ_RECEIVED` 后 |
| 关联变量 | `seq_total`, `seq_step` |

**实现例**:

```c
int RoleFunc_Application_ReceiveSequence(...)
{
    /* [[STABLE_USER_CODE_START:Application_ReceiveSequence]] */
    /* 序列数据已由 Driver 层接收并暂存 */
    ctx->data.seq_total = g_rx_seq.total_steps;
    ctx->data.seq_step = 0;
    ctx->data.stage_elapsed = 0;
    /* [[STABLE_USER_CODE_END:Application_ReceiveSequence]] */
    return 1;
}
```

### 8.2 ParseSequence

| 项目 | 内容 |
|---|---|
| 用途 | 序列解析（划分阶段） |

**实现例**:

```c
int RoleFunc_Application_ParseSequence(...)
{
    /* [[STABLE_USER_CODE_START:Application_ParseSequence]] */
    /* 序列已由 Driver 解析为 g_rx_seq 结构 */
    if (g_rx_seq.total_steps == 0) {
        return 0;
    }
    /* 设置当前阶段的模式、温度、时间 */
    ctx->data.stage_mode = g_rx_seq.steps[0].mode;
    ctx->data.oven_target_temp = g_rx_seq.steps[0].temperature;
    ctx->data.stage_duration = g_rx_seq.steps[0].duration_ms;
    /* [[STABLE_USER_CODE_END:Application_ParseSequence]] */
    return 1;
}
```

### 8.3 StartStage

| 项目 | 内容 |
|---|---|
| 用途 | 当前阶段开始（激活相应的中间层） |
| 关联变量 | `stage_mode` |

**实现例**:

```c
int RoleFunc_Application_StartStage(...)
{
    /* [[STABLE_USER_CODE_START:Application_StartStage]] */
    ctx->data.stage_elapsed = 0;

    switch (ctx->data.stage_mode) {
    case MODE_MICROWAVE:
        StateMachine_EnqueueEvent(&g_ctx,
            EVENT_MwMicrowave_MW_START);
        break;
    case MODE_OVEN:
        StateMachine_EnqueueEvent(&g_ctx,
            EVENT_MwOven_OV_START);
        break;
    case MODE_GRILL:
        StateMachine_EnqueueEvent(&g_ctx,
            EVENT_MwGrill_GR_START);
        break;
    case MODE_STEAM:
        StateMachine_EnqueueEvent(&g_ctx,
            EVENT_MwSteam_ST_START);
        break;
    case MODE_MW_STEAM:   /* 并列加热 */
        StateMachine_EnqueueEvent(&g_ctx,
            EVENT_MwMicrowave_MW_START);
        StateMachine_EnqueueEvent(&g_ctx,
            EVENT_MwSteam_ST_START);
        break;
    default:
        return 0;
    }
    /* [[STABLE_USER_CODE_END:Application_StartStage]] */
    return 1;
}
```

### 8.4 StopStage

| 项目 | 内容 |
|---|---|
| 用途 | 当前阶段停止 |

**实现例**:

```c
int RoleFunc_Application_StopStage(...)
{
    /* [[STABLE_USER_CODE_START:Application_StopStage]] */
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_MwMicrowave_MW_STOP);
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_MwOven_OV_STOP);
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_MwGrill_GR_STOP);
    StateMachine_EnqueueEvent(&g_ctx,
        EVENT_MwSteam_ST_STOP);
    /* [[STABLE_USER_CODE_END:Application_StopStage]] */
    return 1;
}
```

### 8.5 CheckStageDone

| 项目 | 内容 |
|---|---|
| 用途 | 阶段完成判定（时间 + 温度 + 传感器融合） |

**实现例**:

```c
int RoleFunc_Application_CheckStageDone(...)
{
    /* [[STABLE_USER_CODE_START:Application_CheckStageDone]] */
    /* 条件 1: 时间到 */
    if (ctx->data.stage_elapsed >= ctx->data.stage_duration) {
        return 1;
    }
    /* 条件 2: 温度到达目标 */
    if (ctx->data.stage_mode == MODE_OVEN &&
        ctx->data.oven_current_temp >= ctx->data.oven_target_temp) {
        return 1;
    }
    /* 条件 3: 红外传感器判定完成 */
    if (ctx->data.ir_value > IR_DONE_THRESHOLD) {
        return 1;
    }
    return 0;
    /* [[STABLE_USER_CODE_END:Application_CheckStageDone]] */
}
```

### 8.6 NextStage

| 项目 | 内容 |
|---|---|
| 用途 | 下一阶段推进 |

**实现例**:

```c
int RoleFunc_Application_NextStage(...)
{
    /* [[STABLE_USER_CODE_START:Application_NextStage]] */
    ctx->data.seq_step++;
    if (ctx->data.seq_step >= ctx->data.seq_total) {
        return 0;   /* 全阶段完成 */
    }
    /* 加载下一阶段参数 */
    uint8_t idx = ctx->data.seq_step;
    ctx->data.stage_mode = g_rx_seq.steps[idx].mode;
    ctx->data.oven_target_temp = g_rx_seq.steps[idx].temperature;
    ctx->data.stage_duration = g_rx_seq.steps[idx].duration_ms;
    return 1;
    /* [[STABLE_USER_CODE_END:Application_NextStage]] */
}
```

### 8.7 ReportStatus

| 项目 | 内容 |
|---|---|
| 用途 | 向 Android 面板报告状态 |

**实现例**:

```c
int RoleFunc_Application_ReportStatus(...)
{
    /* [[STABLE_USER_CODE_START:Application_ReportStatus]] */
    /* 通过 Driver 层发送 */
    RoleFunc_Driver_SendStatusMaster(NULL, ctx);
    /* [[STABLE_USER_CODE_END:Application_ReportStatus]] */
    return 1;
}
```

### 8.8 ReportComplete

| 项目 | 内容 |
|---|---|
| 用途 | 全阶段完成报告 |

**实现例**:

```c
int RoleFunc_Application_ReportComplete(...)
{
    /* [[STABLE_USER_CODE_START:Application_ReportComplete]] */
    /* 发送完成状态 */
    RoleFunc_Driver_SendStatusMaster(NULL, ctx);
    /* 可选: 蜂鸣器提示 */
    Buzzer_Beep(3, 200);
    /* [[STABLE_USER_CODE_END:Application_ReportComplete]] */
    return 1;
}
```

### 8.9 LogAppError

| 项目 | 内容 |
|---|---|
| 用途 | 应用故障记录 |

**实现例**:

```c
int RoleFunc_Application_LogAppError(...)
{
    /* [[STABLE_USER_CODE_START:Application_LogAppError]] */
    Log_Write(LOG_LEVEL_ERROR, "App fault, err=%d",
              ctx->data.error_code);
    /* [[STABLE_USER_CODE_END:Application_LogAppError]] */
    return 1;
}
```

### 8.10 ClearAppError

| 项目 | 内容 |
|---|---|
| 用途 | 应用故障清除 |

**实现例**:

```c
int RoleFunc_Application_ClearAppError(...)
{
    /* [[STABLE_USER_CODE_START:Application_ClearAppError]] */
    ctx->data.error_code = 0;
    ctx->data.seq_step = 0;
    ctx->data.seq_total = 0;
    ctx->data.stage_elapsed = 0;
    /* [[STABLE_USER_CODE_END:Application_ClearAppError]] */
    return 1;
}
```

---

## 9. 通用实现模式

### 9.1 层间调用

上层 → 下层：**直接函数调用**

```c
/* MwOven → Driver */
RoleFunc_Driver_SetHeaterPwm(NULL, ctx);
```

下层 → 上层：**通过事件队列**

```c
/* Driver → Application */
StateMachine_EnqueueEvent(&g_ctx,
    EVENT_Application_STAGE_DONE);
```

### 9.2 错误处理

```c
static uint8_t error_count = 0;
if (check_error()) {
    error_count++;
    if (error_count >= THRESHOLD) {
        ctx->data.error_code = ERR_CODE;
        return 1;   /* 触发错误迁移 */
    }
} else {
    error_count = 0;
}
```

### 9.3 PID 控制

```c
typedef struct {
    float kp, ki, kd;
    float integral;
    float prev_error;
    float out_min, out_max;
} Pid_t;
```

### 9.4 事件发布

```c
StateMachine_EnqueueEvent(&g_ctx,
    EVENT_<Layer>_<EventName>);
```

### 9.5 用户代码保护

所有实现放在 `[[STABLE_USER_CODE_START:...]]` / `_END` 之间：

- 重新生成时保留
- 手动代码变更安全
- 代码审查友好

---

## 10. 变更历史

| 版本 | 日期 | 内容 |
|---|---|---|
| 1.0 | 2026-10-04 | 初版（54 个 Role 函数参考） |

---

*本文档为 Galanz 复合烹饪器具的 StaTable Role 函数参考资料。*