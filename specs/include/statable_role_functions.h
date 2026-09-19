/**
 * @file    statable_role_functions.h
 * @brief   ロール関数宣言
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 21:33:04
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
 * @brief  ロール関数: センサ初期化
 * @note   センサ初期化
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Application_SensorInit(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: エラーログ出力
 * @note   エラーログ出力
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Application_ErrorLog(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);



#endif /* STATABLE_ROLE_FUNCTIONS_H */