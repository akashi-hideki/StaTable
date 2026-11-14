#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p4a.py - TeraTerm macro for ASCII mode."""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
REPO = CODE.parent


TTL_LINES = [
    "; statable.ttl - TeraTerm macro for StaTable comm monitor (ASCII mode)",
    "; Usage: TeraTerm -> Control -> Macro -> Load this file",
    "; Wire: STX(0x02) + body + CR(0x0D) + ETX(0x03)",
    "",
    ":loop",
    "  listbox 'StaTable Commands' 'PING|LIST|HELP|GET|Custom|Quit'",
    "  if result == 0 goto end",
    "  if inputstr == 'PING' goto send_ping",
    "  if inputstr == 'LIST' goto send_list",
    "  if inputstr == 'HELP' goto send_help",
    "  if inputstr == 'GET' goto send_get",
    "  if inputstr == 'Custom' goto send_custom",
    "  if inputstr == 'Quit' goto end",
    "  goto loop",
    "",
    ":send_ping",
    "  send #2 'PING' #13 #3",
    "  goto loop",
    "",
    ":send_list",
    "  send #2 'LIST' #13 #3",
    "  goto loop",
    "",
    ":send_help",
    "  send #2 'HELP' #13 #3",
    "  goto loop",
    "",
    ":send_get",
    "  inputbox 'Enter variable ID(s)' 'GET'",
    "  if result == 0 goto loop",
    "  send #2 'GET ' inputstr #13 #3",
    "  goto loop",
    "",
    ":send_custom",
    "  inputbox 'Command text (without STX/CR/ETX)' 'GET 0,1 compact'",
    "  if result == 0 goto loop",
    "  send #2 inputstr #13 #3",
    "  goto loop",
    "",
    ":end",
    "  end",
]


README_LINES = [
    "# TeraTerm macro for StaTable comm monitor",
    "",
    "`statable.ttl` provides a menu-driven interface for the ASCII protocol",
    "so you do not have to type STX / CR / ETX by hand.",
    "",
    "## Requirements",
    "",
    "- TeraTerm 4.105 or later",
    "- Connected to the device UART (baud rate must match firmware)",
    "",
    "## Usage",
    "",
    "1. Open TeraTerm, select the COM port (e.g. 115200, 8N1)",
    "2. Control -> Macro -> select statable.ttl",
    "3. A menu appears: PING / LIST / HELP / GET / Custom / Quit",
    "",
    "## Commands",
    "",
    "| Menu   | Sent frame              | Example response |",
    "|--------|-------------------------|------------------|",
    "| PING   | STX PING CR ETX         | ACK ret=0 fw=3.6.0 crc=8A3F21C7 vars=30 |",
    "| LIST   | STX LIST CR ETX         | ACK ret=0 vars=30 + 30 lines |",
    "| HELP   | STX HELP CR ETX         | ACK ret=0 cmds=PING,LIST,GET,HELP |",
    "| GET    | STX GET id CR ETX       | ACK ret=0 id=1 name=... value=25 |",
    "| Custom | free text               | depends on command |",
    "",
    "GET accepts single id (0), multiple ids (0,1,2),",
    "or compact form (0,1,2 compact -> response 0=1000 1=25 2=200).",
    "",
    "## Note",
    "",
    "The macro is ASCII only, so it works regardless of TeraTerm",
    "character encoding (Shift_JIS / UTF-8).",
]


def write_lines(rel, lines):
    p = CODE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  [write ] code/{rel} ({len(lines)} lines)")


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p4a ===")
    print(f"repo: {REPO}")
    write_lines("tools/teraterm/statable.ttl", TTL_LINES)
    write_lines("tools/teraterm/README.md", README_LINES)
    print("  [note ] README badge unchanged (no new test suite in p4a)")
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())