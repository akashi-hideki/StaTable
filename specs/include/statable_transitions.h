/**
 * @file    statable_transitions.h
 * @brief   状態遷移関数宣言
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 21:33:04
 */

#ifndef STATABLE_TRANSITIONS_H
#define STATABLE_TRANSITIONS_H

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types.h"

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
STATE_Application_t StateMachine_Process_Application(
    STATE_Application_t current_state,
    EVENT_Application_t event,
    SystemContext_t *ctx
);

#endif /* STATABLE_TRANSITIONS_H */