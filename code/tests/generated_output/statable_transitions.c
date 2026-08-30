/**
 * @file    statable_transitions.c
 * @brief   状態遷移ロジック
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-08-31 01:30:31
 */

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_transitions.h"
#include "statable_role_functions.h"

/*==============================================================*/
 *  状態遷移テーブル
/*==============================================================*/

    /* STATE_INIT */
    {
        { STATE_IDLE, NULL, Action_PowerOn }, /* INIT -> IDLE (event: POWER_ON) */
        { STATE_INIT, NULL, NULL }, /* No transition */
        { STATE_INIT, NULL, NULL }, /* No transition */
        { STATE_INIT, NULL, NULL }, /* No transition */
    },
    /* STATE_IDLE */
    {
        { STATE_IDLE, NULL, NULL }, /* No transition */
        { STATE_RUNNING, Condition_StartOk, Action_Start }, /* IDLE -> RUNNING (event: START) */
        { STATE_IDLE, NULL, NULL }, /* No transition */
        { STATE_IDLE, NULL, NULL }, /* No transition */
    },
    /* STATE_RUNNING */
    {
        { STATE_RUNNING, NULL, NULL }, /* No transition */
        { STATE_RUNNING, NULL, NULL }, /* No transition */
        { STATE_IDLE, NULL, Action_Stop }, /* RUNNING -> IDLE (event: STOP) */
        { STATE_ERROR, NULL, Action_HandleError }, /* RUNNING -> ERROR (event: ERROR_DETECTED) */
    },
    /* STATE_ERROR */
    {
        { STATE_ERROR, NULL, NULL }, /* No transition */
        { STATE_ERROR, NULL, NULL }, /* No transition */
        { STATE_ERROR, NULL, NULL }, /* No transition */
        { STATE_ERROR, NULL, NULL }, /* No transition */
    },

/*==============================================================*/
 *  状態遷移関数
/*==============================================================*/

/**
 * @brief  状態遷移処理
 * @param  current_state  現在の状態
 * @param  event          発生したイベント
 * @param  ctx            システムコンテキストポインタ
 * @return 遷移後の状態
 */
STATE_t StateMachine_Process(
    STATE_t current_state,
    EVENT_t event,
    SystemContext_t *ctx
)
{
    STATE_t next_state = current_state;

    /* NULLチェック */
    if (ctx == NULL) {
        LOG_ERROR("NULL pointer: ctx");
        return current_state;
    }

    /* 範囲チェック */
    if (current_state >= STATE_MAX || event >= EVENT_MAX) {
        LOG_ERROR("Out of range: state=%d, event=%d", current_state, event);
        return current_state;
    }

    LOG_DEBUG("Enter StateMachine_Process: state=%d, event=%d", current_state, event);

    /* 遷移テーブルから該当セルを取得 */
    const TransitionCell_t *cell = &transition_matrix[current_state][event];

    /* 条件チェック */
    if (cell->condition != NULL) {
        if (!cell->condition(ctx)) {
            LOG_DEBUG("Condition not met");
            return current_state;
        }
    }

    /* アクション実行 */
    if (cell->action != NULL) {
        cell->action(ctx);
    }

    /* 状態遷移 */
    if (cell->next_state != STATE_MAX) {
        next_state = cell->next_state;
        LOG_INFO("Transition: %d -> %d", current_state, next_state);
    }

    LOG_DEBUG("Exit StateMachine_Process: next_state=%d", next_state);

    return next_state;
}