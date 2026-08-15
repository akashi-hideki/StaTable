import sys
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
        self.setWindowTitle("Mermaid Test (External + File Access)")
        self.resize(800, 600)

        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)

        # ★ ローカルファイルアクセスを許可
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

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="mermaidwin.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: false, theme: 'default' }});
        function renderMermaid() {{
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
        }}
    </script>
</head>
<body>
<pre class="mermaid">
{mermaid_code}
</pre>
<script>
    window.addEventListener('load', renderMermaid);
</script>
</body>
</html>"""

        resources_dir = js_path.parent
        base_url = QUrl.fromLocalFile(str(resources_dir))
        print(f"[BASE URL] {base_url.toString()}")
        self.web_view.setHtml(html, base_url)

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