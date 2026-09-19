/**
 * @file    statable_interrupt.c
 * @brief   割り込み処理ISR
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 21:33:04
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
    if (g_tick_100ms >= 5) { StateMachine_EnqueueEvent(EVENT_TICK); }
    g_system_tick++;
UpdateDerivedTimers();

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    /* ユーザー追加コードをここに記述 */
    /* [[STABLE_USER_CODE_END:TIMER0]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: TIMER0");
}
