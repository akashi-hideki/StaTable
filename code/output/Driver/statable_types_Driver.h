/**
 * @file    statable_types_Driver.h
 * @brief   層固有の型定義（enum）
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-16 22:39:54
 */

#ifndef STATABLE_TYPES_H_DRIVER
#define STATABLE_TYPES_H_DRIVER

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types_common.h"

/*==============================================================*/
 *  型定義
/*==============================================================*/

/* Driver層の状態定義 */
typedef enum {
    STATE_Driver_Idle = 0,    /* 待機 Type: INITIAL */
    STATE_Driver_Initializing = 1,    /* 初期化中 */
    STATE_Driver_Ready = 2,    /* 準備完了 */
    STATE_Driver_Error = 3,    /* エラー */
    STATE_Driver_MAX           /* 要素数（システム用） */
} STATE_Driver_t;


/* Driver層のイベント定義 */
typedef enum {
    EVENT_Driver_NONE = 0,    /* 完了遷移 */
    EVENT_Driver_INIT = 1,    /* 初期化要求 Title: 初期化 */
    EVENT_Driver_READY = 2,    /* 準備完了 Title: 準備完了 */
    EVENT_Driver_FAIL = 3,    /* 失敗通知 Title: 失敗 */
    EVENT_Driver_RESET = 4,    /* リセット Title: リセット */
    EVENT_Driver_MAX           /* 要素数（システム用） */
} EVENT_Driver_t;


/* イベントフラグ定義 */
typedef enum {
    FLAG_EVT_INIT_DONE = 0,    /* 初期化完了 Title: 初期化完了 */
    FLAG_EVT_ERROR = 1,    /* エラー発生 Title: エラー */
    FLAG_MAX           /* 要素数（システム用） */
} FLAG_t;


#endif /* STATABLE_TYPES_H_DRIVER */