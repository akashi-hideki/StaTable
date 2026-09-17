/**
 * @file    statable_interrupt.c
 * @brief   割り込み処理ISR
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-16 22:39:54
 */

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_all.h"

/*==============================================================*/
 *  状態遷移関数
/*==============================================================*/

/**
 * @brief  TIMER0 割り込みハンドラ
 * @note   1ms周期タイマ
 */
void ISR_TIMER0(void)
{

    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: TIMER0");

    /* ===== アクション（自動生成） ===== */
    ctx->data.g_system_tick++;

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    /* ユーザー追加コードをここに記述 */

    /* [[STABLE_USER_CODE_END:TIMER0]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: TIMER0");
}

/**
 * @brief  TIMER1 割り込みハンドラ
 * @note   10ms周期タイマ
 * @note   使用ロール関数:
 *         - Application.HandleTick
 */
void ISR_TIMER1(void)
{

    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: TIMER1");

    /* ===== アクション（自動生成） ===== */
    ctx->data.g_tick_10ms++;
    RoleFunc_Application_HandleTick(NULL, ctx);

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:TIMER1]] */
    /* ユーザー追加コードをここに記述 */

    /* [[STABLE_USER_CODE_END:TIMER1]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: TIMER1");
}

/**
 * @brief  UART_RX 割り込みハンドラ
 * @note   UART受信割り込み
 * @note   使用ロール関数:
 *         - Application.HandleRx
 */
void ISR_UARTRX(void)
{

    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: UART_RX");

    /* ===== アクション（自動生成） ===== */
    ctx->data.rx_ready = true;
    if (ctx->data.rx_ready) { RoleFunc_Application_HandleRx(NULL, ctx); }

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:UARTRX]] */
    /* ユーザー追加コードをここに記述 */

    /* [[STABLE_USER_CODE_END:UARTRX]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: UART_RX");
}

/**
 * @brief  GPIO_INT 割り込みハンドラ
 * @note   GPIO割り込み
 * @note   使用ロール関数:
 *         - Application.HandleError
 */
void ISR_GPIOINT(void)
{

    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: GPIO_INT");

    /* ===== アクション（自動生成） ===== */
    if (ctx->data.error_code != 0) { RoleFunc_Application_HandleError(NULL, ctx); }

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:GPIOINT]] */
    /* ユーザー追加コードをここに記述 */

    /* [[STABLE_USER_CODE_END:GPIOINT]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: GPIO_INT");
}

/**
 * @brief  DRIVER_INT 割り込みハンドラ
 * @note   ドライバ補助割り込み
 * @note   使用ロール関数:
 *         - Driver.CheckRx
 */
void ISR_DRIVERINT(void)
{

    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: DRIVER_INT");

    /* ===== アクション（自動生成） ===== */
    RoleFunc_Driver_CheckRx(NULL, ctx);
    ctx->data.counter++;

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:DRIVERINT]] */
    /* ユーザー追加コードをここに記述 */

    /* [[STABLE_USER_CODE_END:DRIVERINT]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: DRIVER_INT");
}
