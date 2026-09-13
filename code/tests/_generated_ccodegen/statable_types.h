/**
 * @file    statable_types.h
 * @brief   状態遷移システムの型定義
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 12:37:52
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

/* 状態定義 */
typedef enum {
    STATE_INIT = 0,    /* 初期状態 Type: INITIAL */
    STATE_IDLE = 1,    /* アイドル状態 */
    STATE_RUNNING = 2,    /* 実行状態 */
    STATE_ERROR = 3,    /* エラー状態 */
    STATE_MAX           /* 要素数（システム用） */
} STATE_t;


/* イベント定義 */
typedef enum {
    EVENT_NONE = 0,    /* 完了遷移 */
    EVENT_POWER_ON = 1,    /* 電源ONイベント Title: イベント: POWER_ON */
    EVENT_START = 2,    /* 開始イベント Title: イベント: START */
    EVENT_STOP = 3,    /* 停止イベント Title: イベント: STOP */
    EVENT_ERROR_DETECTED = 4,    /* エラー検出イベント Title: イベント: ERROR_DETECTED */
    EVENT_MAX           /* 要素数（システム用） */
} EVENT_t;


/* イベントフラグ定義 */
typedef enum {
    FLAG_EVT_POWER_ON_REQ = 0,    /* 電源ON要求 Title: フラグ: EVT_POWER_ON_REQ */
    FLAG_EVT_START_REQ = 1,    /* 開始要求 Title: フラグ: EVT_START_REQ */
    FLAG_EVT_STOP_REQ = 2,    /* 停止要求 Title: フラグ: EVT_STOP_REQ */
    FLAG_EVT_ERROR_FLAG = 3,    /* エラーフラグ Title: フラグ: EVT_ERROR_FLAG */
    FLAG_MAX           /* 要素数（システム用） */
} FLAG_t;


/*==============================================================*/
 *  ユーザー定義型
/*==============================================================*/

/* システム状態管理構造体 */
/* Title: 型: SystemStatus */
typedef struct {
    /* 電源ON状態 */
    /* Title: power_on:1 */
    bool power_on : 1;
    /* 初期化完了フラグ */
    /* Title: initialized:1 */
    bool initialized : 1;
    /* エラーコード */
    /* Title: メンバ: error_code */
    uint8_t error_code;
    /* 動作モード */
    /* Title: メンバ: mode */
    uint8_t mode;
} SystemStatus_t;

/* センサーデータ構造体 */
/* Title: 型: SensorData */
typedef struct {
    /* 温度値 */
    /* Title: メンバ: temperature */
    int16_t temperature;
    /* 湿度値 */
    /* Title: メンバ: humidity */
    uint8_t humidity;
    /* 気圧値 */
    /* Title: メンバ: pressure */
    uint16_t pressure;
} SensorData_t;

/*==============================================================*/
 *  システム構造体
/*==============================================================*/

/* グローバル変数構造体 */
/* システム全体で共有する変数を管理 */
typedef struct {
    /* === Power === */
    /* バッテリー電圧 [mV] */
    uint16_t battery_voltage;

    /* === Timer === */
    /* システムタイマ [ms] */
    uint32_t system_tick;

    /* === Sensor === */
    /* 温度センサ値 [0.1℃] */
    int16_t temperature;

    /* === Data === */
    /* データバッファ */
    uint8_t data_buffer[64];
} SystemData_t;

/* イベントフラグ構造体 */
/* イベント発生を示すフラグを管理 */
typedef struct {
    /* === System === */
    /* 電源ON要求 */
    uint8_t EVT_POWER_ON_REQ;
    /* 開始要求 */
    uint8_t EVT_START_REQ;
    /* 停止要求 */
    uint8_t EVT_STOP_REQ;

    /* === Error === */
    /* エラーフラグ */
    uint8_t EVT_ERROR_FLAG;
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
#define DATA_SYSTEM_TICK(ctx)    ((ctx)->data.SYSTEM_TICK)
#define DATA_TEMPERATURE(ctx)    ((ctx)->data.TEMPERATURE)
#define DATA_DATA_BUFFER(ctx)    ((ctx)->data.DATA_BUFFER)
#define FLAG_EVT_POWER_ON_REQ(ctx)   ((ctx)->flags.EVT_POWER_ON_REQ)
#define FLAG_EVT_START_REQ(ctx)   ((ctx)->flags.EVT_START_REQ)
#define FLAG_EVT_STOP_REQ(ctx)   ((ctx)->flags.EVT_STOP_REQ)
#define FLAG_EVT_ERROR_FLAG(ctx)   ((ctx)->flags.EVT_ERROR_FLAG)

#endif /* STATABLE_TYPES_H */