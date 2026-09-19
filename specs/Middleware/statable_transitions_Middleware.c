/**
 * @file    statable_transitions_Middleware.c
 * @brief   状態遷移ロジック
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

#include "statable_transitions_Middleware.h"
#include "statable_role_functions_Middleware.h"

/*==============================================================*/
 *  状態遷移テーブル
/*==============================================================*/

/* ===== セル単位遷移関数の前方宣言 ===== */
static STATE_Middleware_t t_Idle_CONNECT(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx);
static STATE_Middleware_t t_Connecting_CONNECTED(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx);
static STATE_Middleware_t t_Connecting_ERROR(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx);
static STATE_Middleware_t t_Connected_ERROR(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx);
static STATE_Middleware_t t_Error_RETRY(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx);


/* 遷移関数ポインタ型 */
typedef STATE_Middleware_t (*TransitionFunc_Middleware_t)(
    const TransitionContext_Middleware_t *, SystemContext_t *);

/* ============================================================== */
/*  状態遷移テーブル: 行=状態, 列=イベント                  */
/*  グローバル変数（外部から参照可能）                            */
/* ============================================================== */
const TransitionFunc_Middleware_t transition_table_Middleware
    [STATE_Middleware_MAX][EVENT_Middleware_MAX] = {
    /*              | CONNECT        | CONNECTED              | ERROR              | RETRY          */
    /* ------------+--------------+----------------------+------------------+--------------*/
    /* Idle        */ { t_Idle_CONNECT, NULL                  , NULL              , NULL           },
    /* Connecting  */ { NULL          , t_Connecting_CONNECTED, t_Connecting_ERROR, NULL           },
    /* Connected   */ { NULL          , NULL                  , t_Connected_ERROR , NULL           },
    /* Error       */ { NULL          , NULL                  , NULL              , t_Error_RETRY  },
};


/**
 * @brief  セル遷移: STATE_Middleware_Idle -[EVENT_Middleware_CONNECT]-> Connecting
 */
static STATE_Middleware_t t_Idle_CONNECT(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Middleware_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Middleware_Middleware.Connect(transition, ctx);
        next_state = STATE_Middleware_Connecting;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Middleware_Connecting -[EVENT_Middleware_CONNECTED]-> Connected
 */
static STATE_Middleware_t t_Connecting_CONNECTED(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Middleware_t next_state = transition->from_state;

    /* 遷移[0] */
    if (retry_count < 3) {
        next_state = STATE_Middleware_Connected;
        return next_state;
    }

    /* 遷移[1] */
    if (retry_count >= 3) {
        RoleFunc_Middleware_Middleware.HandleErr(transition, ctx);
        next_state = STATE_Middleware_Error;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Middleware_Connecting -[EVENT_Middleware_ERROR]-> Error
 */
static STATE_Middleware_t t_Connecting_ERROR(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Middleware_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Middleware_Middleware.HandleErr(transition, ctx);
        next_state = STATE_Middleware_Error;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Middleware_Connected -[EVENT_Middleware_ERROR]-> Error
 */
static STATE_Middleware_t t_Connected_ERROR(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Middleware_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Middleware_Middleware.HandleErr(transition, ctx);
        next_state = STATE_Middleware_Error;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Middleware_Error -[EVENT_Middleware_RETRY]-> Idle
 */
static STATE_Middleware_t t_Error_RETRY(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Middleware_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Middleware_Middleware.Retry(transition, ctx);
        next_state = STATE_Middleware_Idle;
        return next_state;
    }

    return next_state;
}


/*==============================================================*/
 *  状態遷移関数
/*==============================================================*/

/**
 * @brief  Middleware層の状態遷移処理
 * @param  current_state  現在の状態
 * @param  event          発生したイベント
 * @param  ctx            システムコンテキストポインタ
 * @return 遷移後の状態
 */
STATE_Middleware_t StateMachine_Process_Middleware(
    STATE_Middleware_t current_state,
    EVENT_Middleware_t event,
    SystemContext_t *ctx
)
{
    TransitionContext_Middleware_t transition = {
        .from_state = current_state,
        .event = event,
    };
    TransitionFunc_Middleware_t func = transition_table_Middleware[current_state][event];
    if (func != NULL) {
        return func(&transition, ctx);
    }
    return current_state;
}
