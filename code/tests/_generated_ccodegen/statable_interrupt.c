/**
 * @file    statable_interrupt.c
 * @brief   割り込み処理ISR
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 11:55:41
 */

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types.h"

/*==============================================================*/
 *  状態遷移関数
/*==============================================================*/

/* 割り込み処理: UART_RX */
void ISR_UARTRX(void)
{
    LOG_DEBUG("Enter ISR");

    EVT_START_REQ = 1;
    if (ctx->data.battery_voltage > 3000) {
        EVT_STOP_REQ = 1;
    }

    LOG_DEBUG("Exit ISR");
}

/* 割り込み処理: TimerTick */
void ISR_TimerTick(void)
{
    LOG_DEBUG("Enter ISR");

    ctx->data.system_tick++;

    LOG_DEBUG("Exit ISR");
}
