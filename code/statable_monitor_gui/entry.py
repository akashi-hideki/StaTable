"""PyInstaller entry point for StaTable Monitor GUI.

Build from project root:
    pyinstaller --onefile --windowed --name StaTableMonitorGUI ^
      --paths code ^
      --hidden-import serial --hidden-import serial.tools.list_ports ^
      --hidden-import PySide6.QtCore --hidden-import PySide6.QtWidgets ^
      code\statable_monitor_gui\entry.py
"""
import sys
from pathlib import Path

_code_dir = Path(__file__).resolve().parent.parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

from statable_monitor_gui.main_window import main

if __name__ == "__main__":
    sys.exit(main())
