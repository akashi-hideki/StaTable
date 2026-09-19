/**
 * @file    statable_all.h
 * @brief   StaTable generated code super include
 */

#ifndef STATABLE_ALL_H
#define STATABLE_ALL_H

/* ---- Common headers ---- */
#include "statable_types_common.h"
#include "Application/statable_types_Application.h"

/* ---- Per-layer headers ---- */
#include "Application/statable_transitions_Application.h"
#include "Application/statable_role_functions_Application.h"

/* ---- Project headers ---- */
#include "osal.h"

/* ---- Super loop variables (extern) ---- */
extern SystemContext_t g_ctx;
extern STATE_Application_t g_Application_state;

/* ---- Super loop functions ---- */
void V22FeaturesTest_Init(void);
void V22FeaturesTest_Run(void);

/* ---- User-added includes ---- */
/* [[STABLE_USER_INCLUDES_START]] */
/* [[STABLE_USER_INCLUDES_END]] */

#endif /* STATABLE_ALL_H */