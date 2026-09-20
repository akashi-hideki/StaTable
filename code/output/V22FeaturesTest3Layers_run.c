/**
 * @file    V22FeaturesTest3Layers_run.c
 * @brief   State machine super loop
 */

#include "statable_all.h"

SystemContext_t g_ctx;

STATE_Driver_t g_Driver_state;
STATE_Middleware_t g_Middleware_state;
STATE_Application_t g_Application_state;

/**
 * @brief  State machine initialization
 */
void V22FeaturesTest3Layers_Init(void)
{
    SystemContext_Init(&g_ctx);
    g_Driver_state = STATE_Driver_Idle;
    g_Middleware_state = STATE_Middleware_Idle;
    g_Application_state = STATE_Application_Boot;
}

/**
 * @brief  State machine main loop
 */
void V22FeaturesTest3Layers_Run(void)
{
    while (1) {
                {
                    EVENT_Driver_t evt = StateMachine_GetNextEvent_Driver(&g_ctx);
                    if (evt != EVENT_Driver_NONE) {
                        g_Driver_state = StateMachine_Process_Driver(g_Driver_state, evt, &g_ctx);
                    }
                }
                {
                    EVENT_Middleware_t evt = StateMachine_GetNextEvent_Middleware(&g_ctx);
                    if (evt != EVENT_Middleware_NONE) {
                        g_Middleware_state = StateMachine_Process_Middleware(g_Middleware_state, evt, &g_ctx);
                    }
                }
                {
                    EVENT_Application_t evt = StateMachine_GetNextEvent_Application(&g_ctx);
                    if (evt != EVENT_Application_NONE) {
                        g_Application_state = StateMachine_Process_Application(g_Application_state, evt, &g_ctx);
                    }
                }
    }
}