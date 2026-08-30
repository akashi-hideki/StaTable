/**
 * @file    statable_role_functions.h
 * @brief   ロール関数宣言
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-08-31 01:30:31
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
 * @param  current_state  現在の状態ポインタ
 * @param  ctx  システムコンテキストポインタ
 * @return なし
 */
void RoleFunc_PowerOn(
    STATE_t *current_state,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: StartOk
 * @note   開始条件チェック
 * @param  current_state  現在の状態ポインタ
 * @param  ctx  システムコンテキストポインタ
 * @return 条件成立の場合true
 */
bool RoleFunc_StartOk(
    STATE_t *current_state,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: Start
 * @note   開始処理
 * @param  current_state  現在の状態ポインタ
 * @param  ctx  システムコンテキストポインタ
 * @return なし
 */
void RoleFunc_Start(
    STATE_t *current_state,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: Stop
 * @note   停止処理
 * @param  current_state  現在の状態ポインタ
 * @param  ctx  システムコンテキストポインタ
 * @return なし
 */
void RoleFunc_Stop(
    STATE_t *current_state,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: HandleError
 * @note   エラー処理
 * @param  current_state  現在の状態ポインタ
 * @param  ctx  システムコンテキストポインタ
 * @return なし
 */
void RoleFunc_HandleError(
    STATE_t *current_state,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: ProcessData
 * @note   データ処理
 * @param  current_state  現在の状態ポインタ
 * @param  ctx  システムコンテキストポインタ
 * @param  data  引数1
 * @param  len  引数2
 * @return 実行結果（0: 成功, 0以外: エラー）
 */
int RoleFunc_ProcessData(
    STATE_t *current_state,
    SystemContext_t *ctx,
    uint8_t*data,
    uint16_t len
);


#endif /* STATABLE_ROLE_FUNCTIONS_H */