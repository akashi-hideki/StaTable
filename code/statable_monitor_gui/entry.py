"""PyInstaller entry point for StaTable Monitor GUI.

Build from project root:
    powershell -ExecutionPolicy Bypass -File code/tools/build_monitor_gui.ps1
"""
import sys
from pathlib import Path

_code_dir = Path(__file__).resolve().parent.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

from statable_monitor_gui.main_window import main

if __name__ == "__main__":
    sys.exit(main())
