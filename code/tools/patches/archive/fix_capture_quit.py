"""fix_capture_quit.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "capture_screenshots_tool.py"
t = TOOL.read_text(encoding="utf-8")

def _must(old, new, label, count=1):
    global t
    n = t.count(old)
    if n != count:
        raise SystemExit(f"[FAIL] {label}: count={n}")
    t = t.replace(old, new)
    print(f"[OK] {label}")

# 1) docstring を raw string に（\c 警告対策）
_must(
    '"""Manual screenshot tool for WeChat promotion.',
    'r"""Manual screenshot tool for WeChat promotion.',
    "docstring raw",
)

# 2) Quit を明示的な quit に
_must(
    "        self.btn_quit = QPushButton(\"Quit\")\n"
    "        self.btn_quit.clicked.connect(self.close)\n",
    "        self.btn_quit = QPushButton(\"Quit\")\n"
    "        self.btn_quit.clicked.connect(self._quit)\n",
    "quit handler",
)

# 3) _quit メソッド + closeEvent を追加
_must(
    "    def on_open(self):\n"
    "        os.startfile(str(OUT_DIR))\n",
    "    def _quit(self):\n"
    "        QApplication.instance().quit()\n"
    "\n"
    "    def closeEvent(self, event):\n"
    "        QApplication.instance().quit()\n"
    "        event.accept()\n"
    "\n"
    "    def on_open(self):\n"
    "        os.startfile(str(OUT_DIR))\n",
    "quit method",
)

TOOL.write_text(t, encoding="utf-8")
print(f"[OK] {TOOL}")
