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
        pytest.fail("gcc failed:\n" + result.stderr + "\n" + result.stdout)
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
            if b == b"\x02":
                buf = bytearray(); started = True
            elif b == b"\x03" and started:
                return buf.decode("ascii").rstrip("\r")
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
    hp.send(b"PING\r\x03")
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
