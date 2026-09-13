/**
 * @file    statable_timer.c
 * @brief   タイマ処理
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

/*==============================================================*/
 *  型定義
/*==============================================================*/

/* タイマ変数構造体 */
/* システム全体で使用するタイマ変数を管理 */
typedef struct {
    volatile uint32_t g_system_tick; /* 1ms */
    volatile uint32_t g_high_speed_tick; /* 100us */
    uint8_t g_tick_10ms; /* 10ms */
    uint8_t g_tick_100ms; /* 100ms */
    uint16_t g_hs_tick_1ms; /* 1ms */
} TimerVariables_t;

/*==============================================================*/
 *  初期化関数
/*==============================================================*/

/**
 * @brief  タイマ変数初期化
 * @param  ctx  システムコンテキストポインタ
 */
void Timer_Init(SystemContext_t *ctx)
{
    if (ctx == NULL) {
        return;
    }
    LOG_DEBUG("Enter Timer_Init");

    ctx->data.g_system_tick = 0;
    ctx->data.g_high_speed_tick = 0;
    ctx->data.g_tick_10ms = 0;
    ctx->data.g_tick_100ms = 0;
    ctx->data.g_hs_tick_1ms = 0;

    LOG_DEBUG("Exit Timer_Init");
}

/*==============================================================*/
 *  状態遷移関数
/*==============================================================*/

/**
 * @brief  タイマ更新処理
 * @param  ctx  システムコンテキストポインタ
 */
void Timer_Update(SystemContext_t *ctx)
{
    if (ctx == NULL) {
        return;
    }
    ctx->data.g_tick_10ms = (uint8_t)(ctx->data.g_system_tick / 10);
    ctx->data.g_tick_100ms = (uint8_t)(ctx->data.g_system_tick / 100);
    ctx->data.g_hs_tick_1ms = (uint16_t)(ctx->data.g_high_speed_tick / 10);
}