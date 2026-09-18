import sys
from pathlib import Path

# ウィンドウ・プレビューのサイズ定数
WINDOW_WIDTH = 1800
WINDOW_HEIGHT = 1000
MERMAID_PREVIEW_MIN_HEIGHT = 400
TABLE_PREVIEW_RATIO = 0.65
MAX_COLUMN_WIDTH = 400
MIN_ROW_HEIGHT = 30
MAX_ROW_HEIGHT = 100


def get_resource_path(filename: str = "") -> Path:
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS) / "Resources"
    else:
        base_path = Path(__file__).resolve().parent.parent / "Resources"
    if filename:
        return base_path / filename
    return base_path