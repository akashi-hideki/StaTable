/**
 * @file    statable_role_functions.c
 * @brief   ロール関数実装
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

#include "statable_role_functions.h"

/*==============================================================*/
 *  ロール関数実装
/*==============================================================*/


/* ============================================================== */
/*  Transition ID 定数                                            */
/* ============================================================== */
#define TRANSITION_ID_NONE   ((uint16_t)0xFFFF)


/* ============================================================== */
/*  ロール関数 呼び出し元テーブル（共通構造体）                    */
/*  {from_state, event} の組でセルを識別                          */
/* ============================================================== */
typedef struct {
    STATE_Middleware_t from_state;   /* 遷移元状態 */
    EVENT_Middleware_t event;        /* 発生イベント */
} RoleFuncCallSiteEntry_Middleware_t;


/* Transition_GetId 前方宣言（本体はファイル末尾） */
static uint16_t Transition_GetId(
    const TransitionContext_Middleware_t *transition,
    const RoleFuncCallSiteEntry_Middleware_t *table,
    uint16_t table_size);


/* --- Connect の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Middleware_t call_sites_Connect[] = {
    { STATE_Middleware_Idle, EVENT_Middleware_CONNECT },
};
#define CALL_SITES_Connect_COUNT \
    (sizeof(call_sites_Connect) / sizeof(call_sites_Connect[0]))


/* --- HandleErr の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Middleware_t call_sites_HandleErr[] = {
    { STATE_Middleware_Connecting, EVENT_Middleware_CONNECTED },
    { STATE_Middleware_Connecting, EVENT_Middleware_ERROR },
    { STATE_Middleware_Connected,  EVENT_Middleware_ERROR },
};
#define CALL_SITES_HandleErr_COUNT \
    (sizeof(call_sites_HandleErr) / sizeof(call_sites_HandleErr[0]))


/* --- Retry の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Middleware_t call_sites_Retry[] = {
    { STATE_Middleware_Error, EVENT_Middleware_RETRY },
};
#define CALL_SITES_Retry_COUNT \
    (sizeof(call_sites_Retry) / sizeof(call_sites_Retry[0]))


/**
 * @brief  ロール関数: 接続処理
 * @note   接続処理
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Middleware_Idle -[EVENT_Middleware_CONNECT]-> STATE_Middleware_Connecting
 */
int RoleFunc_Middleware_Connect(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Middleware_t from_state = STATE_Middleware_MAX;
    EVENT_Middleware_t event = EVENT_Middleware_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_Connect, (uint16_t)CALL_SITES_Connect_COUNT);

    /* ===== ctx->data へのローカルポインタ ===== */
    uint32_t *const counter = &ctx->data.counter;  /* 汎用カウンタ */
    uint8_t *const error_code = &ctx->data.error_code;  /* エラーコード */
    uint8_t *const retry_count = &ctx->data.retry_count;  /* リトライ回数 */
    bool *const rx_ready = &ctx->data.rx_ready;  /* RX 準備完了 */
    uint8_t *const rx_data = &ctx->data.rx_data;  /* RX 受信データ */
    volatile uint32_t *const g_system_tick = &ctx->data.g_system_tick;  /* タイマ基準変数 [1ms] */
    uint8_t *const g_tick_10ms = &ctx->data.g_tick_10ms;  /* 派生タイマ変数（10ms） [10ms] */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Middleware_Connect]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Middleware_Connect]] */

    return ret;
}

/**
 * @brief  ロール関数: エラー処理
 * @note   エラー処理
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Middleware_Connecting -[EVENT_Middleware_CONNECTED]-> STATE_Middleware_Error
 *         - [pre_action]  STATE_Middleware_Connecting -[EVENT_Middleware_ERROR]-> STATE_Middleware_Error
 *         - [pre_action]  STATE_Middleware_Connected  -[EVENT_Middleware_ERROR]-> STATE_Middleware_Error
 */
int RoleFunc_Middleware_HandleErr(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Middleware_t from_state = STATE_Middleware_MAX;
    EVENT_Middleware_t event = EVENT_Middleware_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_HandleErr, (uint16_t)CALL_SITES_HandleErr_COUNT);

    /* ===== ctx->data へのローカルポインタ ===== */
    uint32_t *const counter = &ctx->data.counter;  /* 汎用カウンタ */
    uint8_t *const error_code = &ctx->data.error_code;  /* エラーコード */
    uint8_t *const retry_count = &ctx->data.retry_count;  /* リトライ回数 */
    bool *const rx_ready = &ctx->data.rx_ready;  /* RX 準備完了 */
    uint8_t *const rx_data = &ctx->data.rx_data;  /* RX 受信データ */
    volatile uint32_t *const g_system_tick = &ctx->data.g_system_tick;  /* タイマ基準変数 [1ms] */
    uint8_t *const g_tick_10ms = &ctx->data.g_tick_10ms;  /* 派生タイマ変数（10ms） [10ms] */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Middleware_HandleErr]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Middleware_HandleErr]] */

    return ret;
}

/**
 * @brief  ロール関数: 再試行処理
 * @note   再試行処理
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Middleware_Error -[EVENT_Middleware_RETRY]-> STATE_Middleware_Idle
 */
int RoleFunc_Middleware_Retry(
    const TransitionContext_Middleware_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Middleware_t from_state = STATE_Middleware_MAX;
    EVENT_Middleware_t event = EVENT_Middleware_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_Retry, (uint16_t)CALL_SITES_Retry_COUNT);

    /* ===== ctx->data へのローカルポインタ ===== */
    uint32_t *const counter = &ctx->data.counter;  /* 汎用カウンタ */
    uint8_t *const error_code = &ctx->data.error_code;  /* エラーコード */
    uint8_t *const retry_count = &ctx->data.retry_count;  /* リトライ回数 */
    bool *const rx_ready = &ctx->data.rx_ready;  /* RX 準備完了 */
    uint8_t *const rx_data = &ctx->data.rx_data;  /* RX 受信データ */
    volatile uint32_t *const g_system_tick = &ctx->data.g_system_tick;  /* タイマ基準変数 [1ms] */
    uint8_t *const g_tick_10ms = &ctx->data.g_tick_10ms;  /* 派生タイマ変数（10ms） [10ms] */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Middleware_Retry]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Middleware_Retry]] */

    return ret;
}



/* ============================================================== */
/*  Transition ID 変換（ファイル末尾）                            */
/*  ロール関数ごとの call_sites テーブルを線形探索し、             */
/*  一致したエントリのインデックスを返す。                        */
/*  一致なし / transition==NULL の場合は TRANSITION_ID_NONE を    */
/*  返す。                                                        */
/* ============================================================== */
/**
 * @brief  transition 情報を一意な ID に変換する
 * @param  transition  遷移コンテキスト（NULL 可）
 * @param  table       呼び出し元テーブル（NULL 可）
 * @param  table_size  テーブルの要素数
 * @return テーブル内のインデックス（一致なしは TRANSITION_ID_NONE）
 */
static uint16_t Transition_GetId(
    const TransitionContext_Middleware_t *transition,
    const RoleFuncCallSiteEntry_Middleware_t *table,
    uint16_t table_size)
{
    uint16_t i;

    if (transition == NULL || table == NULL) {
        return TRANSITION_ID_NONE;
    }

    for (i = 0; i < table_size; i++) {
        if (table[i].from_state == transition->from_state &&
            table[i].event      == transition->event) {
            return i;
        }
    }
    return TRANSITION_ID_NONE;
}


/* ============================================================== */
/*  ユーザー追加領域                                              */
/*  ここに追加したコードは再生成時も保持されます                  */
/* ============================================================== */
/* [[STABLE_USER_CODE_TAIL_START]] */
/* ユーザー追加コードをここに記述（ヘルパー関数など） */

/* [[STABLE_USER_CODE_TAIL_END]] */
