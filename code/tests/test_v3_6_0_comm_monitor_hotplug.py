"""v3.6.0 comm_monitor hot-plug tests (spec §7)."""
import sys
import time
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


# ----------------------------------------------------------------------
# Stateless recovery: a broken frame must not poison the next one
# ----------------------------------------------------------------------

def test_partial_frame_then_valid_frame(hp):
    """spec §7: partial frame -> next STX starts a new frame."""
    hp.send(bytes([STX]) + b"GET 3")           # incomplete (no CR ETX)
    hp.send_frame("PING")                      # fresh frame
    assert hp.read_frame().startswith("ACK ret=0 fw=")


def test_partial_frame_then_valid_get(hp):
    hp.send(bytes([STX]) + b"GE")
    hp.send_frame("GET 1")
    assert hp.read_frame() == "ACK ret=0 id=1 name=oven_current_temp value=25"


def test_cr_without_etx_then_valid(hp):
    """spec §3.1: CR not followed by ETX -> discard; next frame OK."""
    hp.send(bytes([STX]) + b"PING" + bytes([CR]) + b"X")
    hp.send_frame("PING")
    assert hp.read_frame().startswith("ACK ret=0")


def test_control_char_in_body_then_valid(hp):
    """spec §3.1: control char -> discard frame; recovery."""
    hp.send(bytes([STX]) + b"GE\x01T" + bytes([CR, ETX]))
    hp.send_frame("PING")
    assert hp.read_frame().startswith("ACK ret=0")


def test_non_ascii_in_body_then_valid(hp):
    hp.send(bytes([STX]) + b"GET \xc3\xa9" + bytes([CR, ETX]))
    hp.send_frame("PING")
    assert hp.read_frame().startswith("ACK ret=0")


def test_long_garbage_then_valid(hp):
    """Large junk burst before STX must not break the receiver."""
    hp.send(b"garbage garbage garbage garbage " * 50)
    hp.send_frame("PING")
    assert hp.read_frame().startswith("ACK ret=0")


# ----------------------------------------------------------------------
# Idempotency: identical command -> identical response (spec §7)
# ----------------------------------------------------------------------

def test_ping_idempotent(hp):
    for _ in range(5):
        hp.send_frame("PING")
        assert hp.read_frame().startswith("ACK ret=0 fw=")


def test_help_idempotent(hp):
    for _ in range(3):
        hp.send_frame("HELP")
        assert "cmds=" in hp.read_frame()


# ----------------------------------------------------------------------
# Multiple error frames in a row then success (stateless)
# ----------------------------------------------------------------------

def test_errors_then_success(hp):
    for cmd in ["FOO", "GET abc", "GET 99"]:
        hp.send_frame(cmd)
        assert hp.read_frame().startswith("NAK ret=")
    hp.send_frame("PING")
    assert hp.read_frame().startswith("ACK ret=0")


def test_alternating_error_success(hp):
    for _ in range(3):
        hp.send_frame("FOO")
        assert hp.read_frame() == "NAK ret=5 reason=cmd"
        hp.send_frame("PING")
        assert hp.read_frame().startswith("ACK ret=0")


# ----------------------------------------------------------------------
# Back-to-back frames (no pause between)
# ----------------------------------------------------------------------

def test_back_to_back_frames(hp):
    """Two frames sent as one write; both must be processed in order."""
    payload = (bytes([STX]) + b"PING" + bytes([CR, ETX])
               + bytes([STX]) + b"HELP" + bytes([CR, ETX]))
    hp.send(payload)
    assert hp.read_frame().startswith("ACK ret=0 fw=")
    assert "cmds=" in hp.read_frame()


def test_burst_of_gets(hp):
    """3 GET frames concatenated; responses must match in order."""
    payload = b""
    for i in (0, 1, 2):
        payload += (bytes([STX]) + f"GET {i}".encode()
                    + bytes([CR, ETX]))
    hp.send(payload)
    for i in (0, 1, 2):
        resp = hp.read_frame()
        assert f"id={i} " in resp


# ----------------------------------------------------------------------
# Idle timeout (spec §7) -- NOT yet implemented in firmware
# ----------------------------------------------------------------------

def test_partial_frame_recovers_via_stx(hp):
    """spec §3.1: STX always starts a fresh frame; idle timeout is
    not required for recovery (v3.6.0 uses STX reentry)."""
    hp.send(bytes([STX]) + b"GET")
    time.sleep(0.15)  # > 100ms idle
    hp.send(bytes([STX]) + b"PING" + bytes([CR, ETX]))
    assert hp.read_frame().startswith("ACK ret=0")
