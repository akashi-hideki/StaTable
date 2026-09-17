/**
 * @file    statable_transitions_Application.h
 * @brief   状態遷移関数宣言
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-16 22:39:54
 */

#ifndef STATABLE_TRANSITIONS_H_APPLICATION
#define STATABLE_TRANSITIONS_H_APPLICATION

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types_Application.h"

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

#endif /* STATABLE_TRANSITIONS_H_APPLICATION */