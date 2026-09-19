/**
 * @file    statable_all.h
 * @brief   StaTable generated code super include
 */

#ifndef STATABLE_ALL_H
#define STATABLE_ALL_H

/* ---- Common headers ---- */
#include "statable_types_common.h"
#include "Driver/statable_types_Driver.h"
#include "Middleware/statable_types_Middleware.h"
#include "Application/statable_types_Application.h"

/* ---- Per-layer headers ---- */
#include "Driver/statable_transitions_Driver.h"
#include "Driver/statable_role_functions_Driver.h"
#include "Middleware/statable_transitions_Middleware.h"
#include "Middleware/statable_role_functions_Middleware.h"
#include "Application/statable_transitions_Application.h"
#include "Application/statable_role_functions_Application.h"

/* ---- Project headers ---- */
#include "osal.h"

/* ---- Super loop variables (extern) ---- */
extern SystemContext_t g_ctx;
extern STATE_Driver_t g_Driver_state;
extern STATE_Middleware_t g_Middleware_state;
extern STATE_Application_t g_Application_state;

/* ---- Super loop functions ---- */
void V22FeaturesTest3Layers_Init(void);
void V22FeaturesTest3Layers_Run(void);

/* ---- Interrupt handlers (extern) ---- */
void ISR_TIMER0(void);

/* ---- User-added includes ---- */
/* [[STABLE_USER_INCLUDES_START]] */
/* [[STABLE_USER_INCLUDES_END]] */

#endif /* STATABLE_ALL_H */