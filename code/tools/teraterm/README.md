# TeraTerm macro for StaTable comm monitor

`statable.ttl` provides a menu-driven interface for the ASCII protocol
so you do not have to type STX / CR / ETX by hand.

## Requirements

- TeraTerm 4.105 or later
- Connected to the device UART (baud rate must match firmware)

## Usage

1. Open TeraTerm, select the COM port (e.g. 115200, 8N1)
2. Control -> Macro -> select statable.ttl
3. A menu appears: PING / LIST / HELP / GET / Custom / Quit

## Commands

| Menu   | Sent frame              | Example response |
|--------|-------------------------|------------------|
| PING   | STX PING CR ETX         | ACK ret=0 fw=3.6.0 crc=8A3F21C7 vars=30 |
| LIST   | STX LIST CR ETX         | ACK ret=0 vars=30 + 30 lines |
| HELP   | STX HELP CR ETX         | ACK ret=0 cmds=PING,LIST,GET,HELP |
| GET    | STX GET id CR ETX       | ACK ret=0 id=1 name=... value=25 |
| Custom | free text               | depends on command |

GET accepts single id (0), multiple ids (0,1,2),
or compact form (0,1,2 compact -> response 0=1000 1=25 2=200).

## Note

The macro is ASCII only, so it works regardless of TeraTerm
character encoding (Shift_JIS / UTF-8).
