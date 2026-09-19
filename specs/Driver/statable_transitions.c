/**
 * @file    statable_transitions.c
 * @brief   状態遷移ロジック
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-15 19:56:53
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
static STATE_Driver_t t_Idle_INIT(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx);
static STATE_Driver_t t_Initializing_READY(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx);
static STATE_Driver_t t_Initializing_FAIL(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx);
static STATE_Driver_t t_Ready_FAIL(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx);
static STATE_Driver_t t_Error_RESET(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx);


/* 遷移関数ポインタ型 */
typedef STATE_Driver_t (*TransitionFunc_Driver_t)(
    const TransitionContext_Driver_t *, SystemContext_t *);

/* ============================================================== */
/*  状態遷移テーブル: 行=状態, 列=イベント                  */
/*  グローバル変数（外部から参照可能）                            */
/* ============================================================== */
const TransitionFunc_Driver_t transition_table_Driver
    [STATE_Driver_MAX][EVENT_Driver_MAX] = {
    /*                | INIT           | READY                | FAIL                | RESET          */
    /* --------------+--------------+--------------------+-------------------+--------------*/
    /* Idle          */ { t_Idle_INIT   , NULL                , NULL               , NULL           },
    /* Initializing  */ { NULL          , t_Initializing_READY, t_Initializing_FAIL, NULL           },
    /* Ready         */ { NULL          , NULL                , t_Ready_FAIL       , NULL           },
    /* Error         */ { NULL          , NULL                , NULL               , t_Error_RESET  },
};


/**
 * @brief  セル遷移: STATE_Driver_Idle -[EVENT_Driver_INIT]-> Initializing
 */
static STATE_Driver_t t_Idle_INIT(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Driver_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Driver_Driver.Init(transition, ctx);
        next_state = STATE_Driver_Initializing;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Driver_Initializing -[EVENT_Driver_READY]-> Ready
 */
static STATE_Driver_t t_Initializing_READY(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Driver_t next_state = transition->from_state;

    /* 遷移[0] */
    if (error_code == 0) {
        next_state = STATE_Driver_Ready;
        return next_state;
    }

    /* 遷移[1] */
    if (error_code != 0) {
        RoleFunc_Driver_Driver.LogError(transition, ctx);
        next_state = STATE_Driver_Error;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Driver_Initializing -[EVENT_Driver_FAIL]-> Error
 */
static STATE_Driver_t t_Initializing_FAIL(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Driver_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Driver_Driver.LogError(transition, ctx);
        next_state = STATE_Driver_Error;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Driver_Ready -[EVENT_Driver_FAIL]-> Error
 */
static STATE_Driver_t t_Ready_FAIL(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Driver_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Driver_Driver.LogError(transition, ctx);
        next_state = STATE_Driver_Error;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Driver_Error -[EVENT_Driver_RESET]-> Idle
 */
static STATE_Driver_t t_Error_RESET(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Driver_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Driver_Driver.Reset(transition, ctx);
        next_state = STATE_Driver_Idle;
        return next_state;
    }

    return next_state;
}


/*==============================================================*/
 *  状態遷移関数
/*==============================================================*/

/**
 * @brief  Driver層の状態遷移処理
 * @param  current_state  現在の状態
 * @param  event          発生したイベント
 * @param  ctx            システムコンテキストポインタ
 * @return 遷移後の状態
 */
STATE_Driver_t StateMachine_Process_Driver(
    STATE_Driver_t current_state,
    EVENT_Driver_t event,
    SystemContext_t *ctx
)
{
    TransitionContext_Driver_t transition = {
        .from_state = current_state,
        .event = event,
    };
    TransitionFunc_Driver_t func = transition_table_Driver[current_state][event];
    if (func != NULL) {
        return func(&transition, ctx);
    }
    return current_state;
}
