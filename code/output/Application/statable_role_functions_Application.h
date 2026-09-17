/**
 * @file    statable_role_functions_Application.h
 * @brief   ロール関数宣言
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-16 22:39:54
 */

#ifndef STATABLE_ROLE_FUNCTIONS_H_APPLICATION
#define STATABLE_ROLE_FUNCTIONS_H_APPLICATION

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types_Application.h"

/*==============================================================*/
 *  ロール関数宣言
/*==============================================================*/

/**
 * @brief  ロール関数: アプリ起動
 * @note   アプリ起動
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Application_Boot(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: アプリ開始
 * @note   アプリ開始
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Application_Start(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: 一時停止処理
 * @note   一時停止処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Application_Pause(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: 再開処理
 * @note   再開処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Application_Resume(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: 周期処理（ISR用）
 * @note   周期処理（ISR用）
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Application_HandleTick(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: RX処理（ISR用）
 * @note   RX処理（ISR用）
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Application_HandleRx(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: エラー処理（ISR用）
 * @note   エラー処理（ISR用）
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Application_HandleError(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: ドライバ初期化
 * @note   ドライバ初期化
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Driver_Init(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: エラーログ
 * @note   エラーログ
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Driver_LogError(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: リセット処理
 * @note   リセット処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Driver_Reset(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: RX確認（ISR用）
 * @note   RX確認処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Driver_CheckRx(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: 接続処理
 * @note   接続処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Middleware_Connect(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: エラー処理
 * @note   エラー処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Middleware_HandleErr(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: 再試行処理
 * @note   再試行処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Middleware_Retry(
    const TransitionContext_Application_t *transition,
    SystemContext_t *ctx
);



#endif /* STATABLE_ROLE_FUNCTIONS_H_APPLICATION */