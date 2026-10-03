# statable_gui/new_project_templates.py
"""Template definitions for the New Project Wizard."""

from __future__ import annotations

# Common events used across all layers
COMMON_EVENTS = [
    {"name": "EV_INIT",    "delivery": "queue",  "kind": "signal", "description": "Initialization request"},
    {"name": "EV_START",   "delivery": "direct", "kind": "signal", "description": "Start request"},
    {"name": "EV_STOP",    "delivery": "direct", "kind": "signal", "description": "Stop request"},
    {"name": "EV_ERROR",   "delivery": "queue",  "kind": "signal", "description": "Error notification"},
    {"name": "EV_TIMEOUT", "delivery": "queue",  "kind": "time",   "description": "Timer expiry"},
]

# Global interrupts (shared across layers)
INTERRUPTS = [
    {"name": "ISR_TIMER0",   "description": "System tick timer"},
    {"name": "ISR_UART_RX",  "description": "UART receive complete"},
    {"name": "ISR_UART_TX",  "description": "UART transmit complete"},
    {"name": "ISR_GPIO",     "description": "GPIO edge detection"},
    {"name": "ISR_ADC",      "description": "ADC conversion complete"},
]

# Global variables (shared)
GLOBAL_VARIABLES = [
    {"name": "g_counter",     "type": "uint32_t", "description": "Loop counter"},
    {"name": "g_error_code",  "type": "int32_t",  "description": "Last error code"},
    {"name": "g_last_event",  "type": "uint16_t", "description": "Last processed event ID"},
    {"name": "g_timeout_ms",  "type": "uint32_t", "description": "Timeout in milliseconds"},
    {"name": "g_debug_level", "type": "uint8_t",  "description": "Debug verbosity level"},
]

# Event flags (shared)
EVENT_FLAGS = [
    {"name": "f_init_done", "description": "Initialization complete"},
    {"name": "f_error",     "description": "Error state active"},
    {"name": "f_ready",     "description": "Ready for operation"},
    {"name": "f_busy",      "description": "Operation in progress"},
    {"name": "f_timeout",   "description": "Timeout occurred"},
]

# Event queues (one per layer + 2 shared)
EVENT_QUEUES = [
    {"name": "q_driver",      "size": 16, "description": "Driver layer event queue"},
    {"name": "q_middleware",  "size": 16, "description": "Middleware layer event queue"},
    {"name": "q_application", "size": 16, "description": "Application layer event queue"},
    {"name": "q_system",      "size": 32, "description": "System-wide event queue"},
    {"name": "q_debug",       "size": 8,  "description": "Debug message queue"},
]


# Layer templates
LAYERS_3LAYER = [
    {
        "name": "Driver",
        "priority": 1,
        "description": "Hardware abstraction layer",
        "states": [
            {"name": "Driver_Init",    "type": "initial", "description": "Hardware initialization"},
            {"name": "Driver_Idle",    "type": "normal",  "description": "Waiting for commands"},
            {"name": "Driver_Active",  "type": "normal",  "description": "Hardware active"},
            {"name": "Driver_Error",   "type": "normal",  "description": "Hardware error"},
            {"name": "Driver_Recover", "type": "normal",  "description": "Recovery in progress"},
        ],
        "role_functions": [
            {"name": "Driver_HwInit",      "description": "Initialize hardware"},
            {"name": "Driver_Start",       "description": "Start hardware operation"},
            {"name": "Driver_Stop",        "description": "Stop hardware operation"},
            {"name": "Driver_HandleError", "description": "Handle hardware error"},
            {"name": "Driver_Cleanup",     "description": "Cleanup resources"},
        ],
    },
    {
        "name": "Middleware",
        "priority": 3,
        "description": "Business logic layer",
        "states": [
            {"name": "Middleware_Init",      "type": "initial", "description": "Middleware initialization"},
            {"name": "Middleware_Standby",   "type": "normal",  "description": "Waiting"},
            {"name": "Middleware_Processing","type": "normal",  "description": "Processing data"},
            {"name": "Middleware_Waiting",   "type": "normal",  "description": "Waiting for response"},
            {"name": "Middleware_Error",     "type": "normal",  "description": "Middleware error"},
        ],
        "role_functions": [
            {"name": "Middleware_Init",      "description": "Initialize middleware"},
            {"name": "Middleware_Process",   "description": "Process request"},
            {"name": "Middleware_Commit",    "description": "Commit result"},
            {"name": "Middleware_Rollback",  "description": "Rollback on error"},
            {"name": "Middleware_Cleanup",   "description": "Cleanup resources"},
        ],
    },
    {
        "name": "Application",
        "priority": 5,
        "description": "User-facing application layer",
        "states": [
            {"name": "Application_Boot",     "type": "initial", "description": "Boot sequence"},
            {"name": "Application_Ready",    "type": "normal",  "description": "Ready for user input"},
            {"name": "Application_Running",  "type": "normal",  "description": "Main operation"},
            {"name": "Application_Paused",   "type": "normal",  "description": "Paused state"},
            {"name": "Application_Shutdown", "type": "normal",  "description": "Shutdown sequence"},
        ],
        "role_functions": [
            {"name": "Application_Init",     "description": "Initialize application"},
            {"name": "Application_Start",    "description": "Start main operation"},
            {"name": "Application_Pause",    "description": "Pause operation"},
            {"name": "Application_Resume",   "description": "Resume operation"},
            {"name": "Application_Shutdown", "description": "Shutdown application"},
        ],
    },
]


TEMPLATES = {
    "blank": {
        "id": "blank",
        "name": "Empty Project",
        "description": "One empty Application layer (existing behavior)",
        "layers": [],
    },
    "basic": {
        "id": "basic",
        "name": "Basic (Single Layer)",
        "description": "Application layer with 5 states + 5 events + 5 role functions",
        "layers": [LAYERS_3LAYER[2]],  # Application only
    },
    "three_layer": {
        "id": "three_layer",
        "name": "3-Layer (Driver / Middleware / Application) [Recommended]",
        "description": "Full 3-layer structure with all placeholders",
        "layers": LAYERS_3LAYER,
    },
}