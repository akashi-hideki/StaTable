import sys
import tempfile
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import QUrl


def get_resource_path(filename="mermaidwin.js"):
    return Path(__file__).resolve().parent / "Resources" / filename


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mermaid Test (temp file + load)")
        self.resize(800, 600)

        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)

        # ローカルファイルアクセスを許可
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

        self.web_view.loadFinished.connect(self._on_load_finished)
        self.load_mermaid()

    def load_mermaid(self):
        js_path = get_resource_path()
        print(f"[JS PATH] {js_path}")
        print(f"[JS EXISTS] {js_path.exists()}")
        if not js_path.exists():
            print("[ERROR] mermaidwin.js not found")
            return

        mermaid_code = """stateDiagram-v2
    [*] --> Idle
    Idle --> Active : start
    Active --> [*] : stop
"""

        # mermaidwin.js を絶対URLで指定
        js_abs_url = QUrl.fromLocalFile(str(js_path)).toString()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="{js_abs_url}"></script>
    <script>
        mermaid.initialize({{ startOnLoad: false, theme: 'default' }});
        function renderMermaid() {{
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
        }}
        window.addEventListener('load', renderMermaid);
    </script>
</head>
<body>
<pre class="mermaid">
{mermaid_code}
</pre>
</body>
</html>"""

        # 一時HTMLファイルを作成してロード
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html)
            temp_path = f.name

        print(f"[TEMP HTML] {temp_path}")
        self.web_view.load(QUrl.fromLocalFile(temp_path))

    def _on_load_finished(self, ok):
        print(f"[LOAD FINISHED] ok={ok}")
        if ok:
            # SVG要素の存在確認
            self.web_view.page().runJavaScript(
                "document.querySelector('.mermaid svg') !== null;",
                self._on_svg_check
            )

    def _on_svg_check(self, result):
        print(f"[SVG CHECK] exists={result}")
        if result:
            print("[SUCCESS] Mermaid rendered!")
        else:
            print("[FAIL] SVG not found.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())