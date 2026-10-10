"""restore_main.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "eclipse_installer" / "__main__.py"

content = '''# eclipse_installer/__main__.py
"""Entry point: python -m eclipse_installer [--cli ...]"""
from __future__ import annotations

import sys


def main() -> int:
    argv = sys.argv[1:]
    if "--cli" in argv:
        from eclipse_installer.cli import main as cli_main
        return cli_main([a for a in argv if a != "--cli"])
    try:
        from eclipse_installer.gui import main as gui_main
    except ImportError as e:
        print(f"[ERROR] GUI not available: {e}", file=sys.stderr)
        print("Install PySide6: pip install PySide6", file=sys.stderr)
        return 1
    return gui_main()


if __name__ == "__main__":
    sys.exit(main())
'''
M.write_text(content, encoding="utf-8")
print(f"[OK] {M}")
