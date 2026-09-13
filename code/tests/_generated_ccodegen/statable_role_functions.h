/**
 * @file    statable_role_functions.h
 * @brief   ロール関数宣言
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 12:37:52
 */

#ifndef STATABLE_ROLE_FUNCTIONS_H
#define STATABLE_ROLE_FUNCTIONS_H

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types.h"

/*==============================================================*/
 *  ロール関数宣言
/*==============================================================*/

/**
 * @brief  ロール関数: PowerOn
 * @note   電源ON処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_PowerOn(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: StartOk
 * @note   開始条件チェック
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_StartOk(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: Start
 * @note   開始処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Start(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: Stop
 * @note   停止処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Stop(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: HandleError
 * @note   エラー処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_HandleError(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: ProcessData
 * @note   データ処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_ProcessData(
    const TransitionContext_t *transition,
    SystemContext_t *ctx
);



#endif /* STATABLE_ROLE_FUNCTIONS_H */