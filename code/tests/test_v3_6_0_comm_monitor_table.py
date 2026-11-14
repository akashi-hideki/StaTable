"""v3.6.0 comm_monitor command table tests (spec §8, §11)."""
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_CODE_DIR = _TESTS_DIR.parent
for _p in (str(_CODE_DIR), str(_TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from test_v3_6_0_comm_monitor_ascii import (  # noqa: F401
    host_binary, hp, STX, CR, ETX, VARS,
)


BUILTIN = ["PING", "LIST", "GET", "HELP"]


# ----------------------------------------------------------------------
# HELP response format (spec §3.4 / §8)
# ----------------------------------------------------------------------

def test_help_format(hp):
    hp.send_frame("HELP")
    resp = hp.read_frame()
    assert resp.startswith("ACK ret=0 cmds=")


def test_help_contains_all_builtin(hp):
    hp.send_frame("HELP")
    resp = hp.read_frame()
    for cmd in BUILTIN:
        assert cmd in resp, f"HELP missing {cmd}: {resp!r}"


def test_help_no_unknown_commands(hp):
    hp.send_frame("HELP")
    resp = hp.read_frame()
    assert "FOO" not in resp
    assert "SET" not in resp


def test_help_lowercase(hp):
    hp.send_frame("help")
    assert "cmds=" in hp.read_frame()


def test_help_mixed_case(hp):
    hp.send_frame("HeLp")
    assert "cmds=" in hp.read_frame()


def test_help_idempotent(hp):
    for _ in range(5):
        hp.send_frame("HELP")
        assert "cmds=" in hp.read_frame()


def test_help_order_stable(hp):
    hp.send_frame("HELP")
    resp1 = hp.read_frame()
    hp.send_frame("HELP")
    resp2 = hp.read_frame()
    assert resp1 == resp2


def test_help_order_ping_first(hp):
    hp.send_frame("HELP")
    resp = hp.read_frame()
    cmds = resp.split("cmds=", 1)[1].split(",")
    assert cmds[0] == "PING"
    assert cmds[-1] == "HELP"


# ----------------------------------------------------------------------
# Dispatch: unknown command rejected
# ----------------------------------------------------------------------

def test_dispatch_unknown_rejected(hp):
    hp.send_frame("UNKNOWN")
    assert hp.read_frame() == "NAK ret=5 reason=cmd"


def test_dispatch_set_rejected(hp):
    """SET is not in builtin table -> CMD error (spec §1.1)."""
    hp.send_frame("SET 0 1")
    assert hp.read_frame() == "NAK ret=5 reason=cmd"


# ----------------------------------------------------------------------
# statable_comm_commands.c (spec §11) -- not yet generated in v3.6.0
# ----------------------------------------------------------------------

@pytest.mark.xfail(
    reason="statable_comm_commands.c (spec §11 table + USER_COMMANDS "
           "markers) is not yet generated. Builtin commands are "
           "hard-coded in statable_comm_monitor.c. v3.6.1 task.",
    strict=False,
)
def test_commands_c_file_exists(tmp_path):
    from codegen.comm_monitor.config import CommMonitorConfig
    from codegen.comm_monitor.registry import build_registry
    from codegen.comm_monitor.generator import CommMonitorGenerator

    reg = build_registry([{'name': 'x', 'type': 'uint32_t', 'size': 4}])
    CommMonitorGenerator(CommMonitorConfig(enabled=True), reg).generate(tmp_path)
    assert (tmp_path / 'statable_comm_commands.c').exists()


@pytest.mark.xfail(
    reason="USER_COMMANDS markers (spec §8.2) not yet in generated code; "
           "v3.6.1 task.",
    strict=False,
)
def test_commands_c_has_user_marker(tmp_path):
    from codegen.comm_monitor.config import CommMonitorConfig
    from codegen.comm_monitor.registry import build_registry
    from codegen.comm_monitor.generator import CommMonitorGenerator

    reg = build_registry([{'name': 'x', 'type': 'uint32_t', 'size': 4}])
    CommMonitorGenerator(CommMonitorConfig(enabled=True), reg).generate(tmp_path)
    p = tmp_path / 'statable_comm_commands.c'
    if not p.exists():
        pytest.fail("statable_comm_commands.c missing")
    text = p.read_text(encoding='utf-8')
    assert '[[STABLE_USER_CODE_START:USER_COMMANDS]]' in text
    assert '[[STABLE_USER_CODE_END:USER_COMMANDS]]' in text
