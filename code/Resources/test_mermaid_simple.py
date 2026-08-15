import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QPlainTextEdit, QLabel
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QFont

# ----------------------------------------------------------------------
# ログ用
# ----------------------------------------------------------------------
def log(msg):
    print(f"[LOG] {msg}", flush=True)


# ----------------------------------------------------------------------
# リソースパス
# ----------------------------------------------------------------------
def get_resource_path(filename: str = "") -> Path:
    # このファイルは code/ 直下にある前提
    base_path = Path(__file__).resolve().parent / "Resources"
    if filename:
        return base_path / filename
    return base_path


# ----------------------------------------------------------------------
# テスト用Mermaidコード
# ----------------------------------------------------------------------
TEST_MERMAID_CODE = """
stateDiagram-v2
    [*] --> Idle
    Idle --> Active : start
    Active --> Idle : stop
    Active --> Error : error [err_code != 0]
    Error --> Active : [retry_count < 3]
    Error --> Halt : [retry_count >= 3]
    Halt --> [*]
"""


# ----------------------------------------------------------------------
# メインウィンドウ
# ----------------------------------------------------------------------
class MermaidTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mermaid簡易テスト")
        self.resize(800, 600)

        layout = QVBoxLayout()

        # 説明ラベル
        label = QLabel("mermaidwin.js を埋め込んだWebEngineViewを表示します")
        layout.addWidget(label)

        # WebEngineView
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_load_finished)
        layout.addWidget(self.web_view)

        # ログ表示用テキスト
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_view)

        # 実行ボタン
        btn = QPushButton("Mermaid再実行")
        btn.clicked.connect(self._run_mermaid)
        layout.addWidget(btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 初期表示
        self._load_mermaid()

    # ------------------------------------------------------------------
    # Mermaidを読み込む
    # ------------------------------------------------------------------
    def _load_mermaid(self):
        log("_load_mermaid() called")

        # mermaidwin.js を読み込む
        js_path = get_resource_path("mermaidwin.js")
        log(f"JS path: {js_path}")
        log(f"JS exists: {js_path.exists()}")

        if js_path.exists():
            script_content = js_path.read_text(encoding="utf-8", errors="ignore")
            log(f"JS size: {len(script_content)} chars")
        else:
            script_content = ""
            log("ERROR: mermaidwin.js not found")

        # HTML組み立て
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{script_content}</script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
            mermaid.run();
        }});
    </script>
</head>
<body>
    <pre class="mermaid">
{TEST_MERMAID_CODE}
    </pre>
</body>
</html>"""

        base_url = QUrl.fromLocalFile(str(get_resource_path("")))
        log(f"base_url: {base_url.toString()}")

        self.web_view.setHtml(html, base_url)

    # ------------------------------------------------------------------
    # loadFinished
    # ------------------------------------------------------------------
    def _on_load_finished(self, ok: bool):
        log(f"loadFinished: ok={ok}")
        if ok:
            # 描画結果を確認
            self.web_view.page().runJavaScript(
                "document.querySelector('svg') !== null",
                self._on_check_svg
            )

    def _on_check_svg(self, result):
        log(f"SVG element exists: {result}")

    # ------------------------------------------------------------------
    # Mermaid再実行
    # ------------------------------------------------------------------
    def _run_mermaid(self):
        log("manual mermaid.run()")
        self.web_view.page().runJavaScript("mermaid.run();")


def main():
    app = QApplication(sys.argv)
    window = MermaidTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()