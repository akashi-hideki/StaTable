/**
 * @file    statable_transitions.c
 * @brief   状態遷移ロジック
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 11:55:41
 */

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_transitions.h"
#include "statable_role_functions.h"

/*==============================================================*/
 *  状態遷移テーブル
/*==============================================================*/

/* ===== セル単位遷移関数の前方宣言 ===== */
static STATE_t t_INIT_POWER_ON(
    const TransitionContext_t *transition,
    SystemContext_t *ctx);
static STATE_t t_IDLE_START(
    const TransitionContext_t *transition,
    SystemContext_t *ctx);
static STATE_t t_RUNNING_STOP(
    const TransitionContext_t *transition,
    SystemContext_t *ctx);
static STATE_t t_RUNNING_ERROR_DETECTED(
    const TransitionContext_t *transition,
    SystemContext_t *ctx);


/* 遷移関数ポインタ型 */
typedef STATE_t (*TransitionFunc_t)(
    const TransitionContext_t *, SystemContext_t *);

/* ============================================================== */
/*  状態遷移テーブル: 行=状態, 列=イベント                  */
/*  グローバル変数（外部から参照可能）                            */
/* ============================================================== */
const TransitionFunc_t transition_matrix
    [STATE_MAX][EVENT_MAX] = {
    /*           | POWER_ON        | START          | STOP           | ERROR_DETECTED           */
    /* ---------+---------------+--------------+--------------+------------------------*/
    /* INIT     */ { t_INIT_POWER_ON, NULL          , NULL          , NULL                     },
    /* IDLE     */ { NULL           , t_IDLE_START  , NULL          , NULL                     },
    /* RUNNING  */ { NULL           , NULL          , t_RUNNING_STOP, t_RUNNING_ERROR_DETECTED },
    /* ERROR    */ { NULL           , NULL          , NULL          , NULL                     },
};


/**
 * @brief  セル遷移: STATE_INIT -[EVENT_POWER_ON]-> IDLE
 */
static STATE_t t_INIT_POWER_ON(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    STATE_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        next_state = STATE_IDLE;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_IDLE -[EVENT_START]-> RUNNING
 */
static STATE_t t_IDLE_START(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    STATE_t next_state = transition->from_state;

    /* 遷移[0] */
    if (StartOk) {
        next_state = STATE_RUNNING;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_RUNNING -[EVENT_STOP]-> IDLE
 */
static STATE_t t_RUNNING_STOP(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    STATE_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        next_state = STATE_IDLE;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_RUNNING -[EVENT_ERROR_DETECTED]-> ERROR
 */
static STATE_t t_RUNNING_ERROR_DETECTED(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    STATE_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        next_state = STATE_ERROR;
        return next_state;
    }

    return next_state;
}


/*==============================================================*/
 *  状態遷移関数
/*==============================================================*/

/**
 * @brief  システム層の状態遷移処理
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
    TransitionContext_t transition = {
        .from_state = current_state,
        .event = event,
    };
    TransitionFunc_t func = transition_matrix[current_state][event];
    if (func != NULL) {
        return func(&transition, ctx);
    }
    return current_state;
}
