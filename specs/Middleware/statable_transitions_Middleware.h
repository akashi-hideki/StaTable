/**
 * @file    statable_transitions_Middleware.h
 * @brief   状態遷移関数宣言
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-15 20:38:05
 */

#ifndef STATABLE_TRANSITIONS_H_MIDDLEWARE
#define STATABLE_TRANSITIONS_H_MIDDLEWARE

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types_Middleware.h"

/*==============================================================*/
 *  関数宣言
/*==============================================================*/

/**
 * @brief  状態遷移処理
 * @param  current_state  現在の状態
 * @param  event          発生したイベント
 * @param  ctx            システムコンテキストポインタ
 * @return 遷移後の状態
 */
STATE_Middleware_t StateMachine_Process_Middleware(
    STATE_Middleware_t current_state,
    EVENT_Middleware_t event,
    SystemContext_t *ctx
);

#endif /* STATABLE_TRANSITIONS_H_MIDDLEWARE */