/**
 * @file    statable_types.h
 * @brief   状態遷移システムの型定義
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 21:33:04
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
    STATE_Application_Idle = 0,    /* 初期状態 */
    STATE_Application_Active = 1,    /* 動作中 */
    STATE_Application_Error = 2,    /* エラー状態 */
    STATE_Application_Halt = 3,    /* 停止状態 Type: FINAL */
    STATE_Application_MAX           /* 要素数（システム用） */
} STATE_Application_t;


/* Application層のイベント定義 */
typedef enum {
    EVENT_Application_NONE = 0,    /* 完了遷移 */
    EVENT_Application_START = 1,    /* 起動要求 Title: 起動要求 */
    EVENT_Application_STOP = 2,    /* 停止要求 Title: 停止要求 */
    EVENT_Application_ERROR = 3,    /* エラー通知 Title: エラー通知 */
    EVENT_Application_TIMER0_OVERFLOW = 4,    /* 1msタイマ満了 Title: タイマ満了 */
    EVENT_Application_NONE = 5,    /* 完了遷移 Title: 完了遷移 */
    EVENT_Application_MAX           /* 要素数（システム用） */
} EVENT_Application_t;


/* イベントフラグ定義 */
typedef enum {
    FLAG_EVT_START_REQ = 0,    /* 起動要求 Title: 起動要求フラグ */
    FLAG_EVT_MODE = 1,    /* モード指示 Title: モード指示フラグ */
    FLAG_MAX           /* 要素数（システム用） */
} FLAG_t;


/*==============================================================*/
 *  ユーザー定義型
/*==============================================================*/

/* システムステータス構造体 */
/* Title: システムステータス */
typedef struct {
    /* 電源ONフラグ */
    /* Title: 電源ON */
    uint8_t power_on : 1;
    /* モード */
    /* Title: モード */
    uint8_t mode : 3;
    /* ステータス */
    /* Title: ステータス */
    uint8_t status : 4;
} SystemStatusT_t;

/* データパケット構造体 */
/* Title: データパケット */
typedef struct {
    /* データ配列 */
    /* Title: データ配列 */
    uint8_t data[64];
    /* データ長 */
    /* Title: データ長 */
    uint16_t length;
} DataPacketT_t;

/*==============================================================*/
 *  システム構造体
/*==============================================================*/

/* グローバル変数構造体 */
/* システム全体で共有する変数を管理 */
typedef struct {
    /* === Power === */
    /* バッテリ電圧 [mV] */
    uint16_t battery_voltage;

    /* === Communication === */
    /* 受信データバッファ [bytes] */
    uint8_t payload[64];

    /* === System === */
    /* システムステータス */
    SystemStatus_t system_status;

    /* === Timer === */
    /* タイマ基準変数 [1ms] */
    volatile uint32_t g_system_tick;
    /* 派生タイマ変数（10ms） [10ms] */
    uint8_t g_tick_10ms;
    /* 派生タイマ変数（100ms） [100ms] */
    uint8_t g_tick_100ms;
    /* 派生タイマ変数（1s） [1s] */
    uint16_t g_tick_1s;
    /* タイマ基準変数 [100us] */
    volatile uint32_t g_high_speed_tick;
    /* 派生タイマ変数（1ms） [1ms] */
    uint16_t g_hs_1ms;
} SystemData_t;

/* イベントフラグ構造体 */
/* イベント発生を示すフラグを管理 */
typedef struct {
    /* === SystemEvents === */
    /* 起動要求 */
    uint8_t EVT_START_REQ;
    /* モード指示 */
    uint8_t EVT_MODE;
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

#define DATA_BATTERY_VOLTAGE(ctx)    ((ctx)->data.BATTERY_VOLTAGE)
#define DATA_PAYLOAD(ctx)    ((ctx)->data.PAYLOAD)
#define DATA_SYSTEM_STATUS(ctx)    ((ctx)->data.SYSTEM_STATUS)
#define DATA_G_SYSTEM_TICK(ctx)    ((ctx)->data.G_SYSTEM_TICK)
#define DATA_G_TICK_10MS(ctx)    ((ctx)->data.G_TICK_10MS)
#define DATA_G_TICK_100MS(ctx)    ((ctx)->data.G_TICK_100MS)
#define DATA_G_TICK_1S(ctx)    ((ctx)->data.G_TICK_1S)
#define DATA_G_HIGH_SPEED_TICK(ctx)    ((ctx)->data.G_HIGH_SPEED_TICK)
#define DATA_G_HS_1MS(ctx)    ((ctx)->data.G_HS_1MS)
#define FLAG_EVT_START_REQ(ctx)   ((ctx)->flags.EVT_START_REQ)
#define FLAG_EVT_MODE(ctx)   ((ctx)->flags.EVT_MODE)

#endif /* STATABLE_TYPES_H */