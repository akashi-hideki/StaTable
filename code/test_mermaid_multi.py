import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QTextEdit
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEnginePage

# リソースパス解決
def get_resource_path(filename="mermaidwin.js"):
    return Path(__file__).resolve().parent / "Resources" / filename

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mermaid Multi-Pattern Test")
        self.resize(900, 700)

        self.web_view = QWebEngineView()
        self.web_view.page().javaScriptConsoleMessage = self._on_js_console
        self.web_view.loadFinished.connect(self._on_load_finished)

        self.setCentralWidget(self.web_view)

        self.pattern_index = 0
        self.patterns = [
            self._pattern_external_file,
            self._pattern_inline_run,
            self._pattern_inline_init,
            self._pattern_minimal_init,
            self._pattern_plain_text
        ]

        QTimer.singleShot(500, self.run_next_pattern)

    def _on_js_console(self, level, message, line, source):
        print(f"[JS CONSOLE] level={level}, line={line}, source={source}, msg={message}")

    def _on_load_finished(self, ok):
        print(f"[LOAD FINISHED] ok={ok}")
        if ok:
            self.web_view.page().runJavaScript(
                "document.querySelector('.mermaid svg') !== null;",
                self._on_svg_check
            )
        else:
            print("[LOAD FAILED] HTML loading failed.")
            QTimer.singleShot(500, self.run_next_pattern)

    def _on_svg_check(self, result):
        print(f"[SVG CHECK] exists={result}")
        QTimer.singleShot(500, self.run_next_pattern)

    def run_next_pattern(self):
        if self.pattern_index >= len(self.patterns):
            print("[TEST COMPLETE] All patterns tested.")
            return
        pattern = self.patterns[self.pattern_index]
        print(f"\n=== PATTERN {self.pattern_index + 1}: {pattern.__name__} ===")
        self.pattern_index += 1
        pattern()

    def _pattern_external_file(self):
        """パターンA: 外部ファイル参照"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="mermaidwin.js"></script>
</head>
<body>
<pre class="mermaid">stateDiagram-v2
    [*] --> Idle
    Idle --> Active : start
    Active --> [*] : stop</pre>
<script>
    mermaid.initialize({ startOnLoad: false, theme: 'default' });
    mermaid.init(undefined, document.querySelectorAll('.mermaid'));
</script>
</body>
</html>"""
        base_url = QUrl.fromLocalFile(str(get_resource_path().parent))
        self.web_view.setHtml(html, base_url)

    def _pattern_inline_run(self):
        """パターンB: インライン埋め込み + mermaid.run()"""
        js = self._load_js()
        if not js:
            return
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<pre class="mermaid">stateDiagram-v2
    [*] --> Idle
    Idle --> Active : start
    Active --> [*] : stop</pre>
<script>{js}</script>
<script>
    mermaid.initialize({{ startOnLoad: false, theme: 'default' }});
    document.addEventListener('DOMContentLoaded', function() {{
        mermaid.run();
    }});
</script>
</body>
</html>"""
        self.web_view.setHtml(html, QUrl())

    def _pattern_inline_init(self):
        """パターンC: インライン埋め込み + mermaid.init()"""
        js = self._load_js()
        if not js:
            return
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<pre class="mermaid">stateDiagram-v2
    [*] --> Idle
    Idle --> Active : start
    Active --> [*] : stop</pre>
<script>{js}</script>
<script>
    mermaid.initialize({{ startOnLoad: false, theme: 'default' }});
    mermaid.init(undefined, document.querySelectorAll('.mermaid'));
</script>
</body>
</html>"""
        self.web_view.setHtml(html, QUrl())

    def _pattern_minimal_init(self):
        """パターンD: 最小構成で init()"""
        js = self._load_js()
        if not js:
            return
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<pre class="mermaid">graph TD;
    A-->B;
</pre>
<script>{js}</script>
<script>
    mermaid.initialize({{ startOnLoad: true }});
    mermaid.init(undefined, document.querySelectorAll('.mermaid'));
</script>
</body>
</html>"""
        self.web_view.setHtml(html, QUrl())

    def _pattern_plain_text(self):
        """パターンE: プレーンテキスト表示（デバッグ用）"""
        self.web_view.setHtml("<html><body><h1>Plain Text</h1><pre>mermaidwin.js loading issue?</pre></body></html>", QUrl())

    def _load_js(self) -> str:
        js_path = get_resource_path()
        print(f"[JS PATH] {js_path}")
        print(f"[JS EXISTS] {js_path.exists()}")
        if not js_path.exists():
            return ""
        js = js_path.read_text(encoding="utf-8", errors="ignore")
        print(f"[JS SIZE] {len(js)} chars")
        print(f"[JS FIRST 200] {js[:200]}")
        # エスケープ
        js = js.replace('</script>', '<\\/script>')
        return js


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())