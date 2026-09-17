/**
 * @file    statable_types_Middleware.h
 * @brief   層固有の型定義（enum）
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-16 22:39:54
 */

#ifndef STATABLE_TYPES_H_MIDDLEWARE
#define STATABLE_TYPES_H_MIDDLEWARE

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types_common.h"

/*==============================================================*/
 *  型定義
/*==============================================================*/

/* Middleware層の状態定義 */
typedef enum {
    STATE_Middleware_Idle = 0,    /* 待機 Type: INITIAL */
    STATE_Middleware_Connecting = 1,    /* 接続中 */
    STATE_Middleware_Connected = 2,    /* 接続済 */
    STATE_Middleware_Error = 3,    /* エラー */
    STATE_Middleware_MAX           /* 要素数（システム用） */
} STATE_Middleware_t;


/* Middleware層のイベント定義 */
typedef enum {
    EVENT_Middleware_NONE = 0,    /* 完了遷移 */
    EVENT_Middleware_CONNECT = 1,    /* 接続要求 Title: 接続 */
    EVENT_Middleware_CONNECTED = 2,    /* 接続完了 Title: 接続完了 */
    EVENT_Middleware_ERROR = 3,    /* エラー通知 Title: エラー */
    EVENT_Middleware_RETRY = 4,    /* 再試行 Title: 再試行 */
    EVENT_Middleware_MAX           /* 要素数（システム用） */
} EVENT_Middleware_t;


/* イベントフラグ定義 */
typedef enum {
    FLAG_EVT_INIT_DONE = 0,    /* 初期化完了 Title: 初期化完了 */
    FLAG_EVT_ERROR = 1,    /* エラー発生 Title: エラー */
    FLAG_MAX           /* 要素数（システム用） */
} FLAG_t;


#endif /* STATABLE_TYPES_H_MIDDLEWARE */