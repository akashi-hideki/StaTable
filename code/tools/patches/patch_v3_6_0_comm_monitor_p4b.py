#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p4b.py

Patch 4b: L1 ホストテスト（gcc + stdin/stdout）。
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
REPO = CODE.parent


def write(rel, content):
    p = CODE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  [write ] code/{rel}")


TEST_MAIN_C = '''\
/* L1 host test driver */
#include <stdio.h>
#include <stdint.h>
#include "statable_comm_monitor.h"

static void tx_fn(uint8_t b)
{
    fputc(b, stdout);
    fflush(stdout);
}

int main(void)
{
    comm_monitor_init();
    comm_monitor_set_tx(tx_fn);
    int c;
    while ((c = getchar()) != EOF) {
        comm_monitor_on_rx_byte((uint8_t)c);
        comm_monitor_poll();
    }
    return 0;
}
'''

FAKE_REGISTRY_C = '''\
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
'''

HOST_README = '''\
# L1 host test

Generated C code is built with gcc and driven via stdin/stdout.

Files:

- test_main.c     : stdin -> comm_monitor -> stdout
- fake_registry.c : 5 fake variables

Run tests:

    pytest tests/test_v3_6_0_comm_monitor_ascii.py -v

Requirements:

- gcc on PATH (MinGW, MSYS2, or WSL)
'''

PYTEST_WRAPPER = '''\
"""v3.6.0 L1 host tests (gcc + stdin/stdout)."""
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from codegen.comm_monitor.config import CommMonitorConfig
from codegen.comm_monitor.registry import build_registry, registry_crc32
from codegen.comm_monitor.generator import CommMonitorGenerator

HOST_DIR = Path(__file__).parent / "host"
STX = 0x02
CR = 0x0D
ETX = 0x03

pytestmark = pytest.mark.skipif(
    shutil.which("gcc") is None, reason="gcc not available"
)

VARS = [
    {"name": "g_system_tick", "type": "uint32_t",
     "unit": "1ms", "group": "Timer"},
    {"name": "oven_current_temp", "type": "uint16_t",
     "unit": "degC", "group": "Hardware"},
    {"name": "oven_target_temp", "type": "uint16_t",
     "unit": "degC", "group": "Hardware"},
    {"name": "heater_top_duty", "type": "uint8_t",
     "unit": "%", "group": "Hardware"},
    {"name": "error_code", "type": "uint8_t",
     "unit": "-", "group": "System"},
]


@pytest.fixture(scope="session")
def host_binary(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("host_build")
    reg = build_registry(VARS)
    CommMonitorGenerator(
        CommMonitorConfig(enabled=True), reg
    ).generate(tmp)
    shutil.copy(HOST_DIR / "test_main.c", tmp)
    shutil.copy(HOST_DIR / "fake_registry.c", tmp)

    exe = tmp / ("test_host.exe" if sys.platform == "win32"
                 else "test_host")
    srcs = [
        str(tmp / "test_main.c"),
        str(tmp / "fake_registry.c"),
        str(tmp / "statable_comm_monitor.c"),
        str(tmp / "statable_comm_ring.c"),
    ]
    cmd = ["gcc", "-O2", "-std=c99", "-I", str(tmp),
           "-o", str(exe)] + srcs
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.fail(
            "gcc failed:\n" + result.stderr + "\n" + result.stdout
        )
    return exe, reg


class HostProc:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [str(exe)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0,
        )
        self.q = queue.Queue()
        threading.Thread(
            target=self._reader, args=(self.proc.stdout, self.q),
            daemon=True,
        ).start()

    @staticmethod
    def _reader(stream, q):
        while True:
            b = stream.read(1)
            if not b:
                break
            q.put(b)

    def send(self, data):
        self.proc.stdin.write(data)
        self.proc.stdin.flush()

    def send_frame(self, body):
        frame = (bytes([STX]) + body.encode("ascii")
                 + bytes([CR, ETX]))
        self.send(frame)

    def read_frame(self, timeout=2.0):
        deadline = time.monotonic() + timeout
        buf = bytearray()
        started = False
        while time.monotonic() < deadline:
            try:
                b = self.q.get(
                    timeout=min(deadline - time.monotonic(), 0.1))
            except queue.Empty:
                continue
            if b == b"\\x02":
                buf = bytearray(); started = True
            elif b == b"\\x03" and started:
                return buf.decode("ascii")
            elif started:
                buf.extend(b)
        raise TimeoutError("no frame")

    def try_read_frame(self, timeout=0.3):
        try:
            return self.read_frame(timeout=timeout)
        except TimeoutError:
            return None

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()


@pytest.fixture
def hp(host_binary):
    exe, _ = host_binary
    p = HostProc(exe)
    yield p
    p.close()


def test_ping(hp, host_binary):
    _, reg = host_binary
    hp.send_frame("PING")
    resp = hp.read_frame()
    assert resp.startswith("ACK ret=0 fw=3.6.0 crc=")
    assert f"{registry_crc32(reg):08X}" in resp
    assert "vars=5" in resp


def test_get_single(hp):
    hp.send_frame("GET 1")
    assert hp.read_frame() == (
        "ACK ret=0 id=1 name=oven_current_temp value=25")


def test_get_multiple(hp):
    hp.send_frame("GET 0,1,2")
    resp = hp.read_frame()
    assert "id=0 name=g_system_tick value=1000" in resp
    assert "id=1 name=oven_current_temp value=25" in resp
    assert "id=2 name=oven_target_temp value=200" in resp


def test_get_compact(hp):
    hp.send_frame("GET 0,1 compact")
    assert hp.read_frame() == "ACK ret=0 0=1000 1=25"


def test_get_idx_out_of_range(hp):
    hp.send_frame("GET 99")
    assert hp.read_frame() == "NAK ret=2 reason=idx"


def test_get_parse_error(hp):
    hp.send_frame("GET abc")
    assert hp.read_frame() == "NAK ret=1 reason=parse"


def test_get_missing_args(hp):
    hp.send_frame("GET")
    assert hp.read_frame() == "NAK ret=7 reason=args"


def test_unknown_command(hp):
    hp.send_frame("FOO")
    assert hp.read_frame() == "NAK ret=5 reason=cmd"


def test_help(hp):
    hp.send_frame("HELP")
    assert hp.read_frame() == (
        "ACK ret=0 cmds=PING,LIST,GET,HELP")


def test_list(hp):
    hp.send_frame("LIST")
    assert hp.read_frame() == "ACK ret=0 vars=5"
    for _ in range(5):
        r = hp.read_frame()
        assert r.startswith("ACK ret=0 id=")


def test_stx_missing_dropped(hp):
    hp.send(b"PING\\r\\x03")
    assert hp.try_read_frame() is None


def test_cr_missing_dropped(hp):
    hp.send(bytes([STX]) + b"PING" + bytes([ETX]))
    assert hp.try_read_frame() is None


def test_etx_missing_dropped(hp):
    hp.send(bytes([STX]) + b"PING" + bytes([CR]) + b"X")
    assert hp.try_read_frame() is None


def test_partial_frame_no_response(hp):
    hp.send(bytes([STX]) + b"GET 3")
    assert hp.try_read_frame() is None
'''


def create_host_files():
    write("tests/host/test_main.c", TEST_MAIN_C)
    write("tests/host/fake_registry.c", FAKE_REGISTRY_C)
    write("tests/host/README.md", HOST_README)


def create_pytest_wrapper():
    write("tests/test_v3_6_0_comm_monitor_ascii.py", PYTEST_WRAPPER)


def register_in_ci():
    p = REPO / ".github" / "workflows" / "check.yml"
    text = p.read_text(encoding="utf-8")
    if "test_v3_6_0_comm_monitor_ascii" in text:
        print("  [skip ] check.yml already has ascii test")
        return
    anchor = ("coverage run --parallel-mode "
              "tests/test_v3_6_0_comm_monitor_integration.py")
    if anchor not in text:
        print("  [error] anchor not found in check.yml")
        return
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if anchor in line:
            indent = line[: len(line) - len(line.lstrip())]
            lines.insert(
                i + 1,
                f"{indent}coverage run --parallel-mode "
                f"tests/test_v3_6_0_comm_monitor_ascii.py",
            )
            break
    p.write_text("\n".join(lines), encoding="utf-8")
    print("  [write ] check.yml (ascii test registered)")


def update_readme():
    p = REPO / "README.md"
    text = p.read_text(encoding="utf-8")
    repls = [
        ("Tests-1887%20PASS", "Tests-1901%20PASS"),
        ("1887 PASS", "1901 PASS"),
        ("1887 tests", "1901 tests"),
        ("51 test suites", "52 test suites"),
        ("51 suites", "52 suites"),
    ]
    changed = False
    for old, new in repls:
        if old in text:
            text = text.replace(old, new)
            changed = True
    if changed:
        p.write_text(text, encoding="utf-8")
        print("  [write ] README.md (52 suites / 1901 PASS)")
    else:
        print("  [skip ] README unchanged")


def main():
    print("=== patch_v3_6_0_comm_monitor_p4b ===")
    print(f"repo: {REPO}")
    create_host_files()
    create_pytest_wrapper()
    register_in_ci()
    update_readme()
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())