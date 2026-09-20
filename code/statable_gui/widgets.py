# statable_gui/widgets.py
"""StaTable main widget (shared library support / v2.2 entry-exit list)

Version: 3.5 (2026-09-20)
  - MermaidWidget: vertically center the diagram in the viewport.

    [v3.5 change]
      * QScrollArea alignment changed from
          Qt.AlignLeft | Qt.AlignTop
        to
          Qt.AlignLeft | Qt.AlignVCenter
        so that a small (short) diagram appears in the vertical
        middle of the widget. When the diagram is taller than the
        viewport, scrolling takes over and alignment is ignored.

    [v3.4 behavior retained]
      * getSvgSize() returns a JSON string, avoiding PySide6's
        runJavaScript array-to-'' conversion.

    [v3.3 behavior retained]
      * QScrollArea viewport background set to #fafafa (dark-mode fix).
      * json.loads() parses the JSON string form of the size array.

    [v3.2 behavior retained]
      * Only Python triggers rendering (no window.load listener).
      * renderMermaid() awaits mermaid.init / run / polls.
      * Python retries up to 5 times (200 ms apart).
      * JS console.log is forwarded to StaTableLogger.

    [v3.0 change] MAX_SVG_WIDTH raised 1200 -> 3000.

    [v2.8] Persistent debug copy of the generated HTML is retained.

    [v2.2] entry / exit are List[str]; display uses "; " separator.
"""

import os
import json
import shutil
import tempfile
from typing import Optional, List

from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QPalette, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QPlainTextEdit, QSplitter, QLabel, QHeaderView,
    QTabWidget, QAbstractItemView, QMessageBox, QDialog, QScrollArea
)

# ============================================================
# A1: branch WebEngine import itself by environment variable
# ============================================================
_DISABLE_MERMAID = os.environ.get("STATABLE_DISABLE_MERMAID") == "1"

if not _DISABLE_MERMAID:
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWebEngineCore import (
            QWebEngineSettings, QWebEnginePage)
        WEBENGINE_AVAILABLE = True
    except ImportError:
        WEBENGINE_AVAILABLE = False
        QWebEngineView = None
        QWebEngineSettings = None
        QWebEnginePage = None
else:
    WEBENGINE_AVAILABLE = False
    QWebEngineView = None
    QWebEngineSettings = None
    QWebEnginePage = None

from statable.model import State, Event, Transition, StateType, EventKind, RoleFunction
from statable.state_machine import StateMachine
from statable.mermaid_gen import generate_mermaid

from .logger import StaTableLogger
from .config import (
    get_resource_path, TABLE_PREVIEW_RATIO, WINDOW_HEIGHT,
    MERMAID_PREVIEW_MIN_HEIGHT, MAX_COLUMN_WIDTH, MIN_ROW_HEIGHT, MAX_ROW_HEIGHT
)
from .matrix_table import MatrixTableWidget
from .role_function_dialog import RoleFunctionDialog
from .action_edit_dialog import ActionEditDialog
from .global_defs import GlobalDefinitions
from .event_definition_dialog import EventDefinitionDialog

from statable_gui.libcntrl.role_function_library import RoleFunctionLibrary
from statable_gui.libcntrl.condition_library import ConditionLibrary
from statable_gui.libcntrl.literal_library import LiteralLibrary


# ======================================================================
# v2.2: List[str] <-> display helpers for entry / exit
# ======================================================================
_ENTRY_EXIT_SEP = "; "

# [v3.3] Background color shared between the HTML body and the
# QScrollArea viewport, so the empty area around a small diagram
# blends in (important for dark mode).
_MERMAID_BG = "#fafafa"


def _list_to_display(items) -> str:
    """Convert List[str] to a display string ('A; B; C')."""
    if items is None:
        return ""
    if isinstance(items, str):
        return items
    if isinstance(items, list):
        return _ENTRY_EXIT_SEP.join(str(x) for x in items if str(x).strip())
    return str(items)


def _display_to_list(text: str) -> List[str]:
    """Parse a display string ('A; B; C') into List[str]."""
    if not text:
        return []
    if isinstance(text, list):
        return [str(x) for x in text if str(x).strip()]
    parts = str(text).split(';')
    return [p.strip() for p in parts if p.strip()]


# ======================================================================
# [v3.2-debug] Custom page to forward JS console to StaTableLogger
# ======================================================================
if WEBENGINE_AVAILABLE:
    class _DebugWebEnginePage(QWebEnginePage):
        """Forward JS console messages to StaTableLogger."""

        def javaScriptConsoleMessage(self, level, message, line, source):
            try:
                lvl_name = {
                    0: "INFO",
                    1: "WARN",
                    2: "ERROR",
                }.get(int(level), str(level))
            except (TypeError, ValueError):
                lvl_name = str(level)
            StaTableLogger.debug(
                f"[JSConsole:{lvl_name}] {message} "
                f"(line {line}, {os.path.basename(source)})")


class MermaidWidget(QWidget):
    """Mermaid diagram preview widget.

    [v3.5] Diagram vertically centered in the viewport.
      QScrollArea alignment = Qt.AlignLeft | Qt.AlignVCenter.

    [v3.4] getSvgSize() returns a JSON string (reliable across
      PySide6 runJavaScript array-conversion quirks).

    [v3.3] QScrollArea viewport background set to _MERMAID_BG;
      _apply_svg_size parses JSON strings as well as lists.

    [v3.2] Async render (mermaid.init/run + polling) and
      retry-based sizing; JS console forwarded to StaTableLogger.

    [v3.0] MAX_SVG_WIDTH raised 1200 -> 3000.

    [v2.8] Persistent debug copy of the generated HTML is written to
      %USERPROFILE%\\statable_mermaid_debug.html
    """

    MAX_SVG_WIDTH = 3000
    MAX_CONTENT_W = 20000
    MAX_CONTENT_H = 20000
    SIZE_RETRY_MAX = 5
    SIZE_RETRY_DELAY_MS = 200

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web_view = None
        self.text_view = None
        self.scroll_area = None
        self._disabled = (
            os.environ.get("STATABLE_DISABLE_MERMAID") == "1"
        )

        StaTableLogger.debug(
            f"MermaidWidget.__init__: MAX_SVG_WIDTH={self.MAX_SVG_WIDTH}, "
            f"disabled={self._disabled}, webengine_available={WEBENGINE_AVAILABLE}"
        )

        if self._disabled:
            placeholder = QLabel("Mermaid rendering disabled (test mode)")
            placeholder.setAlignment(Qt.AlignCenter)
            layout.addWidget(placeholder)
            StaTableLogger.debug(
                "MermaidWidget: disabled via STATABLE_DISABLE_MERMAID")
            return

        if WEBENGINE_AVAILABLE:
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidgetResizable(False)
            # [v3.5] Vertically center the (small) diagram; horizontal
            # stays left-aligned. When the diagram is larger than the
            # viewport on either axis, scrolling takes over and
            # alignment is ignored on that axis.
            self.scroll_area.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarAsNeeded)
            self.scroll_area.setVerticalScrollBarPolicy(
                Qt.ScrollBarAsNeeded)

            # [v3.3] Viewport background = HTML body color.
            self.scroll_area.viewport().setAutoFillBackground(True)
            pal = self.scroll_area.viewport().palette()
            pal.setColor(QPalette.Window, QColor(_MERMAID_BG))
            self.scroll_area.viewport().setPalette(pal)
            StaTableLogger.debug(
                f"MermaidWidget: scroll_area viewport background set "
                f"to {_MERMAID_BG}")

            self.web_view = QWebEngineView()

            # [v3.2-debug] JS console -> Python log.
            try:
                self.web_view.setPage(_DebugWebEnginePage(self.web_view))
                StaTableLogger.debug(
                    "MermaidWidget: _DebugWebEnginePage attached")
            except Exception as e:
                StaTableLogger.warning(
                    f"Failed to attach debug page: {e}")

            self.web_view.setFixedSize(100, 100)

            try:
                self.web_view.setZoomFactor(1.0)
                StaTableLogger.debug("MermaidWidget: zoomFactor set to 1.0")
            except Exception as e:
                StaTableLogger.warning(f"setZoomFactor failed: {e}")

            settings = self.web_view.settings()
            settings.setAttribute(
                QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(
                QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            self.web_view.loadFinished.connect(self._on_load_finished)

            self.scroll_area.setWidget(self.web_view)
            layout.addWidget(self.scroll_area)
            StaTableLogger.debug(
                "MermaidWidget: WebEngine available + file access enabled "
                "(wrapped in QScrollArea, VCenter alignment)")
        else:
            self.text_view = QPlainTextEdit()
            self.text_view.setReadOnly(True)
            layout.addWidget(self.text_view)
            self.text_view.setPlainText(
                "QWebEngineView is not available.\n"
                "Please install PySide6-Addons.\n"
                "pip install PySide6-Addons"
            )
            StaTableLogger.warning("MermaidWidget: WebEngine NOT available")

    def set_mermaid_code(self, code: str):
        StaTableLogger.debug("MermaidWidget.set_mermaid_code called")
        if self._disabled:
            StaTableLogger.debug(
                "MermaidWidget.set_mermaid_code: skipped (disabled)")
            return

        if self.web_view:
            mermaid_js_path = get_resource_path("mermaidwin.js")
            if not mermaid_js_path.exists():
                StaTableLogger.error(
                    f"mermaidwin.js NOT found: {mermaid_js_path}")
                return

            js_abs_url = QUrl.fromLocalFile(str(mermaid_js_path)).toString()
            StaTableLogger.debug(
                f"MermaidWidget: mermaid.js url = {js_abs_url}")

            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: {_MERMAID_BG};
        }}
        .mermaid {{
            padding: 20px;
            margin: 0;
            background-color: transparent;
            display: inline-block;
            width: max-content;
        }}
    </style>
    <script src="{js_abs_url}"></script>
    <script>
        var MAX_SVG_WIDTH = {self.MAX_SVG_WIDTH};
        console.log('[MermaidDebug] script loaded');
        console.log('[MermaidDebug] MAX_SVG_WIDTH =', MAX_SVG_WIDTH);
        console.log('[MermaidDebug] typeof mermaid =', typeof mermaid);
        if (typeof mermaid !== 'undefined') {{
            console.log('[MermaidDebug] mermaid.run type =',
                        typeof mermaid.run);
            console.log('[MermaidDebug] mermaid.init type =',
                        typeof mermaid.init);
            console.log('[MermaidDebug] mermaid.initialize type =',
                        typeof mermaid.initialize);
        }}

        try {{
            mermaid.initialize({{
                startOnLoad: false,
                theme: 'default',
                themeVariables: {{
                    fontSize: '16px',
                    fontFamily: 'Segoe UI, Yu Gothic UI, sans-serif',
                }},
                'stateDiagram-v2': {{
                    nodeSpacing: 50,
                    rankSpacing: 25,
                    padding: 8,
                    useMaxWidth: false,
                }},
                stateDiagram: {{
                    nodeSpacing: 50,
                    rankSpacing: 25,
                    padding: 8,
                    useMaxWidth: false,
                }},
            }});
            console.log('[MermaidDebug] mermaid.initialize done');
        }} catch (e) {{
            console.error('[MermaidDebug] mermaid.initialize failed:', e);
        }}

        function waitForSvg(timeoutMs) {{
            return new Promise(function(resolve) {{
                var start = Date.now();
                (function poll() {{
                    var svg = document.querySelector('.mermaid svg');
                    if (svg && svg.getAttribute('viewBox')) {{
                        resolve(true);
                        return;
                    }}
                    if (Date.now() - start > timeoutMs) {{
                        resolve(false);
                        return;
                    }}
                    setTimeout(poll, 50);
                }})();
            }});
        }}

        async function renderMermaid() {{
            console.log('[MermaidDebug] renderMermaid: ENTER');

            var nodes = document.querySelectorAll('.mermaid');
            console.log('[MermaidDebug] .mermaid node count =', nodes.length);
            if (!nodes.length) {{
                console.warn('[MermaidDebug] no .mermaid nodes; abort');
                return 'no-nodes';
            }}

            try {{
                var promise = null;
                if (typeof mermaid.run === 'function') {{
                    console.log('[MermaidDebug] branch: mermaid.run');
                    promise = mermaid.run({{ nodes: nodes }});
                }} else if (typeof mermaid.init === 'function') {{
                    console.log('[MermaidDebug] branch: mermaid.init');
                    promise = mermaid.init(undefined, nodes);
                }} else {{
                    console.warn('[MermaidDebug] no run/init available');
                }}

                if (promise && typeof promise.then === 'function') {{
                    console.log('[MermaidDebug] awaiting promise');
                    await promise;
                    console.log('[MermaidDebug] promise resolved');
                }} else {{
                    console.log(
                        '[MermaidDebug] no promise; polling for SVG');
                    var ok = await waitForSvg(3000);
                    console.log('[MermaidDebug] waitForSvg =', ok);
                }}
            }} catch (e) {{
                console.error('[MermaidDebug] render failed:', e);
                console.error('[MermaidDebug] stack:', e && e.stack);
                return 'render-failed';
            }}

            var svgs = document.querySelectorAll('.mermaid svg');
            console.log(
                '[MermaidDebug] SVG count after render =', svgs.length);

            svgs.forEach(function(svg, i) {{
                var vb = svg.getAttribute('viewBox');
                console.log('[MermaidDebug] svg[' + i + '] viewBox =', vb);
                if (!vb) return;
                var parts = vb.split(/\\s+/);
                if (parts.length !== 4) return;
                var w = parseFloat(parts[2]);
                var h = parseFloat(parts[3]);
                if (!w || !h) return;
                var scale = 1.0;
                if (w > MAX_SVG_WIDTH) scale = MAX_SVG_WIDTH / w;
                var newW = Math.round(w * scale);
                var newH = Math.round(h * scale);
                svg.removeAttribute('style');
                svg.setAttribute('width', newW);
                svg.setAttribute('height', newH);
                console.log('[MermaidDebug] svg[' + i +
                            '] forced ' + newW + 'x' + newH +
                            ' (natural ' + w + 'x' + h + ')');
            }});

            console.log('[MermaidDebug] renderMermaid: EXIT');
            return 'ok';
        }}

        /* [v3.4] Returns a JSON string instead of a bare array.
           PySide6's runJavaScript callback sometimes converts JS
           arrays to '' at the Qt boundary; a string is reliable. */
        function getSvgSize() {{
            console.log('[MermaidDebug] getSvgSize: ENTER');
            var svg = document.querySelector('.mermaid svg');
            console.log('[MermaidDebug] getSvgSize: svg exists =', !!svg);
            if (!svg) return JSON.stringify([0, 0]);

            var w = parseFloat(svg.getAttribute('width'));
            var h = parseFloat(svg.getAttribute('height'));
            console.log('[MermaidDebug] getSvgSize: raw width/height =',
                        w, h);

            if (!w || !h) {{
                var vb = svg.getAttribute('viewBox');
                console.log('[MermaidDebug] getSvgSize: viewBox =', vb);
                if (vb) {{
                    var parts = vb.split(/\\s+/);
                    if (parts.length === 4) {{
                        var nw = parseFloat(parts[2]);
                        var nh = parseFloat(parts[3]);
                        var sc = 1.0;
                        if (nw > MAX_SVG_WIDTH) sc = MAX_SVG_WIDTH / nw;
                        w = Math.round(nw * sc);
                        h = Math.round(nh * sc);
                    }}
                }}
            }}

            if (!w || !h) {{
                console.log('[MermaidDebug] getSvgSize: returning [0,0]');
                return JSON.stringify([0, 0]);
            }}

            var pad = 40;
            var result = [Math.round(w + pad), Math.round(h + pad)];
            var jsonStr = JSON.stringify(result);
            console.log('[MermaidDebug] getSvgSize: returning ' + jsonStr);
            return jsonStr;
        }}
    </script>
</head>
<body>
<pre class="mermaid">
{code}
</pre>
<script>
    console.log('[MermaidDebug] body loaded; .mermaid count =',
                document.querySelectorAll('.mermaid').length);
</script>
</body>
</html>"""

            try:
                with tempfile.NamedTemporaryFile(
                        mode='w', suffix='.html',
                        delete=False, encoding='utf-8') as f:
                    f.write(html)
                    temp_path = f.name
                StaTableLogger.debug(
                    f"MermaidWidget: temp HTML written: {temp_path}")

                try:
                    debug_path = os.path.join(
                        os.path.expanduser("~"),
                        "statable_mermaid_debug.html")
                    shutil.copy(temp_path, debug_path)
                    StaTableLogger.info(
                        f"[DEBUG] Mermaid HTML saved to: {debug_path}")
                except Exception as e:
                    StaTableLogger.warning(
                        f"[DEBUG] failed to save debug HTML: {e}")

                self.web_view.load(QUrl.fromLocalFile(temp_path))
                StaTableLogger.debug(
                    f"MermaidWidget: loading URL {temp_path}")
            except Exception as e:
                StaTableLogger.error(
                    f"Failed to create temporary HTML: {e}")
        elif self.text_view:
            self.text_view.setPlainText(code)
            StaTableLogger.debug(
                "MermaidWidget: text fallback updated")

    def _on_load_finished(self, ok: bool):
        StaTableLogger.debug(
            f"MermaidWidget._on_load_finished: ok={ok}")
        if ok and self.web_view:
            StaTableLogger.debug(
                "MermaidWidget: invoking renderMermaid() via JS")
            self.web_view.page().runJavaScript(
                "renderMermaid();",
                lambda r: StaTableLogger.debug(
                    f"renderMermaid() returned: {r!r}"),
            )
            QTimer.singleShot(
                self.SIZE_RETRY_DELAY_MS,
                lambda: self._request_svg_size(retry=0),
            )
        elif not ok:
            StaTableLogger.warning(
                "MermaidWidget: WebEngine load FAILED")

    def _request_svg_size(self, retry: int = 0):
        StaTableLogger.debug(
            f"MermaidWidget._request_svg_size: retry={retry}")
        if not self.web_view:
            StaTableLogger.warning(
                "MermaidWidget._request_svg_size: no web_view")
            return
        self.web_view.page().runJavaScript(
            "getSvgSize();",
            lambda result: self._apply_svg_size(result, retry),
        )

    def _apply_svg_size(self, result, retry: int = 0):
        """[v3.4] Accept JSON string (new) or list/tuple (legacy)."""
        StaTableLogger.debug(
            f"MermaidWidget._apply_svg_size: retry={retry}, "
            f"result={result!r}, type={type(result).__name__}")

        values = None
        if isinstance(result, (list, tuple)) and len(result) >= 2:
            values = result
        elif isinstance(result, str):
            s = result.strip()
            if s:
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, (list, tuple)) and len(parsed) >= 2:
                        values = parsed
                        StaTableLogger.debug(
                            f"MermaidWidget: parsed JSON string -> {values}")
                except (json.JSONDecodeError, ValueError) as e:
                    StaTableLogger.debug(
                        f"MermaidWidget: JSON parse failed: {e}")

        valid = False
        w = h = 0
        if values is not None:
            try:
                w = int(values[0])
                h = int(values[1])
                if w > 0 and h > 0:
                    valid = True
            except (ValueError, TypeError) as e:
                StaTableLogger.warning(
                    f"_apply_svg_size: int() failed: {e}")

        if not valid:
            if retry < self.SIZE_RETRY_MAX:
                next_retry = retry + 1
                StaTableLogger.debug(
                    f"MermaidWidget: size not ready, scheduling retry "
                    f"{next_retry}/{self.SIZE_RETRY_MAX}")
                QTimer.singleShot(
                    self.SIZE_RETRY_DELAY_MS,
                    lambda: self._request_svg_size(retry=next_retry),
                )
            else:
                StaTableLogger.warning(
                    f"MermaidWidget: size query failed after "
                    f"{self.SIZE_RETRY_MAX} retries; keeping current size")
            return

        w = min(w, self.MAX_CONTENT_W)
        h = min(h, self.MAX_CONTENT_H)

        StaTableLogger.debug(
            f"MermaidWidget: setting web_view fixed size to {w}x{h}")
        self.web_view.setFixedSize(w, h)


class SettingsPanel(QWidget):
    """State / role function settings panel.

    [v2.2 change]
      - State.entry / State.exit are List[str].
      - Display format: "; " separated.
      - apply_changes() parses display back to List[str].
    """
    settings_changed = Signal()

    def __init__(self, sm: StateMachine, global_defs: GlobalDefinitions = None, parent=None):
        super().__init__(parent)
        self.sm = sm
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self._updating = False

        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._emit_settings_changed)

        layout = QVBoxLayout(self)
        self.tab = QTabWidget()
        layout.addWidget(self.tab)

        # ---- State tab ----
        state_tab = QWidget()
        state_layout = QVBoxLayout(state_tab)
        self.state_table = QTableWidget(0, 6)
        self.state_table.setHorizontalHeaderLabels([
            "Name", "Description",
            "entry function", "exit function", "do function", "Type"
        ])
        self.state_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.state_table.setFont(QFont("Consolas", 10))
        state_layout.addWidget(self.state_table)
        btn_state = QHBoxLayout()
        add_state_btn = QPushButton("Add")
        add_state_btn.clicked.connect(self.add_state)
        del_state_btn = QPushButton("Delete")
        del_state_btn.clicked.connect(self.delete_state)
        btn_state.addWidget(add_state_btn)
        btn_state.addWidget(del_state_btn)
        state_layout.addLayout(btn_state)
        self.tab.addTab(state_tab, "State list")

        # ---- Role function tab ----
        role_tab = QWidget()
        role_layout = QVBoxLayout(role_tab)
        self.role_table = QTableWidget(0, 9)
        self.role_table.setHorizontalHeaderLabels([
            "Title", "Function name", "Namespace", "Description", "Return type",
            "Arg 1 type", "Arg 1 name", "Arg 2 type", "Arg 2 name"
        ])
        self.role_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.role_table.setFont(QFont("Consolas", 10))
        role_layout.addWidget(self.role_table)
        btn_role = QHBoxLayout()
        add_role_btn = QPushButton("Add")
        add_role_btn.clicked.connect(self.add_role_function)
        del_role_btn = QPushButton("Delete")
        del_role_btn.clicked.connect(self.delete_role_function)
        btn_role.addWidget(add_role_btn)
        btn_role.addWidget(del_role_btn)
        role_layout.addLayout(btn_role)

        event_btn = QPushButton("Event definitions...")
        event_btn.clicked.connect(self.open_event_definition)
        role_layout.addWidget(event_btn)

        self.tab.addTab(role_tab, "Role function")

        self.state_table.itemChanged.connect(self.on_state_table_item_changed)
        self.role_table.itemChanged.connect(self.on_role_table_item_changed)
        self.state_table.cellDoubleClicked.connect(
            self.on_state_table_cell_double_clicked)

        self.populate()
        StaTableLogger.debug("SettingsPanel initialized")

    def _emit_settings_changed(self):
        if not self._updating:
            self.settings_changed.emit()

    def populate(self):
        self._updating = True

        states = list(self.sm.states.values())
        self.state_table.setRowCount(len(states))
        for row, state in enumerate(states):
            self.state_table.setItem(row, 0, QTableWidgetItem(state.name))
            self.state_table.setItem(row, 1, QTableWidgetItem(state.description))

            entry_display = _list_to_display(getattr(state, 'entry', []))
            exit_display = _list_to_display(getattr(state, 'exit', []))

            entry_item = QTableWidgetItem(entry_display)
            entry_item.setToolTip(
                "Multiple functions: separate with '; '\n"
                "Double-click to edit via action dialog")
            self.state_table.setItem(row, 2, entry_item)

            exit_item = QTableWidgetItem(exit_display)
            exit_item.setToolTip(
                "Multiple functions: separate with '; '\n"
                "Double-click to edit via action dialog")
            self.state_table.setItem(row, 3, exit_item)

            do_item = QTableWidgetItem(state.do)
            do_item.setToolTip("Double-click to edit")
            self.state_table.setItem(row, 4, do_item)

            self.state_table.setItem(row, 5, QTableWidgetItem(state.type.value))

        self.populate_role_table()

        self._updating = False
        StaTableLogger.debug(
            f"Settings populated: {len(states)} states, "
            f"{len(self.sm.role_functions)} roles")

    def populate_role_table(self):
        roles = list(self.sm.role_functions.values())
        self.role_table.setRowCount(len(roles))
        for row, rf in enumerate(roles):
            self.role_table.setItem(row, 0, QTableWidgetItem(rf.title))
            self.role_table.setItem(row, 1, QTableWidgetItem(rf.name))
            self.role_table.setItem(row, 2, QTableWidgetItem(rf.namespace))
            self.role_table.setItem(row, 3, QTableWidgetItem(rf.description))
            self.role_table.setItem(row, 4, QTableWidgetItem(rf.return_type))
            self.role_table.setItem(row, 5, QTableWidgetItem(rf.arg1_type))
            self.role_table.setItem(row, 6, QTableWidgetItem(rf.arg1_name))
            self.role_table.setItem(row, 7, QTableWidgetItem(rf.arg2_type))
            self.role_table.setItem(row, 8, QTableWidgetItem(rf.arg2_name))

    def on_state_table_cell_double_clicked(self, row, col):
        StaTableLogger.debug(
            f"SettingsPanel.on_state_table_cell_double_clicked: row={row}, col={col}")
        if col not in (2, 3, 4):
            return

        item = self.state_table.item(row, col)
        current_text = item.text() if item else ""

        dlg = ActionEditDialog(
            self,
            action_text=current_text,
            role_functions=self.sm.role_functions,
            global_defs=self.global_defs
        )
        if dlg.exec() == QDialog.Accepted:
            new_text = dlg.get_action_text()
            if item:
                item.setText(new_text)
            else:
                item = QTableWidgetItem(new_text)
                self.state_table.setItem(row, col, item)
            self.settings_changed.emit()

    def add_state(self):
        row = self.state_table.rowCount()
        self.state_table.insertRow(row)
        for col, default in enumerate(["", "", "", "", "", "normal"]):
            self.state_table.setItem(row, col, QTableWidgetItem(default))
        self.state_table.editItem(self.state_table.item(row, 0))
        StaTableLogger.debug("Add state row")

    def delete_state(self):
        row = self.state_table.currentRow()
        if row >= 0:
            name = (self.state_table.item(row, 0).text().strip()
                    if self.state_table.item(row, 0) else "")
            if name and name in self.sm.states:
                self.sm.transitions = [
                    t for t in self.sm.transitions
                    if t.source != name and t.target != name
                ]
                for (src, evt) in list(self.sm.get_cell_keys()):
                    if src == name:
                        self.sm.remove_cell_metadata(src, evt)
                del self.sm.states[name]
                self.populate()
                self.settings_changed.emit()
                StaTableLogger.info(f"State deleted: {name}")
            else:
                self.state_table.removeRow(row)

    def open_event_definition(self):
        StaTableLogger.debug("SettingsPanel.open_event_definition called")
        dlg = EventDefinitionDialog(self.sm, self.global_defs, self)
        if dlg.exec() == QDialog.Accepted:
            self.settings_changed.emit()
            StaTableLogger.info("Event definitions updated")

    def add_role_function(self):
        StaTableLogger.debug("SettingsPanel.add_role_function called")
        dlg = RoleFunctionDialog(self)
        if dlg.exec() == QDialog.Accepted:
            rf = dlg.get_role_function()
            if rf.name in self.sm.role_functions:
                QMessageBox.warning(
                    self, "Warning",
                    "A role function with the same name already exists.")
                return
            self.sm.add_role_function(rf)
            self.populate_role_table()
            self.settings_changed.emit()

    def delete_role_function(self):
        row = self.role_table.currentRow()
        if row >= 0:
            name = (self.role_table.item(row, 1).text().strip()
                    if self.role_table.item(row, 1) else "")
            if name and name in self.sm.role_functions:
                self.sm.remove_role_function(name)
                self.populate_role_table()
                self.settings_changed.emit()
                StaTableLogger.info(f"Role function deleted: {name}")
            else:
                self.role_table.removeRow(row)

    def on_state_table_item_changed(self, item):
        self._debounce_timer.start()

    def on_role_table_item_changed(self, item):
        self._debounce_timer.start()

    def apply_changes(self):
        """Apply the UI edits back into the StateMachine.

        [v2.2]
          entry / exit: display string -> List[str] via split(';')
        """
        for row in range(self.state_table.rowCount()):
            name = (self.state_table.item(row, 0).text().strip()
                    if self.state_table.item(row, 0) else "")
            desc = (self.state_table.item(row, 1).text().strip()
                    if self.state_table.item(row, 1) else "")

            entry_text = (self.state_table.item(row, 2).text().strip()
                          if self.state_table.item(row, 2) else "")
            exit_text = (self.state_table.item(row, 3).text().strip()
                         if self.state_table.item(row, 3) else "")
            entry_list = _display_to_list(entry_text)
            exit_list = _display_to_list(exit_text)

            do = (self.state_table.item(row, 4).text().strip()
                  if self.state_table.item(row, 4) else "")
            type_str = (self.state_table.item(row, 5).text().strip()
                        if self.state_table.item(row, 5) else "normal")

            if name:
                if name in self.sm.states:
                    st = self.sm.states[name]
                    st.description = desc
                    st.entry = entry_list
                    st.exit = exit_list
                    st.do = do
                    st.type = StateType(type_str)
                else:
                    self.sm.add_state(State(
                        name, type=StateType(type_str), description=desc,
                        entry=entry_list, exit=exit_list, do=do,
                    ))

        self.sm.role_functions.clear()
        for row in range(self.role_table.rowCount()):
            title = (self.role_table.item(row, 0).text().strip()
                     if self.role_table.item(row, 0) else "")
            name = (self.role_table.item(row, 1).text().strip()
                    if self.role_table.item(row, 1) else "")
            if name:
                namespace = (self.role_table.item(row, 2).text().strip()
                             if self.role_table.item(row, 2) else "")
                desc = (self.role_table.item(row, 3).text().strip()
                        if self.role_table.item(row, 3) else "")
                ret = (self.role_table.item(row, 4).text().strip()
                       if self.role_table.item(row, 4) else "int")
                a1t = (self.role_table.item(row, 5).text().strip()
                       if self.role_table.item(row, 5) else "int")
                a1n = (self.role_table.item(row, 6).text().strip()
                       if self.role_table.item(row, 6) else "arg1")
                a2t = (self.role_table.item(row, 7).text().strip()
                       if self.role_table.item(row, 7) else "int")
                a2n = (self.role_table.item(row, 8).text().strip()
                       if self.role_table.item(row, 8) else "arg2")

                self.sm.add_role_function(RoleFunction(
                    name=name,
                    namespace=namespace,
                    description=desc,
                    return_type=ret,
                    arg1_type=a1t,
                    arg1_name=a1n,
                    arg2_type=a2t,
                    arg2_name=a2n,
                    title=title,
                ))
        StaTableLogger.debug("Settings changes applied")


class StateMachineTab(QWidget):
    def __init__(self, sm: StateMachine, global_defs: GlobalDefinitions = None,
                 role_function_library: RoleFunctionLibrary = None,
                 condition_library: ConditionLibrary = None,
                 literal_library: LiteralLibrary = None,
                 parent=None):
        super().__init__(parent)
        self.sm = sm
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        self.role_function_library = role_function_library if role_function_library else RoleFunctionLibrary()
        self.condition_library = condition_library if condition_library else ConditionLibrary()
        self.literal_library = literal_library if literal_library else LiteralLibrary()

        StaTableLogger.debug(
            f"StateMachineTab.__init__: global_defs id={id(self.global_defs)}, "
            f"vars={len(self.global_defs.variables)}, flags={len(self.global_defs.flags)}"
        )
        StaTableLogger.debug(
            f"StateMachineTab shared libraries: "
            f"roles={len(self.role_function_library.list_all())}, "
            f"conditions={len(self.condition_library.list_all())}, "
            f"literals={len(self.literal_library.list_all())}"
        )

        layout = QHBoxLayout(self)

        left_split = QSplitter(Qt.Vertical)
        self.table = MatrixTableWidget(
            sm,
            global_defs=self.global_defs,
            role_function_library=self.role_function_library,
            condition_library=self.condition_library,
            literal_library=self.literal_library
        )
        self.mermaid = MermaidWidget()
        left_split.addWidget(self.table)
        left_split.addWidget(self.mermaid)

        total_height = WINDOW_HEIGHT
        table_height = int(total_height * TABLE_PREVIEW_RATIO)
        mermaid_height = total_height - table_height
        left_split.setSizes([table_height, mermaid_height])

        self.table.setMinimumHeight(300)
        self.mermaid.setMinimumHeight(MERMAID_PREVIEW_MIN_HEIGHT)

        layout.addWidget(left_split, stretch=3)

        self.settings = SettingsPanel(sm, global_defs=self.global_defs)
        layout.addWidget(self.settings, stretch=1)

        self.table.transition_changed.connect(self.update_mermaid)
        self.settings.settings_changed.connect(self.update_mermaid)

        self.update_mermaid()
        StaTableLogger.debug("StateMachineTab created")

    def update_mermaid(self):
        self.settings.apply_changes()
        self.table.populate()
        code = generate_mermaid(self.sm)
        self.mermaid.set_mermaid_code(code)
        StaTableLogger.info("Mermaid updated for current tab")