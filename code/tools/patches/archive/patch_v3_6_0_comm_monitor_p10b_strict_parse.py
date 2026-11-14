#!/usr/bin/env python3
"""patch_v3_6_0_comm_monitor_p10b_strict_parse.py"""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "codegen" / "comm_monitor" / "templates.py"

MARKER = "manual comma-walk strict parse"

OLD = (
    "    char *tok = strtok(tmp, \",\");\n"
    "    while (tok) {\n"
    "        while (*tok == ' ') tok++;\n"
    "        if (!isdigit((unsigned char)*tok)) { nak(1, \"parse\"); return; }\n"
    "        unsigned id = (unsigned)strtoul(tok, NULL, 10);\n"
    "        if (id >= g_var_count) { nak(2, \"idx\"); return; }\n"
    "        uint32_t v = comm_registry_read((uint8_t)id);\n"
    "        if (compact) {\n"
    "            off += snprintf(line + off, sizeof(line) - off,\n"
    "                            \" %u=%lu\", id, (unsigned long)v);\n"
    "        } else {\n"
    "            off += snprintf(line + off, sizeof(line) - off,\n"
    "                            \" id=%u name=%s value=%lu\",\n"
    "                            id, g_var_names[id], (unsigned long)v);\n"
    "        }\n"
    "        tok = strtok(NULL, \",\");\n"
    "    }\n"
)

NEW = (
    "    /* manual comma-walk strict parse (spec 3.2: id is 10-decimal) */\n"
    "    const char *p = tmp;\n"
    "    while (1) {\n"
    "        const char *comma = strchr(p, ',');\n"
    "        size_t len = comma ? (size_t)(comma - p) : strlen(p);\n"
    "        while (len > 0 && *p == ' ') { p++; len--; }\n"
    "        while (len > 0 && p[len - 1] == ' ') { len--; }\n"
    "        if (len == 0) { nak(1, \"parse\"); return; }\n"
    "        if (len >= 16) { nak(1, \"parse\"); return; }\n"
    "        char tok[16];\n"
    "        memcpy(tok, p, len); tok[len] = 0;\n"
    "        char *end = NULL;\n"
    "        unsigned long vlong = strtoul(tok, &end, 10);\n"
    "        if (end == tok || *end != 0) { nak(1, \"parse\"); return; }\n"
    "        unsigned id = (unsigned)vlong;\n"
    "        if (id >= g_var_count) { nak(2, \"idx\"); return; }\n"
    "        uint32_t v = comm_registry_read((uint8_t)id);\n"
    "        if (compact) {\n"
    "            off += snprintf(line + off, sizeof(line) - off,\n"
    "                            \" %u=%lu\", id, (unsigned long)v);\n"
    "        } else {\n"
    "            off += snprintf(line + off, sizeof(line) - off,\n"
    "                            \" id=%u name=%s value=%lu\",\n"
    "                            id, g_var_names[id], (unsigned long)v);\n"
    "        }\n"
    "        if (!comma) break;\n"
    "        p = comma + 1;\n"
    "    }\n"
)


def main() -> int:
    print("=== patch_v3_6_0_comm_monitor_p10b_strict_parse ===")
    if not TARGET.is_file():
        print(f"[error] not found: {TARGET}", file=sys.stderr)
        return 1
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        print("  [skip] already patched")
        return 0
    if OLD not in text:
        print("[error] anchor not found in handle_get", file=sys.stderr)
        return 1
    text = text.replace(OLD, NEW, 1)
    TARGET.write_text(text, encoding="utf-8")
    print("  [patched] strict id parse in handle_get")
    print("=== done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
