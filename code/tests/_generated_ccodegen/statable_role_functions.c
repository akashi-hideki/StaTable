/**
 * @file    statable_role_functions.c
 * @brief   ロール関数実装
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 12:37:52
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
    STATE_t from_state;   /* 遷移元状態 */
    EVENT_t event;        /* 発生イベント */
} RoleFuncCallSiteEntry_t;


/* Transition_GetId 前方宣言（本体はファイル末尾） */
static uint16_t Transition_GetId(
    const TransitionContext_t *transition,
    const RoleFuncCallSiteEntry_t *table,
    uint16_t table_size);


/* --- StartOk の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_t call_sites_StartOk[] = {
    { STATE_IDLE, EVENT_START },
};
#define CALL_SITES_StartOk_COUNT \
    (sizeof(call_sites_StartOk) / sizeof(call_sites_StartOk[0]))


/**
 * @brief  ロール関数: PowerOn
 * @note   電源ON処理
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_PowerOn(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_t from_state = STATE_MAX;
    EVENT_t event = EVENT_NONE;
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
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:PowerOn]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:PowerOn]] */

    return ret;
}

/**
 * @brief  ロール関数: StartOk
 * @note   開始条件チェック
 *
 * @note   呼び出し元:
 *         - [condition]  STATE_IDLE -[EVENT_START]-> STATE_RUNNING
 */
int RoleFunc_StartOk(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_t from_state = STATE_MAX;
    EVENT_t event = EVENT_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    /* ===== transition ID（call_sites 内のインデックス） ===== */
    const uint16_t transition_id = Transition_GetId(
        transition, call_sites_StartOk, (uint16_t)CALL_SITES_StartOk_COUNT);

    /* ===== ctx->data へのローカルポインタ ===== */
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:StartOk]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:StartOk]] */

    return ret;
}

/**
 * @brief  ロール関数: Start
 * @note   開始処理
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Start(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_t from_state = STATE_MAX;
    EVENT_t event = EVENT_NONE;
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
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Start]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Start]] */

    return ret;
}

/**
 * @brief  ロール関数: Stop
 * @note   停止処理
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Stop(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_t from_state = STATE_MAX;
    EVENT_t event = EVENT_NONE;
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
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Stop]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Stop]] */

    return ret;
}

/**
 * @brief  ロール関数: HandleError
 * @note   エラー処理
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_HandleError(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_t from_state = STATE_MAX;
    EVENT_t event = EVENT_NONE;
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
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:HandleError]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:HandleError]] */

    return ret;
}

/**
 * @brief  ロール関数: ProcessData
 * @note   データ処理
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_ProcessData(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_t from_state = STATE_MAX;
    EVENT_t event = EVENT_NONE;
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
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:ProcessData]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:ProcessData]] */

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
    const TransitionContext_t *transition,
    const RoleFuncCallSiteEntry_t *table,
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
