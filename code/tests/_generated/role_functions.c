
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


/* --- StartOk の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Driver_t call_sites_StartOk[] = {
    { STATE_Driver_Idle, EVENT_Driver_START },
};
#define CALL_SITES_StartOk_COUNT \
    (sizeof(call_sites_StartOk) / sizeof(call_sites_StartOk[0]))


/* --- LogStop の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Driver_t call_sites_LogStop[] = {
    { STATE_Driver_Active, EVENT_Driver_STOP },
};
#define CALL_SITES_LogStop_COUNT \
    (sizeof(call_sites_LogStop) / sizeof(call_sites_LogStop[0]))


/* --- LogError の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Driver_t call_sites_LogError[] = {
    { STATE_Driver_Active, EVENT_Driver_ERROR },
};
#define CALL_SITES_LogError_COUNT \
    (sizeof(call_sites_LogError) / sizeof(call_sites_LogError[0]))


/* --- Fallback の呼び出し元テーブル --- */
static const RoleFuncCallSiteEntry_Driver_t call_sites_Fallback[] = {
    { STATE_Driver_Active, EVENT_Driver_ERROR },
};
#define CALL_SITES_Fallback_COUNT \
    (sizeof(call_sites_Fallback) / sizeof(call_sites_Fallback[0]))


/**
 * @brief  ロール関数: StartOk
 * @note   開始条件チェック
 *
 * @note   呼び出し元:
 *         - [condition]  STATE_Driver_Idle -[EVENT_Driver_START]-> STATE_Driver_Running
 */
int RoleFunc_Driver_StartOk(
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
        transition, call_sites_StartOk, (uint16_t)CALL_SITES_StartOk_COUNT);

    /* ===== ctx->data へのローカルポインタ ===== */
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Driver_StartOk]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Driver_StartOk]] */

    return ret;
}

/**
 * @brief  ロール関数: LogStop
 * @note   停止ログ
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Driver_Active -[EVENT_Driver_STOP]-> STATE_Driver_Idle
 */
int RoleFunc_Driver_LogStop(
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
        transition, call_sites_LogStop, (uint16_t)CALL_SITES_LogStop_COUNT);

    /* ===== ctx->data へのローカルポインタ ===== */
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Driver_LogStop]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Driver_LogStop]] */

    return ret;
}

/**
 * @brief  ロール関数: LogError
 * @note   エラーログ
 *
 * @note   呼び出し元:
 *         - [pre_action]  STATE_Driver_Active -[EVENT_Driver_ERROR]-> STATE_Driver_Error
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
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Driver_LogError]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Driver_LogError]] */

    return ret;
}

/**
 * @brief  ロール関数: Fallback
 * @note   フォールバック処理
 *
 * @note   呼び出し元:
 *         - [else_action]  STATE_Driver_Active -[EVENT_Driver_ERROR]-> STATE_Driver_Idle
 */
int RoleFunc_Driver_Fallback(
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
        transition, call_sites_Fallback, (uint16_t)CALL_SITES_Fallback_COUNT);

    /* ===== ctx->data へのローカルポインタ ===== */
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリー電圧 [mV] */
    uint32_t *const system_tick = &ctx->data.system_tick;  /* システムタイマ [ms] */
    int16_t *const temperature = &ctx->data.temperature;  /* 温度センサ値 [0.1℃] */
    uint8_t *const data_buffer = ctx->data.data_buffer;  /* データバッファ */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Driver_Fallback]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Driver_Fallback]] */

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
