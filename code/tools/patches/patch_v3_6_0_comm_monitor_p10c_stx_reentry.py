#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p10c_stx_reentry.py

Fix spec §7 hot-plug recovery: if STX arrives while RX_BODY is active,
treat it as the start of a new frame instead of discarding it.

Current behavior (bug):
  STX "GET 3"   (incomplete, RX_BODY)
  STX "PING" CR ETX
     ^ ignored as "control char in body" -> WAIT_STX
       -> "PING" body bytes discarded
       -> no response

New behavior:
  STX "GET 3"   (incomplete, RX_BODY)
  STX "PING" CR ETX
     ^ in RX_BODY, treat as fresh STX: g_pos=0, stay in RX_BODY
       -> "PING" body read normally
       -> ACK returned

Idempotent.
"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "codegen" / "comm_monitor" / "templates.py"

MARKER = "STX reentry in RX_BODY"


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p10c_stx_reentry ===")
    if not TARGET.is_file():
        print(f"[error] not found: {TARGET}", file=sys.stderr)
        return 1
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print("  [skip] already patched")
        return 0

    # 1) Add STX reentry branch in RX_BODY
    #    Insert a new "if (b == 0x02)" before the CR check.
    old_body = (
        "    case RX_BODY:\n"
        "        if (b == 0x0D) { g_state = RX_CR; return; }\n"
    )
    new_body = (
        "    case RX_BODY:\n"
        "        if (b == 0x02) {\n"
        "            /* STX reentry in RX_BODY: discard partial frame,\n"
        "             * start a fresh one (spec 3.1 / 7). */\n"
        "            g_pos = 0;\n"
        "            return;\n"
        "        }\n"
        "        if (b == 0x0D) { g_state = RX_CR; return; }\n"
    )
    if old_body not in text:
        print("[error] RX_BODY anchor not found", file=sys.stderr)
        return 1
    text = text.replace(old_body, new_body, 1)

    # 2) Also: if STX arrives in RX_CR (i.e., CR not followed by ETX),
    #    treat it as a fresh frame start.
    old_cr = (
        "    case RX_CR:\n"
        "        if (b == 0x03) { g_buf[g_pos] = 0; dispatch(g_buf); }\n"
        "        g_state = RX_WAIT_STX;\n"
        "        return;\n"
    )
    new_cr = (
        "    case RX_CR:\n"
        "        if (b == 0x03) { g_buf[g_pos] = 0; dispatch(g_buf); }\n"
        "        if (b == 0x02) {\n"
        "            /* CR not followed by ETX, but STX starts a new\n"
        "             * frame immediately. */\n"
        "            g_pos = 0;\n"
        "            g_state = RX_BODY;\n"
        "            return;\n"
        "        }\n"
        "        g_state = RX_WAIT_STX;\n"
        "        return;\n"
    )
    if old_cr not in text:
        print("[error] RX_CR anchor not found", file=sys.stderr)
        return 1
    text = text.replace(old_cr, new_cr, 1)

    TARGET.write_text(text, encoding="utf-8")
    print("  [patched] STX reentry in RX_BODY and RX_CR")
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
