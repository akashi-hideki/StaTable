#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor.py

StaTable v3.6.0 通信モニター（GET 専用 / ASCII のみ）の基盤を追加する。
"""
from __future__ import annotations
import sys
from pathlib import Path
from string import Template

REPO = Path(__file__).resolve().parent.parent.parent
CODE = REPO
if not (CODE / "pyproject.toml").exists():
    CODE = REPO / "code"


def write(rel: str, content: str) -> None:
    p = CODE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        print(f"  [skip] {rel}")
        return
    p.write_text(content, encoding="utf-8")
    print(f"  [new ] {rel}")


def replace_once(rel: str, old: str, new: str) -> None:
    p = CODE / rel
    if not p.exists():
        print(f"  [warn] {rel} not found")
        return
    text = p.read_text(encoding="utf-8")
    if old not in text:
        print(f"  [warn] {rel}: pattern not found")
        return
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"  [upd ] {rel}")


CONFIG_PY = '''"""CommMonitor の設定値（v3.6.0 / GET 専用 / ASCII のみ）。"""
from dataclasses import dataclass

MIN_POLL_PERIOD_MS = 100
DEFAULT_POLL_PERIOD_MS = 200
MAX_POLL_PERIOD_MS = 60_000


@dataclass
class CommMonitorConfig:
    enabled: bool = False
    ascii_body_max: int = 96
    rx_ring_size: int = 64
    tx_ring_size: int = 64
    idle_ms: int = 100
    ack_unit: bool = True
    ack_name: bool = True
    period_ms: int = DEFAULT_POLL_PERIOD_MS

    def validate(self) -> None:
        if self.rx_ring_size & (self.rx_ring_size - 1):
            raise ValueError("rx_ring_size must be power of two")
        if self.tx_ring_size & (self.tx_ring_size - 1):
            raise ValueError("tx_ring_size must be power of two")
        if not (MIN_POLL_PERIOD_MS <= self.period_ms <= MAX_POLL_PERIOD_MS):
            raise ValueError(
                f"period_ms must be {MIN_POLL_PERIOD_MS}..{MAX_POLL_PERIOD_MS}"
            )
'''

REGISTRY_PY = '''"""XML 変数モデルからレジストリ（ID 順）を構築。"""
from dataclasses import dataclass
from typing import Iterable
import zlib

_C_TYPE_SIZE = {
    "uint8_t": 1, "int8_t": 1, "bool": 1,
    "uint16_t": 2, "int16_t": 2,
    "uint32_t": 4, "int32_t": 4, "float": 4,
}


def _normalize_type(t: str) -> str:
    return t.replace("volatile", "").replace("const", "").strip()


@dataclass(frozen=True)
class VarMeta:
    id: int
    name: str
    c_type: str
    size: int
    unit: str = "-"
    group: str = "-"
    description: str = ""


def build_registry(variables: Iterable[dict]) -> list[VarMeta]:
    result: list[VarMeta] = []
    for i, v in enumerate(variables):
        t = _normalize_type(v["type"])
        if t not in _C_TYPE_SIZE:
            raise ValueError(f"unsupported type: {v['type']} ({v['name']})")
        result.append(VarMeta(
            id=i,
            name=v["name"],
            c_type=t,
            size=_C_TYPE_SIZE[t],
            unit=v.get("unit", "-"),
            group=v.get("group", "-"),
            description=v.get("description", ""),
        ))
    return result


def registry_crc32(vars_: list[VarMeta]) -> int:
    payload = "\\n".join(f"{v.name}:{v.c_type}" for v in vars_)
    return zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF
'''

TEMPLATES_PY = '''"""C コードテンプレート（v3.6.0 / GET 専用 / ASCII のみ）。"""
from string import Template

CONFIG_H = Template("""\\
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
#define COMM_MONITOR_XML_CRC32      0x$crc32u
#define COMM_MONITOR_VAR_COUNT      $var_countu
#endif
""")

REGISTRY_H = Template("""\\
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

REGISTRY_C = Template("""\\
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

MONITOR_H = Template("""\\
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

MONITOR_C = Template("""\\
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
'''

GENERATOR_PY = '''"""CommMonitor の C コード生成器。"""
from pathlib import Path
from .config import CommMonitorConfig
from .registry import VarMeta, registry_crc32
from . import templates


class CommMonitorGenerator:
    def __init__(self, config: CommMonitorConfig, variables: list[VarMeta]):
        config.validate()
        self.config = config
        self.vars = variables

    def generate(self, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        crc = registry_crc32(self.vars)

        entries = "\\n".join(
            f"    {{ &g_ctx.data.{v.name}, {v.size} }}," for v in self.vars
        )
        names = "\\n".join(f'    "{v.name}",' for v in self.vars)

        rendered = {
            "statable_comm_config.h": templates.CONFIG_H.substitute(
                enabled=int(self.config.enabled),
                body_max=self.config.ascii_body_max,
                rx_ring=self.config.rx_ring_size,
                tx_ring=self.config.tx_ring_size,
                idle_ms=self.config.idle_ms,
                ack_unit=int(self.config.ack_unit),
                ack_name=int(self.config.ack_name),
                version="3.6.0",
                crc32=f"{crc:08X}",
                var_count=len(self.vars),
            ),
            "statable_comm_registry.h": templates.REGISTRY_H.substitute(),
            "statable_comm_registry.c": templates.REGISTRY_C.substitute(
                entries=entries, names=names,
            ),
            "statable_comm_monitor.h": templates.MONITOR_H.substitute(),
            "statable_comm_monitor.c": templates.MONITOR_C.substitute(),
        }

        written: list[Path] = []
        for name, body in rendered.items():
            p = out_dir / name
            p.write_text(body, encoding="utf-8")
            written.append(p)
        return written
'''

SDK_INIT = '''"""statable-monitor: StaTable UART モニター SDK (v0.1.0)."""
from .connection import StaTableMonitor, ConnectionError
from .registry import VariableInfo

__all__ = ["StaTableMonitor", "ConnectionError", "VariableInfo"]
__version__ = "0.1.0"
'''

SDK_CONNECTION = '''"""接続・フレーム送受信（ASCII のみ）。"""
import time

STX = 0x02
ETX = 0x03
CR = 0x0D
MIN_PERIOD_MS = 100
MAX_PERIOD_MS = 60_000


class ConnectionError(Exception):
    pass


class StaTableMonitor:
    def __init__(self, serial_factory=None):
        self._factory = serial_factory
        self._ser = None
        self._timeout = 1.0

    def connect(self, port, baudrate=115200, xml_path=None):
        if self._factory:
            self._ser = self._factory(
                port=port, baudrate=baudrate, timeout=self._timeout)
        else:
            import serial
            self._ser = serial.Serial(port, baudrate, timeout=self._timeout)
        if xml_path:
            self._verify_xml(xml_path)

    def _verify_xml(self, xml_path):
        from .registry import load_xml
        info = load_xml(xml_path)
        pong = self.ping()
        expected = f"{info.crc32:08X}"
        if pong.get("crc") != expected:
            self._ser.close()
            raise ConnectionError(
                f"XML CRC mismatch: xml={expected}, device={pong.get('crc')}")

    def ping(self):
        return self._command("PING")

    def _command(self, body):
        frame = bytes([STX]) + body.encode("ascii") + bytes([CR, ETX])
        self._ser.write(frame)
        return self._parse(self._read_frame())

    def _read_frame(self):
        buf = bytearray()
        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            b = self._ser.read(1)
            if not b:
                continue
            if b[0] == STX:
                buf.clear()
                continue
            if b[0] == CR:
                nxt = self._ser.read(1)
                if nxt and nxt[0] == ETX:
                    return buf.decode("ascii", "replace")
                continue
            buf.append(b[0])
        raise TimeoutError("no response")

    @staticmethod
    def _parse(line):
        parts = line.split()
        out = {"kind": parts[0] if parts else "",
               "ret": -1}
        for p in parts[1:]:
            if "=" in p:
                k, v = p.split("=", 1)
                out[k] = v
        if "ret" in out:
            out["ret"] = int(out["ret"])
        return out
'''

SDK_REGISTRY = '''"""XML からレジストリを構築。"""
import zlib
from dataclasses import dataclass
from xml.etree import ElementTree as ET


@dataclass
class VariableInfo:
    id: int
    name: str
    c_type: str
    unit: str = "-"
    group: str = "-"
    description: str = ""


@dataclass
class RegistryInfo:
    variables: list
    crc32: int


def load_xml(path):
    root = ET.parse(path).getroot()
    vs = []
    for i, el in enumerate(root.findall(".//variable")):
        raw = el.get("type", "uint32_t")
        t = raw.replace("volatile", "").replace("const", "").strip()
        vs.append(VariableInfo(
            id=i,
            name=el.get("name", f"var{i}"),
            c_type=t,
            unit=el.get("unit", "-"),
            group=el.get("group", "-"),
            description=el.get("description", ""),
        ))
    payload = "\\n".join(f"{v.name}:{v.c_type}" for v in vs)
    crc = zlib.crc32(payload.encode("utf-8")) & 0xFFFFFFFF
    return RegistryInfo(vs, crc)
'''

SDK_POLLING = '''"""PC 側ポーリング制御（最小 100 ms）。"""
import threading
import time


class PollingController:
    MIN_MS = 100
    MAX_MS = 60_000

    def __init__(self, send_get):
        self._send_get = send_get
        self._thread = None
        self._stop = threading.Event()

    def start(self, ids, period_ms=200, on_sample=None):
        if not (self.MIN_MS <= period_ms <= self.MAX_MS):
            raise ValueError(
                f"period_ms must be {self.MIN_MS}..{self.MAX_MS}")
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            args=(list(ids), period_ms, on_sample),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _loop(self, ids, period_ms, on_sample):
        interval = period_ms / 1000.0
        next_t = time.monotonic()
        while not self._stop.is_set():
            try:
                values = self._send_get(ids)
                ts = time.monotonic()
                if on_sample:
                    for idx, val in values.items():
                        on_sample(idx, val, ts)
            except TimeoutError:
                pass
            next_t += interval
            sleep = next_t - time.monotonic()
            if sleep > 0:
                self._stop.wait(sleep)
            else:
                next_t = time.monotonic()
'''

SDK_PSBLOG = '''"""psblog/v1 ライター（PC 側専用）。"""
from datetime import datetime, timezone
from pathlib import Path


class PStaBlogLogger:
    def __init__(self, path, source, firmware, period_ms, variables):
        self.path = Path(path)
        self.source = source
        self.firmware = firmware
        self.period_ms = period_ms
        self.variables = list(variables)
        self._f = None
        self._samples = 0
        self._dropped = 0

    def start(self):
        self._f = self.path.open("w", encoding="utf-8", newline="\\n")
        t0 = datetime.now(timezone.utc).astimezone()
        self._f.write("# StaTable UART Monitor Log\\n")
        self._f.write("@schema       psblog/v1\\n")
        self._f.write(
            f"@captured_at  {t0.isoformat(timespec='milliseconds')}\\n")
        self._f.write(f"@source       uart:{self.source}\\n")
        self._f.write(f"@firmware     {self.firmware}\\n")
        self._f.write("@protocol     pstable-uart/v1\\n")
        self._f.write(f"@period_ms    {self.period_ms}\\n")
        for v in self.variables:
            desc = v.get("description", "")
            desc_q = f'"{desc}"' if desc else ""
            self._f.write(
                f"@var {v['name']} {v['type']} {v.get('unit', '-')} "
                f"{v.get('group', '-')} {desc_q}\\n")

    def write(self, name, value, host_ts):
        if self._f is None:
            return
        t_ms = int(round(host_ts * 1000))
        self._f.write(f"@{t_ms} {name}={value}\\n")
        self._samples += 1

    def stop(self):
        if self._f is None:
            return
        end = datetime.now(timezone.utc).astimezone()
        self._f.write(
            f"@end      {end.isoformat(timespec='milliseconds')}\\n")
        self._f.write(f"@samples  {self._samples}\\n")
        self._f.write(f"@dropped  {self._dropped}\\n")
        self._f.close()
        self._f = None
'''

TEST_GENERATOR = '''"""v3.6.0 通信モニター生成器のテスト。"""
from pathlib import Path
import pytest
from codegen.comm_monitor.config import CommMonitorConfig
from codegen.comm_monitor.registry import build_registry, registry_crc32
from codegen.comm_monitor.generator import CommMonitorGenerator

VARS = [
    {"name": "g_system_tick", "type": "volatile uint32_t",
     "unit": "1ms", "group": "Timer"},
    {"name": "oven_current_temp", "type": "uint16_t",
     "unit": "degC", "group": "Hardware"},
    {"name": "heater_top_duty", "type": "uint8_t",
     "unit": "%", "group": "Hardware"},
]


def test_registry_ids_are_sequential():
    reg = build_registry(VARS)
    assert [v.id for v in reg] == [0, 1, 2]
    assert reg[0].size == 4
    assert reg[1].size == 2
    assert reg[2].size == 1


def test_registry_crc_is_stable():
    reg = build_registry(VARS)
    assert registry_crc32(reg) == registry_crc32(build_registry(VARS))


def test_generator_writes_all_files(tmp_path: Path):
    reg = build_registry(VARS)
    gen = CommMonitorGenerator(CommMonitorConfig(enabled=True), reg)
    written = gen.generate(tmp_path)
    names = {p.name for p in written}
    assert "statable_comm_config.h" in names
    assert "statable_comm_registry.c" in names
    assert "statable_comm_monitor.c" in names


def test_generated_config_has_var_count(tmp_path: Path):
    reg = build_registry(VARS)
    gen = CommMonitorGenerator(CommMonitorConfig(enabled=True), reg)
    gen.generate(tmp_path)
    text = (tmp_path / "statable_comm_config.h").read_text()
    assert "COMM_MONITOR_VAR_COUNT      3u" in text


def test_period_validation_rejects_below_100():
    with pytest.raises(ValueError):
        CommMonitorConfig(period_ms=50).validate()
'''


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor ===")
    print(f"repo: {REPO}")

    write("codegen/comm_monitor/__init__.py",
          '"""v3.6.0 通信モニター生成器。"""\n')
    write("codegen/comm_monitor/config.py", CONFIG_PY)
    write("codegen/comm_monitor/registry.py", REGISTRY_PY)
    write("codegen/comm_monitor/templates.py", TEMPLATES_PY)
    write("codegen/comm_monitor/generator.py", GENERATOR_PY)

    write("statable_monitor/__init__.py", SDK_INIT)
    write("statable_monitor/connection.py", SDK_CONNECTION)
    write("statable_monitor/registry.py", SDK_REGISTRY)
    write("statable_monitor/polling.py", SDK_POLLING)
    write("statable_monitor/psblog_logger.py", SDK_PSBLOG)

    write("tests/test_v3_6_0_comm_monitor_generator.py", TEST_GENERATOR)

    print("--- version bump ---")
    replace_once("pyproject.toml", 'version = "3.5.3"',
                 'version = "3.6.0"')
    replace_once("statable/__init__.py", '__version__ = "3.5.3"',
                 '__version__ = "3.6.0"')
    replace_once("codegen/__init__.py", '__version__ = "3.5.3"',
                 '__version__ = "3.6.0"')

    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())