/**
 * @file    statable_init.c
 * @brief   初期化処理
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
 *  初期化関数
/*==============================================================*/

/**
 * @brief  システムコンテキスト初期化
 * @param  ctx  システムコンテキストポインタ
 */
void SystemContext_Init(SystemContext_t *ctx)
{
    /* NULLチェック */
    if (ctx == NULL) {
        LOG_ERROR("NULL pointer: ctx");
        return;
    }

    LOG_DEBUG("Enter SystemContext_Init");

    /* グローバル変数の初期化 */
    ctx->data.battery_voltage = 0;
    ctx->data.system_tick = 0;
    ctx->data.temperature = 0;
    memset(ctx->data.data_buffer, 0, sizeof(ctx->data.data_buffer));

    /* イベントフラグの初期化 */
    ctx->flags.EVT_POWER_ON_REQ = 0;
    ctx->flags.EVT_START_REQ = 0;
    ctx->flags.EVT_STOP_REQ = 0;
    ctx->flags.EVT_ERROR_FLAG = 0;

    /* 保留イベントの初期化 */
    ctx->pending_event = 0;
    ctx->pending_event_valid = false;

    LOG_DEBUG("Exit SystemContext_Init");
}