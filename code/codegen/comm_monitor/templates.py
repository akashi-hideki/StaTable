"""C コードテンプレート（v3.6.0 / GET 専用 / ASCII のみ）。"""
from string import Template

CONFIG_H = Template("""\
#ifndef STATABLE_COMM_CONFIG_H
#define STATABLE_COMM_CONFIG_H
#define COMM_MONITOR_ENABLED        $enabled
#define COMM_MONITOR_ASCII_BODY_MAX $body_max
#define COMM_MONITOR_RX_RING_SIZE   $rx_ring
#define COMM_MONITOR_TX_RING_SIZE   $tx_ring
#define COMM_MONITOR_IDLE_MS        $idle_ms
#define COMM_MONITOR_ACK_UNIT       $ack_unit
#define COMM_MONITOR_ACK_NAME       $ack_name
#define COMM_MONITOR_VERSION        "$version"
#define COMM_MONITOR_XML_CRC32      0x${crc32}u
#define COMM_MONITOR_VAR_COUNT      ${var_count}u
#endif
""")

REGISTRY_H = Template("""\
#ifndef STATABLE_COMM_REGISTRY_H
#define STATABLE_COMM_REGISTRY_H
#include <stdint.h>
typedef struct { const void *ptr; uint8_t size; } VarEntry_t;
extern const VarEntry_t   g_var_registry[];
extern const uint8_t      g_var_count;
extern const char * const g_var_names[];
uint32_t comm_registry_read(uint8_t id);
#endif
""")

REGISTRY_C = Template("""\
#include "statable_comm_registry.h"
#include "statable_types.h"
const VarEntry_t g_var_registry[] = {
$entries
};
const uint8_t g_var_count =
    sizeof(g_var_registry) / sizeof(g_var_registry[0]);
const char * const g_var_names[] = {
$names
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
""")

MONITOR_H = Template("""\
#ifndef STATABLE_COMM_MONITOR_H
#define STATABLE_COMM_MONITOR_H
#include <stdint.h>
void comm_monitor_init(void);
void comm_monitor_on_rx_byte(uint8_t b);
void comm_monitor_poll(void);
typedef void (*CommTxFn)(uint8_t b);
void comm_monitor_set_tx(CommTxFn fn);
#endif
""")

MONITOR_C = Template("""\
#include "statable_comm_monitor.h"
#include "statable_comm_config.h"
#include "statable_comm_registry.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>

typedef enum { RX_WAIT_STX, RX_BODY, RX_CR } RxState_t;

static RxState_t g_state = RX_WAIT_STX;
static char      g_buf[COMM_MONITOR_ASCII_BODY_MAX];
static uint8_t   g_pos;
static CommTxFn  g_tx;

void comm_monitor_init(void) { g_state = RX_WAIT_STX; g_pos = 0; }
void comm_monitor_set_tx(CommTxFn fn) { g_tx = fn; }

static void tx_put(uint8_t b) { if (g_tx) g_tx(b); }
static void tx_str(const char *s) { while (*s) tx_put((uint8_t)*s++); }

static void respond(const char *text)
{
    tx_put(0x02);
    tx_str(text);
    tx_put(0x0D);
    tx_put(0x03);
}

static void nak(int ret, const char *reason)
{
    char line[80];
    snprintf(line, sizeof(line), "NAK ret=%d reason=%s", ret, reason);
    respond(line);
}

static void handle_ping(void)
{
    char line[96];
    snprintf(line, sizeof(line),
             "ACK ret=0 fw=%s crc=%08lX vars=%u",
             COMM_MONITOR_VERSION,
             (unsigned long)COMM_MONITOR_XML_CRC32,
             (unsigned)g_var_count);
    respond(line);
}

static void handle_list(void)
{
    char line[80];
    snprintf(line, sizeof(line), "ACK ret=0 vars=%u", (unsigned)g_var_count);
    respond(line);
    for (uint8_t i = 0; i < g_var_count; i++) {
        snprintf(line, sizeof(line), "ACK ret=0 id=%u name=%s",
                 i, g_var_names[i]);
        respond(line);
    }
}

static void handle_get(const char *args)
{
    if (!args || !*args) { nak(7, "args"); return; }

    int compact = 0;
    char tmp[COMM_MONITOR_ASCII_BODY_MAX];
    strncpy(tmp, args, sizeof(tmp) - 1);
    tmp[sizeof(tmp) - 1] = 0;
    size_t n = strlen(tmp);
    if (n > 7 && strcmp(tmp + n - 7, "compact") == 0) {
        compact = 1;
        tmp[n - 7] = 0;
    }

    char line[COMM_MONITOR_ASCII_BODY_MAX];
    int off = snprintf(line, sizeof(line), "ACK ret=0");

    char *tok = strtok(tmp, ",");
    while (tok) {
        while (*tok == ' ') tok++;
        if (!isdigit((unsigned char)*tok)) { nak(1, "parse"); return; }
        unsigned id = (unsigned)strtoul(tok, NULL, 10);
        if (id >= g_var_count) { nak(2, "idx"); return; }
        uint32_t v = comm_registry_read((uint8_t)id);
        if (compact) {
            off += snprintf(line + off, sizeof(line) - off,
                            " %u=%lu", id, (unsigned long)v);
        } else {
            off += snprintf(line + off, sizeof(line) - off,
                            " id=%u name=%s value=%lu",
                            id, g_var_names[id], (unsigned long)v);
        }
        tok = strtok(NULL, ",");
    }
    respond(line);
}

static void handle_help(void)
{
    respond("ACK ret=0 cmds=PING,LIST,GET,HELP");
}

static void dispatch(char *line)
{
    char *sp = strchr(line, ' ');
    char *args = NULL;
    if (sp) { *sp = 0; args = sp + 1; }
    for (char *p = line; *p; p++) *p = (char)toupper((unsigned char)*p);

    if (strcmp(line, "PING") == 0) { handle_ping(); return; }
    if (strcmp(line, "LIST") == 0) { handle_list(); return; }
    if (strcmp(line, "GET")  == 0) { handle_get(args); return; }
    if (strcmp(line, "HELP") == 0) { handle_help(); return; }
    nak(5, "cmd");
}

void comm_monitor_on_rx_byte(uint8_t b)
{
    switch (g_state) {
    case RX_WAIT_STX:
        if (b == 0x02) { g_pos = 0; g_state = RX_BODY; }
        return;
    case RX_BODY:
        if (b == 0x0D) { g_state = RX_CR; return; }
        if (b >= 0x20 && b <= 0x7E
            && g_pos < COMM_MONITOR_ASCII_BODY_MAX - 1) {
            g_buf[g_pos++] = (char)b;
        } else {
            g_state = RX_WAIT_STX;
        }
        return;
    case RX_CR:
        if (b == 0x03) { g_buf[g_pos] = 0; dispatch(g_buf); }
        g_state = RX_WAIT_STX;
        return;
    }
}

void comm_monitor_poll(void) { /* リングバッファ実装は次パッチ */ }
""")
