# eclipse_installer/__main__.py
"""Entry point: python -m eclipse_installer [--cli ...]"""
from __future__ import annotations

import sys


def main() -> int:
    argv = sys.argv[1:]
    if "--cli" in argv:
        from .cli import main as cli_main
        return cli_main([a for a in argv if a != "--cli"])
    # Default: GUI
    try:
        from .gui import main as gui_main
    except ImportError as e:
        print(f"[ERROR] GUI not available: {e}", file=sys.stderr)
        print("Install PySide6: pip install PySide6", file=sys.stderr)
        return 1
    return gui_main()


if __name__ == "__main__":
    sys.exit(main())
