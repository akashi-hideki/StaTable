/**
 * @file    statable_role_functions.c
 * @brief   ロール関数実装
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


/**
 * @brief  ロール関数: センサ初期化
 * @note   センサ初期化
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Application_SensorInit(
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
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリ電圧 [mV] */
    uint8_t *const payload = ctx->data.payload;  /* 受信データバッファ [bytes] */
    SystemStatus_t *const system_status = &ctx->data.system_status;  /* システムステータス */
    volatile uint32_t *const g_system_tick = &ctx->data.g_system_tick;  /* タイマ基準変数 [1ms] */
    uint8_t *const g_tick_10ms = &ctx->data.g_tick_10ms;  /* 派生タイマ変数（10ms） [10ms] */
    uint8_t *const g_tick_100ms = &ctx->data.g_tick_100ms;  /* 派生タイマ変数（100ms） [100ms] */
    uint16_t *const g_tick_1s = &ctx->data.g_tick_1s;  /* 派生タイマ変数（1s） [1s] */
    volatile uint32_t *const g_high_speed_tick = &ctx->data.g_high_speed_tick;  /* タイマ基準変数 [100us] */
    uint16_t *const g_hs_1ms = &ctx->data.g_hs_1ms;  /* 派生タイマ変数（1ms） [1ms] */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Application_SensorInit]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Application_SensorInit]] */

    return ret;
}

/**
 * @brief  ロール関数: エラーログ出力
 * @note   エラーログ出力
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Application_ErrorLog(
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
    uint16_t *const battery_voltage = &ctx->data.battery_voltage;  /* バッテリ電圧 [mV] */
    uint8_t *const payload = ctx->data.payload;  /* 受信データバッファ [bytes] */
    SystemStatus_t *const system_status = &ctx->data.system_status;  /* システムステータス */
    volatile uint32_t *const g_system_tick = &ctx->data.g_system_tick;  /* タイマ基準変数 [1ms] */
    uint8_t *const g_tick_10ms = &ctx->data.g_tick_10ms;  /* 派生タイマ変数（10ms） [10ms] */
    uint8_t *const g_tick_100ms = &ctx->data.g_tick_100ms;  /* 派生タイマ変数（100ms） [100ms] */
    uint16_t *const g_tick_1s = &ctx->data.g_tick_1s;  /* 派生タイマ変数（1s） [1s] */
    volatile uint32_t *const g_high_speed_tick = &ctx->data.g_high_speed_tick;  /* タイマ基準変数 [100us] */
    uint16_t *const g_hs_1ms = &ctx->data.g_hs_1ms;  /* 派生タイマ変数（1ms） [1ms] */

    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Application_ErrorLog]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Application_ErrorLog]] */

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
