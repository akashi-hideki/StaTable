/* L1 host test: 5 fake variables */
#include <stdint.h>
#include "statable_comm_registry.h"

static uint32_t v_system_tick       = 1000;
static uint16_t v_oven_current_temp = 25;
static uint16_t v_oven_target_temp  = 200;
static uint8_t  v_heater_top_duty   = 50;
static uint8_t  v_error_code        = 0;

const VarEntry_t g_var_registry[] = {
    { &v_system_tick,       4 },
    { &v_oven_current_temp, 2 },
    { &v_oven_target_temp,  2 },
    { &v_heater_top_duty,   1 },
    { &v_error_code,        1 },
};
const uint8_t g_var_count =
    sizeof(g_var_registry) / sizeof(g_var_registry[0]);

const char * const g_var_names[] = {
    "g_system_tick",
    "oven_current_temp",
    "oven_target_temp",
    "heater_top_duty",
    "error_code",
};

uint32_t comm_registry_read(uint8_t id)
{
    if (id >= g_var_count) return 0;
    const VarEntry_t *e = &g_var_registry[id];
    switch (e->size) {
    case 1: return *(const uint8_t  *)e->ptr;
    case 2: return *(const uint16_t *)e->ptr;
    case 4: return *(const uint32_t *)e->ptr;
    default: return 0;
    }
}
