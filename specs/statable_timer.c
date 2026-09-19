/**
 * @file    statable_timer.c
 * @brief   タイマ処理
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-15 20:38:05
 */

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types_common.h"
#include "Driver/statable_types_Driver.h"
#include "Middleware/statable_types_Middleware.h"
#include "Application/statable_types_Application.h"

/*==============================================================*/
 *  型定義
/*==============================================================*/



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
    ctx->data.g_tick_10ms = 0;

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
}