/**
 * @file    statable_interrupt.c
 * @brief   割り込み処理ISR
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 12:37:52
 */

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types.h"
#include "statable_all.h"

/*==============================================================*/
 *  状態遷移関数
/*==============================================================*/

/**
 * @brief  UART_RX 割り込みハンドラ
 * @note   UART受信割り込み
 */
void ISR_UARTRX(void)
{

    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: UART_RX");

    /* ===== アクション（自動生成） ===== */
    EVT_START_REQ = 1;
    if (ctx->data.battery_voltage > 3000) { EVT_STOP_REQ = 1; }

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:UARTRX]] */
    /* ユーザー追加コードをここに記述 */
    /* [[STABLE_USER_CODE_END:UARTRX]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: UART_RX");
}

/**
 * @brief  TimerTick 割り込みハンドラ
 * @note   タイマ割り込み
 */
void ISR_TimerTick(void)
{

    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: TimerTick");

    /* ===== アクション（自動生成） ===== */
    ctx->data.system_tick++;

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:TimerTick]] */
    /* ユーザー追加コードをここに記述 */
    /* [[STABLE_USER_CODE_END:TimerTick]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: TimerTick");
}
