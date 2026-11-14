#!/usr/bin/env python3
"""fix_p4b_2.py - fix trailing CR and increase buffer size to 256"""
import ast
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent


def fix_config():
    p = CODE / "codegen" / "comm_monitor" / "config.py"
    text = p.read_text(encoding="utf-8")
    if "ascii_body_max: int = 256" in text:
        print("[skip] config already 256")
        return
    if "ascii_body_max: int = 96" not in text:
        print("[err] ascii_body_max=96 not found in config.py")
        return
    text = text.replace("ascii_body_max: int = 96",
                        "ascii_body_max: int = 256")
    p.write_text(text, encoding="utf-8")
    print("[fix] config.py: ascii_body_max 96 -> 256")


def fix_test():
    p = CODE / "tests" / "test_v3_6_0_comm_monitor_ascii.py"
    text = p.read_text(encoding="utf-8")
    old = 'return buf.decode("ascii")'
    new = 'return buf.decode("ascii").rstrip("\\r")'
    if new in text:
        print("[skip] test already strips CR")
        return
    if old not in text:
        print("[err] 'return buf.decode' not found")
        return
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("[fix] test: strip trailing CR")

    try:
        ast.parse(text)
        print("[ok ] syntax valid")
    except SyntaxError as e:
        print(f"[err] syntax error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    fix_config()
    fix_test()