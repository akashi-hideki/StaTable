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
#include "statable_types_common.h"
#include "Driver/statable_types_Driver.h"
#include "Middleware/statable_types_Middleware.h"
#include "Application/statable_types_Application.h"

/* ---- 層ごとのヘッダ ---- */
#include "Driver/statable_transitions_Driver.h"
#include "Driver/statable_role_functions_Driver.h"
#include "Middleware/statable_transitions_Middleware.h"
#include "Middleware/statable_role_functions_Middleware.h"
#include "Application/statable_transitions_Application.h"
#include "Application/statable_role_functions_Application.h"

/* ---- プロジェクトヘッダ ---- */
#include "osal.h"

/* ---- スーパーループ変数（extern） ---- */
extern SystemContext_t g_ctx;
extern STATE_Driver_t g_Driver_state;
extern STATE_Middleware_t g_Middleware_state;
extern STATE_Application_t g_Application_state;

/* ---- スーパーループ関数 ---- */
void IsrNamespaceTest_Init(void);
void IsrNamespaceTest_Run(void);

/* ---- ユーザー追加インクルード ---- */
/* [[STABLE_USER_INCLUDES_START]] */
/* [[STABLE_USER_INCLUDES_END]] */

#endif /* STATABLE_ALL_H */