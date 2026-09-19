/**
 * @file    statable_types.h
 * @brief   状態遷移システムの型定義
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-15 19:56:53
 */

#ifndef STATABLE_TYPES_H
#define STATABLE_TYPES_H

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include <stdint.h>
#include <stdbool.h>
#include <string.h>

/*==============================================================*/
 *  型定義
/*==============================================================*/

/* Application層の状態定義 */
typedef enum {
    STATE_Application_Boot = 0,    /* 起動 Type: INITIAL */
    STATE_Application_Init = 1,    /* 初期化 */
    STATE_Application_Running = 2,    /* 実行中 */
    STATE_Application_Paused = 3,    /* 一時停止 */
    STATE_Application_Stopped = 4,    /* 停止 Type: FINAL */
    STATE_Application_MAX           /* 要素数（システム用） */
} STATE_Application_t;


/* Application層のイベント定義 */
typedef enum {
    EVENT_Application_NONE = 0,    /* 完了遷移 */
    EVENT_Application_BOOT = 1,    /* 起動 Title: 起動 */
    EVENT_Application_START = 2,    /* 開始 Title: 開始 */
    EVENT_Application_PAUSE = 3,    /* 一時停止 Title: 一時停止 */
    EVENT_Application_RESUME = 4,    /* 再開 Title: 再開 */
    EVENT_Application_STOP = 5,    /* 停止 Title: 停止 */
    EVENT_Application_MAX           /* 要素数（システム用） */
} EVENT_Application_t;


/* イベントフラグ定義 */
typedef enum {
    FLAG_EVT_INIT_DONE = 0,    /* 初期化完了 Title: 初期化完了 */
    FLAG_EVT_ERROR = 1,    /* エラー発生 Title: エラー */
    FLAG_MAX           /* 要素数（システム用） */
} FLAG_t;


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

/*==============================================================*/
 *  変数アクセスマクロ
/*==============================================================*/

#define DATA_COUNTER(ctx)    ((ctx)->data.COUNTER)
#define DATA_ERROR_CODE(ctx)    ((ctx)->data.ERROR_CODE)
#define DATA_RETRY_COUNT(ctx)    ((ctx)->data.RETRY_COUNT)
#define DATA_RX_READY(ctx)    ((ctx)->data.RX_READY)
#define DATA_RX_DATA(ctx)    ((ctx)->data.RX_DATA)
#define DATA_G_SYSTEM_TICK(ctx)    ((ctx)->data.G_SYSTEM_TICK)
#define DATA_G_TICK_10MS(ctx)    ((ctx)->data.G_TICK_10MS)
#define FLAG_EVT_INIT_DONE(ctx)   ((ctx)->flags.EVT_INIT_DONE)
#define FLAG_EVT_ERROR(ctx)   ((ctx)->flags.EVT_ERROR)

#endif /* STATABLE_TYPES_H */