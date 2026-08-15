import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl

# リソースパス解決（code/Resources を指す）
def get_resource_path(filename="mermaidwin.js"):
    return Path(__file__).resolve().parent / "Resources" / filename


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mermaid WebEngine Test")
        self.resize(800, 600)

        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)
        self.web_view.loadFinished.connect(self._on_load_finished)

        self.load_mermaid()

    def load_mermaid(self):
        js_path = get_resource_path()
        print(f"[LOG] JS path: {js_path}")
        print(f"[LOG] JS exists: {js_path.exists()}")

        if not js_path.exists():
            print("[LOG] ERROR: mermaidwin.js not found")
            return

        js_content = js_path.read_text(encoding="utf-8", errors="ignore")
        # 重要: </script> をエスケープ
        js_content = js_content.replace('</script>', '<\\/script>')

        mermaid_code = """stateDiagram-v2
    [*] --> Idle
    Idle --> Active : start
    Active --> [*] : stop
"""

        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<pre class="mermaid">
{mermaid_code}
</pre>
<script>{js_content}</script>
<script>
    mermaid.initialize({{ startOnLoad: false, theme: 'default' }});
    mermaid.init(undefined, document.querySelectorAll('.mermaid'));
</script>
</body>
</html>"""

        resources_dir = js_path.parent
        base_url = QUrl.fromLocalFile(str(resources_dir))
        print(f"[LOG] base_url: {base_url.toString()}")
        self.web_view.setHtml(html, base_url)

    def _on_load_finished(self, ok):
        print(f"[LOG] loadFinished: ok={ok}")
        if ok:
            # SVG要素があるか確認
            self.web_view.page().runJavaScript(
                "document.querySelector('.mermaid svg') !== null;",
                self._on_svg_check
            )

    def _on_svg_check(self, result):
        print(f"[LOG] SVG element exists: {result}")
        if result:
            print("[SUCCESS] Mermaid rendered successfully!")
        else:
            print("[FAIL] SVG not found. mermaid may not have run.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())