# statable_gui/widgets.py
"""StaTable main widget (shared library support / v2.2 entry-exit list)

Version: 3.11 (2026-09-22)
  - [C-38 fix] SettingsPanel.add_state() now emits settings_changed
      so that the window's modified flag ([*]) updates when a state
      is added.

  - [v3.11] Namespace combo box: full project-wide candidates.
      * SettingsPanel now accepts `layer_names_provider`, a
        zero-argument callable returning every tab name (= every
        layer name) in the project.
      * StateMachineTab forwards `layer_names_provider` to
        SettingsPanel.
      * _get_namespace_choices() merges candidates from:
          1. layer_names_provider  (all tabs: Application, Driver, ...)
          2. sm.layer_name         (current tab, in case provider
                                    is not supplied)
          3. role_function_library namespaces
          4. sm.role_functions namespaces
        Deduplicated while preserving order, so the inline combo
        box and RoleFunctionDialog show the same complete list.

    [v3.10 behavior retained]
      * Role function table: inline editing restricted to the
        Namespace column (editable QComboBox delegate).
        Title / Function name / Description are read-only there.
      * _NamespaceDelegate uses _get_namespace_choices() on every
        editor creation, so the candidate list stays fresh.

    [v3.9 behavior retained]
      * SettingsPanel receives role_function_library and
        literal_library from StateMachineTab.
      * RoleFunctionDialog renders namespace as an editable
        QComboBox populated with candidates.

    [v3.8 behavior retained]
      * "Edit" button + row double-click for role functions.
      * used_global_vars / used_events / used_literals persisted.
      * apply_changes() uses getattr(...) for defensive access.

    [v3.7 behavior retained]
      * State list:    6 -> 5 columns (removed "do function").
      * Role function: 9 -> 4 columns (removed "Return type",
        "Arg 1 type", "Arg 1 name", "Arg 2 type", "Arg 2 name").
      * StateMachineTab: QSplitter(Qt.Horizontal).
      * apply_changes() carries reserved values forward.

    [v3.6 behavior retained]
      * SettingsPanel: entry / exit columns are non-editable
        inline (edited via ActionEditDialog).
    [v3.5 behavior retained]
      * MermaidWidget: QScrollArea alignment VCenter.
    [v3.4 behavior retained]
      * getSvgSize() returns a JSON string.
    [v3.3 behavior retained]
      * QScrollArea viewport background #fafafa.
    [v3.2 behavior retained]
      * Async render; JS console forwarded to StaTableLogger.
    [v3.0] MAX_SVG_WIDTH 1200 -> 3000.
    [v2.8] Persistent debug copy retained.
    [v2.2] entry / exit are List[str]; "; " separator.

[v2.3 change]
  - StateMachineTab: dataModified signal relays child modifications
    to MainWindow (for the [*] window-modified marker).
"""

import os
import json
import shutil
import tempfile
from typing import Optional, List, Callable

from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QPalette, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QPlainTextEdit, QSplitter, QLabel, QHeaderView,
    QTabWidget, QAbstractItemView, QMessageBox, QDialog, QScrollArea,
    QComboBox, QStyledItemDelegate
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


# ======================================================================
# [v3.10] Namespace column delegate (editable QComboBox)
# ======================================================================
class _NamespaceDelegate(QStyledItemDelegate):
    """Inline editor for the Role-function Namespace column.

    [v3.10]
      Renders an editable QComboBox populated with the current
      namespace candidates (supplied by `choices_provider`). The
      user can either pick a candidate or type a custom value.

    [v3.11]
      `choices_provider` is re-evaluated on every editor creation,
      so newly added layers / namespaces appear immediately.
    """

    def __init__(self, choices_provider, parent=None):
        super().__init__(parent)
        self._choices_provider = choices_provider

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        # First entry: empty namespace (no layer)
        combo.addItem("")
        try:
            for ns in (self._choices_provider() or []):
                ns = (ns or "").strip()
                if ns and combo.findText(ns) < 0:
                    combo.addItem(ns)
        except Exception as e:
            StaTableLogger.warning(
                f"_NamespaceDelegate.choices_provider failed: {e}")
        return combo

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole) or ""
        value = str(value)
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)
        else:
            editor.setEditText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText().strip(), Qt.EditRole)


class MermaidWidget(QWidget):
    """Mermaid diagram preview widget.

    [v3.5] Diagram vertically centered in the viewport.
      QScrollArea alignment = Qt.AlignLeft | Qt.AlignVCenter.

    [v3.4] getSvgSize() returns a JSON string.

    [v3.3] QScrollArea viewport background set to _MERMAID_BG.

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
            self.scroll_area.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarAsNeeded)
            self.scroll_area.setVerticalScrollBarPolicy(
                Qt.ScrollBarAsNeeded)

            self.scroll_area.viewport().setAutoFillBackground(True)
            pal = self.scroll_area.viewport().palette()
            pal.setColor(QPalette.Window, QColor(_MERMAID_BG))
            self.scroll_area.viewport().setPalette(pal)

            self.web_view = QWebEngineView()

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
            return

        if self.web_view:
            mermaid_js_path = get_resource_path("mermaidwin.js")
            if not mermaid_js_path.exists():
                StaTableLogger.error(
                    f"mermaidwin.js NOT found: {mermaid_js_path}")
                return

            js_abs_url = QUrl.fromLocalFile(str(mermaid_js_path)).toString()

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
            except Exception as e:
                StaTableLogger.error(
                    f"Failed to create temporary HTML: {e}")
        elif self.text_view:
            self.text_view.setPlainText(code)

    def _on_load_finished(self, ok: bool):
        StaTableLogger.debug(
            f"MermaidWidget._on_load_finished: ok={ok}")
        if ok and self.web_view:
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
            return
        self.web_view.page().runJavaScript(
            "getSvgSize();",
            lambda result: self._apply_svg_size(result, retry),
        )

    def _apply_svg_size(self, result, retry: int = 0):
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
                except (json.JSONDecodeError, ValueError):
                    pass

        valid = False
        w = h = 0
        if values is not None:
            try:
                w = int(values[0])
                h = int(values[1])
                if w > 0 and h > 0:
                    valid = True
            except (ValueError, TypeError):
                pass

        if not valid:
            if retry < self.SIZE_RETRY_MAX:
                next_retry = retry + 1
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
        self.web_view.setFixedSize(w, h)


class SettingsPanel(QWidget):
    """State / role function settings panel.

    [C-38 fix]
      add_state() now emits settings_changed so that the parent
      StateMachineTab / MainWindow updated the window's modified
      flag when a state is added.

    [v3.11]
      Accepts `layer_names_provider`, a zero-argument callable that
      returns all tab names (all layer names in the project). It is
      used by _get_namespace_choices() to populate the namespace
      combo box with every layer, not just the current one.

    [v3.10]
      Role function table: only the Namespace column is editable
      inline (via _NamespaceDelegate).

    [v3.9]
      Receives role_function_library and literal_library.

    [v3.8]
      "Edit" button + row double-click for role functions.

    [v3.7]
      State list: 5 columns. Role function: 4 columns.
      Reserved fields carried forward in apply_changes().
    """
    settings_changed = Signal()

    # Columns whose items are edited via ActionEditDialog (not inline).
    # State list layout: 0=Name, 1=Description, 2=entry, 3=exit, 4=Type
    NON_INLINE_EDIT_COLS = (2, 3)

    # [v3.10] Role-function table layout: 0=Title, 1=Function name,
    #         2=Namespace, 3=Description. Only column 2 is editable.
    ROLE_NAMESPACE_COL = 2

    def __init__(self, sm: StateMachine,
                 global_defs: GlobalDefinitions = None,
                 literal_library: LiteralLibrary = None,
                 role_function_library: RoleFunctionLibrary = None,
                 layer_names_provider: Callable[[], List[str]] = None,
                 parent=None):
        super().__init__(parent)
        self.sm = sm
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.literal_library = literal_library
        self.role_function_library = role_function_library
        # [v3.11] Callable returning all tab names (= all layer names)
        self.layer_names_provider = layer_names_provider
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
        self.state_table = QTableWidget(0, 5)
        self.state_table.setHorizontalHeaderLabels([
            "Name", "Description",
            "entry function", "exit function", "Type"
        ])
        self.state_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
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
        self.role_table = QTableWidget(0, 4)
        self.role_table.setHorizontalHeaderLabels([
            "Title", "Function name", "Namespace", "Description"
        ])
        self.role_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.role_table.setFont(QFont("Consolas", 10))

        # [v3.10] Namespace column: editable QComboBox delegate.
        self._namespace_delegate = _NamespaceDelegate(
            self._get_namespace_choices, self.role_table)
        self.role_table.setItemDelegateForColumn(
            self.ROLE_NAMESPACE_COL, self._namespace_delegate)

        role_layout.addWidget(self.role_table)
        btn_role = QHBoxLayout()
        add_role_btn = QPushButton("Add")
        add_role_btn.clicked.connect(self.add_role_function)
        edit_role_btn = QPushButton("Edit")
        edit_role_btn.clicked.connect(self.edit_role_function)
        del_role_btn = QPushButton("Delete")
        del_role_btn.clicked.connect(self.delete_role_function)
        btn_role.addWidget(add_role_btn)
        btn_role.addWidget(edit_role_btn)
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
        self.role_table.cellDoubleClicked.connect(
            self.on_role_table_cell_double_clicked)

        self.populate()
        StaTableLogger.debug("SettingsPanel initialized")

    def _emit_settings_changed(self):
        if not self._updating:
            self.settings_changed.emit()

    @staticmethod
    def _make_state_item(text: str, col: int) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if col in SettingsPanel.NON_INLINE_EDIT_COLS:
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    # ------------------------------------------------------------------
    # Namespace choices provider (shared by delegate + dialog)
    # ------------------------------------------------------------------
    def _get_namespace_choices(self) -> List[str]:
        """Return namespace candidates (deduped, order preserved).

        [v3.11]
          Candidates come from (in order):
            1. layer_names_provider    (all tabs: Application, Driver,
                                        Middleware, ...)
            2. self.sm.layer_name      (current tab, in case provider
                                        is unavailable)
            3. role_function_library   (shared library)
            4. sm.role_functions       (this StateMachine)

          Used both by the inline namespace combo-box delegate and
          by _role_function_dialog_kwargs() for RoleFunctionDialog,
          so both show the same complete list.
        """
        ordered: List[str] = []

        def _add(ns):
            ns = (ns or "").strip()
            if ns and ns not in ordered:
                ordered.append(ns)

        # 1. All tab names (= all layer names in the project)
        if self.layer_names_provider is not None:
            try:
                for name in self.layer_names_provider():
                    _add(name)
            except Exception as e:
                StaTableLogger.warning(
                    f"layer_names_provider failed: {e}")

        # 2. Current tab's layer name (fallback)
        _add(getattr(self.sm, 'layer_name', ''))

        # 3. Shared library namespaces
        if self.role_function_library is not None:
            try:
                for rf in self.role_function_library.list_all():
                    _add(getattr(rf, 'namespace', ''))
            except Exception as e:
                StaTableLogger.warning(
                    f"role_function_library.list_all() failed: {e}")

        # 4. Namespaces used in this StateMachine
        for rf in self.sm.role_functions.values():
            _add(getattr(rf, 'namespace', ''))

        return ordered

    # ------------------------------------------------------------------
    # Populate
    # ------------------------------------------------------------------
    def populate(self):
        self._updating = True

        states = list(self.sm.states.values())
        self.state_table.setRowCount(len(states))
        for row, state in enumerate(states):
            self.state_table.setItem(row, 0, QTableWidgetItem(state.name))
            self.state_table.setItem(row, 1, QTableWidgetItem(state.description))

            entry_display = _list_to_display(getattr(state, 'entry', []))
            exit_display = _list_to_display(getattr(state, 'exit', []))

            entry_item = self._make_state_item(entry_display, 2)
            entry_item.setToolTip(
                "Multiple functions: separate with '; '\n"
                "Double-click to edit via action dialog")
            self.state_table.setItem(row, 2, entry_item)

            exit_item = self._make_state_item(exit_display, 3)
            exit_item.setToolTip(
                "Multiple functions: separate with '; '\n"
                "Double-click to edit via action dialog")
            self.state_table.setItem(row, 3, exit_item)

            self.state_table.setItem(row, 4, QTableWidgetItem(state.type.value))

        self.populate_role_table()

        self._updating = False
        StaTableLogger.debug(
            f"Settings populated: {len(states)} states, "
            f"{len(self.sm.role_functions)} roles")

    def populate_role_table(self):
        """Refresh the role function table.

        [v3.10]
          Only the Namespace column is editable inline.
        """
        roles = list(self.sm.role_functions.values())
        self.role_table.setRowCount(len(roles))
        for row, rf in enumerate(roles):
            values = [rf.title, rf.name, rf.namespace, rf.description]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                if col != self.ROLE_NAMESPACE_COL:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.role_table.setItem(row, col, item)

    # ------------------------------------------------------------------
    # State editing
    # ------------------------------------------------------------------
    def on_state_table_cell_double_clicked(self, row, col):
        StaTableLogger.debug(
            f"SettingsPanel.on_state_table_cell_double_clicked: "
            f"row={row}, col={col}")
        if col not in (2, 3):
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
                item = self._make_state_item(new_text, col)
                self.state_table.setItem(row, col, item)
            self.settings_changed.emit()

    def add_state(self):
        row = self.state_table.rowCount()
        self.state_table.insertRow(row)
        defaults = ["", "", "", "", "normal"]
        for col, default in enumerate(defaults):
            self.state_table.setItem(
                row, col, self._make_state_item(default, col))
        self.state_table.editItem(self.state_table.item(row, 0))
        # [C-38 fix] Notify listeners that a state was added
        self.settings_changed.emit()
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

    # ------------------------------------------------------------------
    # Role function dialog helpers
    # ------------------------------------------------------------------
    def _role_function_dialog_kwargs(self):
        """Build kwargs for RoleFunctionDialog."""
        global_vars = [
            getattr(v, 'name', '') for v in
            (getattr(self.global_defs, 'variables', []) or [])
            if getattr(v, 'name', '')
        ]

        events = [
            getattr(e, 'name', '') for e in self.sm.events.values()
            if getattr(e, 'name', '')
        ]

        literals = []
        if self.literal_library is not None:
            try:
                literals = [
                    getattr(lit, 'name', '')
                    for lit in self.literal_library.list_all()
                    if getattr(lit, 'name', '')
                ]
            except Exception as e:
                StaTableLogger.warning(
                    f"literal_library.list_all() failed: {e}")

        return dict(
            global_vars=global_vars,
            events=events,
            literals=literals,
            namespace_choices=self._get_namespace_choices(),
        )

    def add_role_function(self):
        StaTableLogger.debug("SettingsPanel.add_role_function called")
        dlg = RoleFunctionDialog(
            self, **self._role_function_dialog_kwargs())
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

    def edit_role_function(self):
        row = self.role_table.currentRow()
        if row < 0:
            StaTableLogger.debug("edit_role_function: no row selected")
            return

        name = (self.role_table.item(row, 1).text().strip()
                if self.role_table.item(row, 1) else "")
        if not name or name not in self.sm.role_functions:
            StaTableLogger.debug(
                f"edit_role_function: unknown name '{name}'")
            return

        existing = self.sm.role_functions[name]
        dlg = RoleFunctionDialog(
            self,
            role_function=existing,
            **self._role_function_dialog_kwargs(),
        )
        if dlg.exec() != QDialog.Accepted:
            return

        updated = dlg.get_role_function()

        if updated.name != name and updated.name in self.sm.role_functions:
            QMessageBox.warning(
                self, "Warning",
                "A role function with the same name already exists.")
            return

        self.sm.remove_role_function(name)
        self.sm.add_role_function(updated)
        self.populate_role_table()
        self.settings_changed.emit()
        StaTableLogger.info(
            f"Role function updated: '{name}' -> '{updated.name}'")

    def on_role_table_cell_double_clicked(self, row, col):
        """Row double-click handler.

        [v3.10]
          If the Namespace column was double-clicked, the inline
          combo-box delegate handles it; do not open the dialog.
        """
        StaTableLogger.debug(
            f"SettingsPanel.on_role_table_cell_double_clicked: "
            f"row={row}, col={col}")

        if col == self.ROLE_NAMESPACE_COL:
            return

        self.role_table.selectRow(row)
        self.edit_role_function()

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

        [v3.10]
          The Namespace column may have been edited inline via the
          combo-box delegate. This method picks up the change and
          rebuilds the role functions accordingly.
        """
        # ---- States ----
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

            type_str = (self.state_table.item(row, 4).text().strip()
                        if self.state_table.item(row, 4) else "normal")

            if name:
                if name in self.sm.states:
                    st = self.sm.states[name]
                    st.description = desc
                    st.entry = entry_list
                    st.exit = exit_list
                    try:
                        st.type = StateType(type_str)
                    except ValueError:
                        st.type = StateType.NORMAL
                else:
                    self.sm.add_state(State(
                        name, type=StateType(type_str), description=desc,
                        entry=entry_list, exit=exit_list,
                    ))

        # ---- Role functions ----
        existing_roles = dict(self.sm.role_functions)
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

                prev = existing_roles.get(name)
                self.sm.add_role_function(RoleFunction(
                    name=name,
                    namespace=namespace,
                    description=desc,
                    title=title,
                    # [Reserved] carry forward previous values
                    return_type=(
                        getattr(prev, 'return_type', 'void')
                        if prev else "void"),
                    arg1_type=(
                        getattr(prev, 'arg1_type', '') if prev else ""),
                    arg1_name=(
                        getattr(prev, 'arg1_name', '') if prev else ""),
                    arg2_type=(
                        getattr(prev, 'arg2_type', '') if prev else ""),
                    arg2_name=(
                        getattr(prev, 'arg2_name', '') if prev else ""),
                    # [v3.8] carry forward symbol references
                    used_global_vars=list(
                        getattr(prev, 'used_global_vars', []) or []
                    ) if prev else [],
                    used_events=list(
                        getattr(prev, 'used_events', []) or []
                    ) if prev else [],
                    used_literals=list(
                        getattr(prev, 'used_literals', []) or []
                    ) if prev else [],
                ))
        StaTableLogger.debug("Settings changes applied")


class StateMachineTab(QWidget):
    """Tab hosting one state machine (matrix + mermaid + settings).

    [v3.11]
      Accepts and forwards `layer_names_provider` to SettingsPanel.

    [v3.9]
      Passes role_function_library and literal_library to SettingsPanel.

    [v3.7 change]
      Layout: QSplitter(Qt.Horizontal).

    [v2.3 change]
      dataModified signal relays child modifications to MainWindow.
    """

    dataModified = Signal()

    SETTINGS_MIN_WIDTH = 260
    SETTINGS_MAX_WIDTH = 560

    def __init__(self, sm: StateMachine,
                 global_defs: GlobalDefinitions = None,
                 role_function_library: RoleFunctionLibrary = None,
                 condition_library: ConditionLibrary = None,
                 literal_library: LiteralLibrary = None,
                 layer_names_provider: Callable[[], List[str]] = None,
                 parent=None):
        super().__init__(parent)
        self.sm = sm
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        self.role_function_library = (
            role_function_library if role_function_library
            else RoleFunctionLibrary())
        self.condition_library = (
            condition_library if condition_library
            else ConditionLibrary())
        self.literal_library = (
            literal_library if literal_library
            else LiteralLibrary())
        # [v3.11] forwarded to SettingsPanel
        self.layer_names_provider = layer_names_provider

        StaTableLogger.debug(
            f"StateMachineTab.__init__: global_defs id={id(self.global_defs)}, "
            f"vars={len(self.global_defs.variables)}, "
            f"flags={len(self.global_defs.flags)}"
        )
        StaTableLogger.debug(
            f"StateMachineTab shared libraries: "
            f"roles={len(self.role_function_library.list_all())}, "
            f"conditions={len(self.condition_library.list_all())}, "
            f"literals={len(self.literal_library.list_all())}"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        main_split = QSplitter(Qt.Horizontal)
        main_split.setChildrenCollapsible(False)

        left_split = QSplitter(Qt.Vertical)
        # [R-6] Forward layer_names_provider to MatrixTableWidget so
        #       that ActionEditorDialog / TransitionsTab / ActionsTab
        #       can list every layer in the project.
        self.table = MatrixTableWidget(
            sm,
            global_defs=self.global_defs,
            role_function_library=self.role_function_library,
            condition_library=self.condition_library,
            literal_library=self.literal_library,
            layer_names_provider=self.layer_names_provider,
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

        main_split.addWidget(left_split)

        # [v3.11] Forward layer_names_provider to SettingsPanel.
        self.settings = SettingsPanel(
            sm,
            global_defs=self.global_defs,
            literal_library=self.literal_library,
            role_function_library=self.role_function_library,
            layer_names_provider=self.layer_names_provider,
        )
        self.settings.setMinimumWidth(self.SETTINGS_MIN_WIDTH)
        self.settings.setMaximumWidth(self.SETTINGS_MAX_WIDTH)

        main_split.addWidget(self.settings)

        main_split.setStretchFactor(0, 4)
        main_split.setStretchFactor(1, 1)
        main_split.setSizes([WINDOW_HEIGHT, self.SETTINGS_MIN_WIDTH])

        outer.addWidget(main_split)

        self.table.transition_changed.connect(self.update_mermaid)
        self.settings.settings_changed.connect(self.update_mermaid)

        self.table.transition_changed.connect(self.dataModified)
        self.settings.settings_changed.connect(self.dataModified)

        self.update_mermaid()
        StaTableLogger.debug("StateMachineTab created")

    def update_mermaid(self):
        self.settings.apply_changes()
        self.table.populate()
        code = generate_mermaid(self.sm)
        self.mermaid.set_mermaid_code(code)
        StaTableLogger.info("Mermaid updated for current tab")