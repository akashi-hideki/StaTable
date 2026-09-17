/**
 * @file    statable_types_Application.h
 * @brief   層固有の型定義（enum）
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-16 22:39:54
 */

#ifndef STATABLE_TYPES_H_APPLICATION
#define STATABLE_TYPES_H_APPLICATION

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types_common.h"

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


#endif /* STATABLE_TYPES_H_APPLICATION */