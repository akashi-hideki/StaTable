/**
 * @file    statable_types_common.h
 * @brief   状態遷移システムの共通型定義
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-15 20:38:05
 */

#ifndef STATABLE_TYPES_COMMON_H
#define STATABLE_TYPES_COMMON_H

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include <stdint.h>
#include <stdbool.h>
#include <string.h>

/*==============================================================*/
 *  型定義
/*==============================================================*/

/*==============================================================*/
 *  システム構造体
/*==============================================================*/

/* グローバル変数構造体 */
/* システム全体で共有する変数を管理 */
typedef struct {
    /* === System === */
    /* 汎用カウンタ */
    uint32_t counter;
    /* エラーコード */
    uint8_t error_code;
    /* リトライ回数 */
    uint8_t retry_count;
    /* RX 準備完了 */
    bool rx_ready;
    /* RX 受信データ */
    uint8_t rx_data;

    /* === Timer === */
    /* タイマ基準変数 [1ms] */
    volatile uint32_t g_system_tick;
    /* 派生タイマ変数（10ms） [10ms] */
    uint8_t g_tick_10ms;
} SystemData_t;

/* イベントフラグ構造体 */
/* イベント発生を示すフラグを管理 */
typedef struct {
    /* === System === */
    /* 初期化完了 */
    uint8_t EVT_INIT_DONE;
    /* エラー発生 */
    uint8_t EVT_ERROR;
} EventFlags_t;

/* システム全体構造体 */
/* グローバル変数とイベントフラグを統合管理 */
typedef struct {
    SystemData_t data;     /* グローバル変数 */
    EventFlags_t flags;    /* イベントフラグ */
    uint16_t pending_event;         /* 保留中のイベント */
    bool pending_event_valid;       /* 保留イベント有効フラグ */
} SystemContext_t;

/* 汎用遷移コンテキスト（層を問わない共通ロール関数用） */
/* 各層の TransitionContext_<Layer>_t と同じレイアウト */
typedef struct {
    uint16_t from_state;   /* 遷移元状態（層の enum 値をキャスト） */
    uint16_t event;        /* 発生イベント（層の enum 値をキャスト） */
} TransitionContext_t;


/* ============================================================== */
/*  保留イベント制御                                              */
/* ============================================================== */

/* イベント発火マクロ */
/* ロール関数内で使用: FIRE_EVENT(ctx, EVENT_XXX_YYY); */
#define FIRE_EVENT(ctx, evt)  do { \
    (ctx)->pending_event = (uint16_t)(evt); \
    (ctx)->pending_event_valid = true; \
} while(0)

/* 保留イベント連続処理の上限 */
/* 無限ループ防止用。ビルド時に -D で上書き可能 */
#ifndef MAX_CONSECUTIVE_PENDING_EVENTS
#define MAX_CONSECUTIVE_PENDING_EVENTS 16
#endif


/*==============================================================*/
 *  変数アクセスマクロ
/*==============================================================*/

#define DATA_COUNTER(ctx)    ((ctx)->data.counter)
#define DATA_ERROR_CODE(ctx)    ((ctx)->data.error_code)
#define DATA_RETRY_COUNT(ctx)    ((ctx)->data.retry_count)
#define DATA_RX_READY(ctx)    ((ctx)->data.rx_ready)
#define DATA_RX_DATA(ctx)    ((ctx)->data.rx_data)
#define DATA_G_SYSTEM_TICK(ctx)    ((ctx)->data.g_system_tick)
#define DATA_G_TICK_10MS(ctx)    ((ctx)->data.g_tick_10ms)
#define FLAG_EVT_INIT_DONE(ctx)   ((ctx)->flags.EVT_INIT_DONE)
#define FLAG_EVT_ERROR(ctx)   ((ctx)->flags.EVT_ERROR)

#endif /* STATABLE_TYPES_COMMON_H */