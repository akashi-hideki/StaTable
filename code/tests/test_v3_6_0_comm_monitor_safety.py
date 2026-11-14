"""v3.6.0 comm_monitor safety tests (spec §1.1, §3.1, §3.2, §4)."""
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
_CODE_DIR = _TESTS_DIR.parent
for _p in (str(_CODE_DIR), str(_TESTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Reuse the exact same host_binary + hp fixtures from the ascii tests.
from test_v3_6_0_comm_monitor_ascii import (  # noqa: F401
    host_binary, hp, STX, CR, ETX, VARS,
)


# ----------------------------------------------------------------------
# SET is out of scope (spec §1.1). Firmware must reject with CMD error.
# ----------------------------------------------------------------------

def test_set_rejected_uppercase(hp):
    hp.send_frame("SET 2 210")
    assert hp.read_frame() == "NAK ret=5 reason=cmd"


def test_set_rejected_lowercase(hp):
    hp.send_frame("set 2 210")
    assert hp.read_frame() == "NAK ret=5 reason=cmd"


def test_set_rejected_mixed_case(hp):
    hp.send_frame("SeT 0 1")
    assert hp.read_frame() == "NAK ret=5 reason=cmd"


# ----------------------------------------------------------------------
# ID parsing edge cases
# ----------------------------------------------------------------------

def test_negative_id(hp):
    """Negative IDs are not valid 10-decimal; must not crash or misparse."""
    hp.send_frame("GET -1")
    resp = hp.read_frame()
    assert resp.startswith("NAK ret=")


def test_non_numeric_id_trailing_char(hp):
    hp.send_frame("GET 1x")
    resp = hp.read_frame()
    assert resp.startswith("NAK ret=1 reason=parse")


def test_non_numeric_id_leading_char(hp):
    hp.send_frame("GET x1")
    resp = hp.read_frame()
    assert resp.startswith("NAK ret=1 reason=parse")


def test_trailing_comma_in_id_list(hp):
    hp.send_frame("GET 0,")
    resp = hp.read_frame()
    assert resp.startswith("NAK ret=1 reason=parse")


def test_double_comma_in_id_list(hp):
    hp.send_frame("GET 0,,1")
    resp = hp.read_frame()
    assert resp.startswith("NAK ret=1 reason=parse")


# ----------------------------------------------------------------------
# ID range boundary (VARS = 5 entries: 0..4)
# ----------------------------------------------------------------------

def test_boundary_id_last_valid(hp):
    hp.send_frame("GET 4")
    resp = hp.read_frame()
    assert resp.startswith("ACK ret=0 id=4")


def test_boundary_id_first_invalid(hp):
    hp.send_frame("GET 5")
    resp = hp.read_frame()
    assert resp.startswith("NAK ret=2")


def test_id_beyond_uint8(hp):
    """IDs >= 256 must not wrap around via uint8 truncation."""
    hp.send_frame("GET 256")
    resp = hp.read_frame()
    assert resp.startswith("NAK ret=2")


def test_mixed_valid_invalid_ids_rejected(hp):
    """A single invalid ID must cause the entire request to fail."""
    hp.send_frame("GET 0,99")
    resp = hp.read_frame()
    assert resp.startswith("NAK ret=2")


# ----------------------------------------------------------------------
# Case-insensitive command names (spec §3.2)
# ----------------------------------------------------------------------

def test_ping_lowercase(hp):
    hp.send_frame("ping")
    assert hp.read_frame().startswith("ACK ret=0 fw=")


def test_get_lowercase(hp):
    hp.send_frame("get 0")
    assert hp.read_frame().startswith("ACK ret=0 id=0")


def test_help_lowercase(hp):
    hp.send_frame("help")
    assert "cmds=" in hp.read_frame()


# ----------------------------------------------------------------------
# Frame content safety (spec §3.1)
# ----------------------------------------------------------------------

def test_empty_body_does_not_crash(hp):
    """STX + CR + ETX (empty body) — must not crash, may NAK or drop."""
    hp.send_frame("")
    resp = hp.try_read_frame()
    assert resp is None or resp.startswith("NAK")


def test_control_char_in_body_dropped(hp):
    """Non-printable control char inside body -> frame discarded (spec §3.1)."""
    hp.send(bytes([STX]) + b"GET\x01" + bytes([CR, ETX]))
    assert hp.try_read_frame() is None


def test_non_ascii_in_body_dropped(hp):
    """Bytes outside 0x20..0x7E -> frame discarded."""
    hp.send(bytes([STX]) + b"GET \xc3\xa9" + bytes([CR, ETX]))
    assert hp.try_read_frame() is None


def test_body_too_long_dropped(hp):
    """Body exceeding COMM_MONITOR_ASCII_BODY_MAX (default 96) is discarded."""
    big = "GET " + ",".join(["0"] * 100)
    assert len(big) > 96
    hp.send_frame(big)
    assert hp.try_read_frame() is None


def test_duplicate_ids_handled(hp):
    """Duplicate IDs: implementation may allow or reject but must not crash."""
    hp.send_frame("GET 0,0,0")
    resp = hp.read_frame()
    assert resp.startswith(("ACK ret=0", "NAK ret="))


# ----------------------------------------------------------------------
# Dispatch continuity: after NAK, next valid command still works
# ----------------------------------------------------------------------

def test_recovery_after_nak(hp):
    """Protocol is stateless; NAK does not break subsequent requests."""
    hp.send_frame("FOO")
    assert hp.read_frame() == "NAK ret=5 reason=cmd"
    hp.send_frame("PING")
    assert hp.read_frame().startswith("ACK ret=0 fw=")


def test_recovery_after_parse_error(hp):
    hp.send_frame("GET abc")
    assert hp.read_frame() == "NAK ret=1 reason=parse"
    hp.send_frame("GET 1")
    assert hp.read_frame().startswith("ACK ret=0 id=1")
