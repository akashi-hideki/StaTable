/**
 * @file    statable_transitions_Application.c
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

#include "statable_transitions_Application.h"
#include "statable_role_functions_Application.h"

/*==============================================================*/
 *  状態遷移テーブル
/*==============================================================*/

/* ===== セル単位遷移関数の前方宣言 ===== */
static STATE_Application_t t_Boot_BOOT(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx);
static STATE_Application_t t_Init_START(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx);
static STATE_Application_t t_Running_PAUSE(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx);
static STATE_Application_t t_Running_STOP(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx);
static STATE_Application_t t_Paused_RESUME(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx);
static STATE_Application_t t_Paused_STOP(
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
    /*           | BOOT           | START          | PAUSE           | RESUME          | STOP           */
    /* ---------+--------------+--------------+---------------+---------------+--------------*/
    /* Boot     */ { t_Boot_BOOT   , NULL          , NULL           , NULL           , NULL           },
    /* Init     */ { NULL          , t_Init_START  , NULL           , NULL           , NULL           },
    /* Running  */ { NULL          , NULL          , t_Running_PAUSE, NULL           , t_Running_STOP },
    /* Paused   */ { NULL          , NULL          , NULL           , t_Paused_RESUME, t_Paused_STOP  },
    /* Stopped  */ { NULL          , NULL          , NULL           , NULL           , NULL           },
};


/**
 * @brief  セル遷移: STATE_Application_Boot -[EVENT_Application_BOOT]-> Init
 */
static STATE_Application_t t_Boot_BOOT(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Application_Application.Boot(transition, ctx);
        next_state = STATE_Application_Init;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Application_Init -[EVENT_Application_START]-> Running
 */
static STATE_Application_t t_Init_START(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Application_Application.Start(transition, ctx);
        next_state = STATE_Application_Running;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Application_Running -[EVENT_Application_PAUSE]-> Paused
 */
static STATE_Application_t t_Running_PAUSE(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] */
    if (counter > 0) {
        next_state = STATE_Application_Paused;
        return next_state;
    }

    /* 遷移[1] */
    if (counter == 0) {
        next_state = STATE_Application_Running;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Application_Running -[EVENT_Application_STOP]-> Stopped
 */
static STATE_Application_t t_Running_STOP(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] */
    if (g_system_tick > 100) {
        RoleFunc_Application_Application.Pause(transition, ctx);
        next_state = STATE_Application_Stopped;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Application_Paused -[EVENT_Application_RESUME]-> Running
 */
static STATE_Application_t t_Paused_RESUME(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        RoleFunc_Application_Application.Resume(transition, ctx);
        next_state = STATE_Application_Running;
        return next_state;
    }

    return next_state;
}

/**
 * @brief  セル遷移: STATE_Application_Paused -[EVENT_Application_STOP]-> Stopped
 */
static STATE_Application_t t_Paused_STOP(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    STATE_Application_t next_state = transition->from_state;

    /* 遷移[0] (条件なし遷移) */
    if (1) {
        next_state = STATE_Application_Stopped;
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
