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
    STATE_Driver_t from_state;   /* 遷移元状態 */
    EVENT_Driver_t event;        /* 発生イベント */
} RoleFuncCallSiteEntry_Driver_t;


/* Transition_GetId 前方宣言（本体はファイル末尾） */
static uint16_t Transition_GetId(
    const TransitionContext_Driver_t *transition,
    const RoleFuncCallSiteEntry_Driver_t *table,
    uint16_t table_size);


/* --- Init の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Driver_t call_sites_Init[] = {
    { STATE_Driver_Idle, EVENT_Driver_INIT },
};
#define CALL_SITES_Init_COUNT \
    (sizeof(call_sites_Init) / sizeof(call_sites_Init[0]))


/* --- LogError の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Driver_t call_sites_LogError[] = {
    { STATE_Driver_Initializing, EVENT_Driver_READY },
    { STATE_Driver_Initializing, EVENT_Driver_FAIL },
    { STATE_Driver_Ready,        EVENT_Driver_FAIL },
};
#define CALL_SITES_LogError_COUNT \
    (sizeof(call_sites_LogError) / sizeof(call_sites_LogError[0]))


/* --- Reset の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Driver_t call_sites_Reset[] = {
    { STATE_Driver_Error, EVENT_Driver_RESET },
};
#define CALL_SITES_Reset_COUNT \
    (sizeof(call_sites_Reset) / sizeof(call_sites_Reset[0]))


/**
 * @brief  ロール関数: ドライバ初期化
 * @note   ドライバ初期化
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Driver_Idle -[EVENT_Driver_INIT]-> STATE_Driver_Initializing
 */
int RoleFunc_Driver_Init(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Driver_t from_state = STATE_Driver_MAX;
    EVENT_Driver_t event = EVENT_Driver_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_Init, (uint16_t)CALL_SITES_Init_COUNT);

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

    /* [[STABLE_USER_CODE_START:Driver_Init]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Driver_Init]] */

    return ret;
}

/**
 * @brief  ロール関数: エラーログ
 * @note   エラーログ
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Driver_Initializing -[EVENT_Driver_READY]-> STATE_Driver_Error
 *         - [pre_action]  STATE_Driver_Initializing -[EVENT_Driver_FAIL]-> STATE_Driver_Error
 *         - [pre_action]  STATE_Driver_Ready        -[EVENT_Driver_FAIL]-> STATE_Driver_Error
 */
int RoleFunc_Driver_LogError(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Driver_t from_state = STATE_Driver_MAX;
    EVENT_Driver_t event = EVENT_Driver_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_LogError, (uint16_t)CALL_SITES_LogError_COUNT);

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

    /* [[STABLE_USER_CODE_START:Driver_LogError]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Driver_LogError]] */

    return ret;
}

/**
 * @brief  ロール関数: リセット処理
 * @note   リセット処理
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Driver_Error -[EVENT_Driver_RESET]-> STATE_Driver_Idle
 */
int RoleFunc_Driver_Reset(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Driver_t from_state = STATE_Driver_MAX;
    EVENT_Driver_t event = EVENT_Driver_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_Reset, (uint16_t)CALL_SITES_Reset_COUNT);

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

    /* [[STABLE_USER_CODE_START:Driver_Reset]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Driver_Reset]] */

    return ret;
}

/**
 * @brief  ロール関数: RX確認（ISR用）
 * @note   RX確認処理
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Driver_CheckRx(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Driver_t from_state = STATE_Driver_MAX;
    EVENT_Driver_t event = EVENT_Driver_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, NULL, 0);

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

    /* [[STABLE_USER_CODE_START:Driver_CheckRx]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Driver_CheckRx]] */

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
    const TransitionContext_Driver_t *transition,
    const RoleFuncCallSiteEntry_Driver_t *table,
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
