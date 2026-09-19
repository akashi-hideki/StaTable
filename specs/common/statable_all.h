/**
 * @file    statable_all.h
 * @brief   StaTable 生成コード一括インクルード
 *
 * @note    このファイルは以下のファイルからのみインクルード可能:
 *          - ユーザーの main.c
 *          - プロジェクトの .c ファイル
 *          ※ 生成コードの .h ファイルからはインクルード禁止
 */

#ifndef STATABLE_ALL_H
#define STATABLE_ALL_H

/* ---- 共通ヘッダ ---- */
#include "statable_types.h"

/* ---- 層ごとのヘッダ ---- */
#include "statable_transitions.h"
#include "statable_role_functions.h"

/* ---- プロジェクトヘッダ ---- */
#include "osal.h"

/* ---- スーパーループ変数（extern） ---- */
extern SystemContext_t g_ctx;
extern STATE_Application_t g_Application_state;

/* ---- スーパーループ関数 ---- */
void MyProject_Init(void);
void MyProject_Run(void);

/* ---- ユーザー追加インクルード ---- */
/* [[STABLE_USER_INCLUDES_START]] */
/* [[STABLE_USER_INCLUDES_END]] */

#endif /* STATABLE_ALL_H */