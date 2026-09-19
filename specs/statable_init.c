/**
 * @file    statable_init.c
 * @brief   初期化処理
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
    memset(&ctx->data.counter, 0, sizeof(ctx->data.counter));
    memset(&ctx->data.error_code, 0, sizeof(ctx->data.error_code));
    memset(&ctx->data.retry_count, 0, sizeof(ctx->data.retry_count));
    ctx->data.rx_ready = false;
    memset(&ctx->data.rx_data, 0, sizeof(ctx->data.rx_data));
    memset(&ctx->data.g_system_tick, 0, sizeof(ctx->data.g_system_tick));
    memset(&ctx->data.g_tick_10ms, 0, sizeof(ctx->data.g_tick_10ms));

    /* イベントフラグの初期化 */
    ctx->flags.EVT_INIT_DONE = 0;
    ctx->flags.EVT_ERROR = 0;

    /* 保留イベントの初期化 */
    ctx->pending_event = 0;
    ctx->pending_event_valid = false;

    LOG_DEBUG("Exit SystemContext_Init");
}