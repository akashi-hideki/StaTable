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
    STATE_Application_t from_state;   /* 遷移元状態 */
    EVENT_Application_t event;        /* 発生イベント */
} RoleFuncCallSiteEntry_Application_t;


/* Transition_GetId 前方宣言（本体はファイル末尾） */
static uint16_t Transition_GetId(
    const TransitionContext_Application_t *transition,
    const RoleFuncCallSiteEntry_Application_t *table,
    uint16_t table_size);


/* --- Boot の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Application_t call_sites_Boot[] = {
    { STATE_Application_Boot, EVENT_Application_BOOT },
};
#define CALL_SITES_Boot_COUNT \
    (sizeof(call_sites_Boot) / sizeof(call_sites_Boot[0]))


/* --- Start の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Application_t call_sites_Start[] = {
    { STATE_Application_Init, EVENT_Application_START },
};
#define CALL_SITES_Start_COUNT \
    (sizeof(call_sites_Start) / sizeof(call_sites_Start[0]))


/* --- Pause の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Application_t call_sites_Pause[] = {
    { STATE_Application_Running, EVENT_Application_STOP },
};
#define CALL_SITES_Pause_COUNT \
    (sizeof(call_sites_Pause) / sizeof(call_sites_Pause[0]))


/* --- Resume の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Application_t call_sites_Resume[] = {
    { STATE_Application_Paused, EVENT_Application_RESUME },
};
#define CALL_SITES_Resume_COUNT \
    (sizeof(call_sites_Resume) / sizeof(call_sites_Resume[0]))


/**
 * @brief  ロール関数: アプリ起動
 * @note   アプリ起動
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Application_Boot -[EVENT_Application_BOOT]-> STATE_Application_Init
 */
int RoleFunc_Application_Boot(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Application_t from_state = STATE_Application_MAX;
    EVENT_Application_t event = EVENT_Application_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_Boot, (uint16_t)CALL_SITES_Boot_COUNT);

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

    /* [[STABLE_USER_CODE_START:Application_Boot]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Application_Boot]] */

    return ret;
}

/**
 * @brief  ロール関数: アプリ開始
 * @note   アプリ開始
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Application_Init -[EVENT_Application_START]-> STATE_Application_Running
 */
int RoleFunc_Application_Start(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Application_t from_state = STATE_Application_MAX;
    EVENT_Application_t event = EVENT_Application_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_Start, (uint16_t)CALL_SITES_Start_COUNT);

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

    /* [[STABLE_USER_CODE_START:Application_Start]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Application_Start]] */

    return ret;
}

/**
 * @brief  ロール関数: 一時停止処理
 * @note   一時停止処理
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Application_Running -[EVENT_Application_STOP]-> STATE_Application_Stopped
 */
int RoleFunc_Application_Pause(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Application_t from_state = STATE_Application_MAX;
    EVENT_Application_t event = EVENT_Application_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_Pause, (uint16_t)CALL_SITES_Pause_COUNT);

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

    /* [[STABLE_USER_CODE_START:Application_Pause]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Application_Pause]] */

    return ret;
}

/**
 * @brief  ロール関数: 再開処理
 * @note   再開処理
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Application_Paused -[EVENT_Application_RESUME]-> STATE_Application_Running
 */
int RoleFunc_Application_Resume(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Application_t from_state = STATE_Application_MAX;
    EVENT_Application_t event = EVENT_Application_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_Resume, (uint16_t)CALL_SITES_Resume_COUNT);

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

    /* [[STABLE_USER_CODE_START:Application_Resume]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Application_Resume]] */

    return ret;
}

/**
 * @brief  ロール関数: 周期処理（ISR用）
 * @note   周期処理（ISR用）
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Application_HandleTick(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Application_t from_state = STATE_Application_MAX;
    EVENT_Application_t event = EVENT_Application_NONE;
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

    /* [[STABLE_USER_CODE_START:Application_HandleTick]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Application_HandleTick]] */

    return ret;
}

/**
 * @brief  ロール関数: RX処理（ISR用）
 * @note   RX処理（ISR用）
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Application_HandleRx(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Application_t from_state = STATE_Application_MAX;
    EVENT_Application_t event = EVENT_Application_NONE;
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

    /* [[STABLE_USER_CODE_START:Application_HandleRx]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Application_HandleRx]] */

    return ret;
}

/**
 * @brief  ロール関数: エラー処理（ISR用）
 * @note   エラー処理（ISR用）
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Application_HandleError(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Application_t from_state = STATE_Application_MAX;
    EVENT_Application_t event = EVENT_Application_NONE;
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

    /* [[STABLE_USER_CODE_START:Application_HandleError]] */
    /* ユーザー実装コードをここに記述 */

    /* [[STABLE_USER_CODE_END:Application_HandleError]] */

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
    const TransitionContext_Application_t *transition,
    const RoleFuncCallSiteEntry_Application_t *table,
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
