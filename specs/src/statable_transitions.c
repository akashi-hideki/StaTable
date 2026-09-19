/**
 * @file    statable_transitions.c
 * @brief   状態遷移ロジック
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

#include "statable_transitions.h"
#include "statable_role_functions.h"

/*==============================================================*/
 *  状態遷移テーブル
/*==============================================================*/

/* ===== セル単位遷移関数の前方宣言 ===== */
static STATE_Application_t t_Idle_START(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx);
static STATE_Application_t t_Active_STOP(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx);
static STATE_Application_t t_Active_ERROR(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx);
static STATE_Application_t t_Error_NONE(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx);


/* 遷移関数ポインタ型 */
typedef STATE_Application_t (*TransitionFunc_Application_t)(
    const TransitionContext_Application_t *, SystemContext_t *);

/* ============================================================== */
/*  状態遷移テーブル: 行=状態, 列=イベント                  */
/*  グローバル変数（外部から参照可能）                            */
/* ============================================================== */
const TransitionFunc_Application_t transition_table_Application
    [STATE_Application_MAX][EVENT_Application_MAX] = {
    /*          | START          | STOP           | ERROR          | TIMER0_OVERFLOW | NONE           */
    /* --------+--------------+--------------+--------------+---------------+--------------*/
    /* Idle    */ { t_Idle_START  , NULL          , NULL          , NULL           , NULL           },
    /* Active  */ { NULL          , t_Active_STOP , t_Active_ERROR, NULL           , NULL           },
    /* Error   */ { NULL          , NULL          , NULL          , NULL           , t_Error_NONE   },
    /* Halt    */ { NULL          , NULL          , NULL          , NULL           , NULL           },
};


/**
 * @brief  セル遷移: STATE_Application_Idle -[EVENT_Application_START]-> Active
 */
static STATE_Application_t t_Idle_START(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Application_Init()(transition, ctx);
        next_state = STATE_Application_Active;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Application_Active -[EVENT_Application_STOP]-> Idle
 */
static STATE_Application_t t_Active_STOP(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Application_Stop()(transition, ctx);
        next_state = STATE_Application_Idle;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Application_Active -[EVENT_Application_ERROR]-> Error
 */
static STATE_Application_t t_Active_ERROR(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] */
    if (err_code != 0) {
        RoleFunc_Application_Log()(transition, ctx);
        next_state = STATE_Application_Error;
        return next_state;
    }

    /* 遷移[1] */
    if (err_code == 0) {
        RoleFunc_Application_Ignore()(transition, ctx);
        next_state = STATE_Application_Active;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Application_Error -[EVENT_Application_NONE]-> Active
 */
static STATE_Application_t t_Error_NONE(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] */
    if (retry_count < 3) {
        RoleFunc_Application_RetryCount++(transition, ctx);
        next_state = STATE_Application_Active;
        return next_state;
    }

    /* 遷移[1] */
    if (retry_count >= 3) {
        next_state = STATE_Application_Halt;
        return next_state;
    }

    return next_state;
}


/*==============================================================*/
 *  状態遷移関数
/*==============================================================*/

/**
 * @brief  Application層の状態遷移処理
 * @param  current_state  現在の状態
 * @param  event          発生したイベント
 * @param  ctx            システムコンテキストポインタ
 * @return 遷移後の状態
 */
STATE_Application_t StateMachine_Process_Application(
    STATE_Application_t current_state,
    EVENT_Application_t event,
    SystemContext_t *ctx
)
{
    TransitionContext_Application_t transition = {
        .from_state = current_state,
        .event = event,
    };
    TransitionFunc_Application_t func = transition_table_Application[current_state][event];
    if (func != NULL) {
        return func(&transition, ctx);
    }
    return current_state;
}
