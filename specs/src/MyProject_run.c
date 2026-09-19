/**
 * @file    MyProject_run.c
 * @brief   ステートマシン スーパーループ
 *
 * @note    このファイルはユーザーが編集しないこと
 *          ハードウェア初期化等は main.c で行い、本ファイルを呼び出す
 */

#include "statable_all.h"

SystemContext_t g_ctx;

STATE_Application_t g_Application_state;

/**
 * @brief  ステートマシン初期化
 * @note   各層のステートマシンを優先度昇順で初期化
 */
void MyProject_Init(void)
{
    SystemContext_Init(&g_ctx);
    g_Application_state = STATE_Application_Idle;
}

/**
 * @brief  ステートマシン メインループ
 */
void MyProject_Run(void)
{
    while (1) {
                EVENT_Application_t evt = StateMachine_GetNextEvent_Application(&g_ctx);
                if (evt != EVENT_Application_NONE) {
                    g_Application_state = StateMachine_Process_Application(g_Application_state, evt, &g_ctx);
                }
    }
}