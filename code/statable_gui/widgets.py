import tempfile
from typing import Optional, List

from PySide6.QtCore import Qt, Signal, QUrl, QTimer
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QPlainTextEdit, QSplitter, QLabel, QHeaderView,
    QTabWidget, QAbstractItemView, QMessageBox, QDialog
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

from statable.model import State, Event, Transition, StateType, EventKind, RoleFunction
from statable.state_machine import StateMachine
from statable.mermaid_gen import generate_mermaid

from .logger import StaTableLogger
from .config import (
    get_resource_path, TABLE_PREVIEW_RATIO, WINDOW_HEIGHT,
    MERMAID_PREVIEW_MIN_HEIGHT, MAX_COLUMN_WIDTH, MIN_ROW_HEIGHT, MAX_ROW_HEIGHT
)
from .matrix_table import MatrixTableWidget
from .dialogs import TransitionListDialog
from .role_function_dialog import RoleFunctionDialog
from .action_edit_dialog import ActionEditDialog
from .global_defs import GlobalDefinitions


# ----------------------------------------------------------------------
# Mermaidプレビューウィジェット
# ----------------------------------------------------------------------
class MermaidWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.web_view = None
        self.text_view = None

        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            self.web_view.loadFinished.connect(self._on_load_finished)
            layout.addWidget(self.web_view)
            StaTableLogger.debug("MermaidWidget: WebEngine available + file access enabled")
        else:
            self.text_view = QPlainTextEdit()
            self.text_view.setReadOnly(True)
            layout.addWidget(self.text_view)
            self.text_view.setPlainText(
                "QWebEngineViewが利用できません。\n"
                "PySide6-Addonsをインストールしてください。\n"
                "pip install PySide6-Addons"
            )
            StaTableLogger.warning("MermaidWidget: WebEngine NOT available")

    def set_mermaid_code(self, code: str):
        StaTableLogger.debug("MermaidWidget.set_mermaid_code called")
        StaTableLogger.debug(f"Mermaid code:\n{code}")

        if self.web_view:
            mermaid_js_path = get_resource_path("mermaidwin.js")
            if not mermaid_js_path.exists():
                StaTableLogger.error(f"mermaidwin.js NOT found: {mermaid_js_path}")
                return

            js_abs_url = QUrl.fromLocalFile(str(mermaid_js_path)).toString()
            StaTableLogger.debug(f"mermaidwin.js absolute URL: {js_abs_url}")

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
{code}
</pre>
</body>
</html>"""

            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(html)
                    temp_path = f.name
                StaTableLogger.debug(f"Temporary HTML created: {temp_path}")
                self.web_view.load(QUrl.fromLocalFile(temp_path))
            except Exception as e:
                StaTableLogger.error(f"Failed to create temporary HTML: {e}")
        else:
            self.text_view.setPlainText(code)

    def _on_load_finished(self, ok: bool):
        StaTableLogger.debug(f"WebEngine loadFinished: ok={ok}")
        if ok and self.web_view:
            StaTableLogger.debug("Executing renderMermaid() via JavaScript...")
            self.web_view.page().runJavaScript("renderMermaid();")


# ----------------------------------------------------------------------
# 状態/イベント設定パネル
# ----------------------------------------------------------------------
class SettingsPanel(QWidget):
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

        # 状態一覧タブ
        state_tab = QWidget()
        state_layout = QVBoxLayout(state_tab)
        self.state_table = QTableWidget(0, 6)
        self.state_table.setHorizontalHeaderLabels(["名称", "説明", "entry関数", "exit関数", "do関数", "タイプ"])
        self.state_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.state_table.setFont(QFont("Consolas", 10))
        state_layout.addWidget(self.state_table)
        btn_state = QHBoxLayout()
        add_state_btn = QPushButton("追加")
        add_state_btn.clicked.connect(self.add_state)
        del_state_btn = QPushButton("削除")
        del_state_btn.clicked.connect(self.delete_state)
        btn_state.addWidget(add_state_btn)
        btn_state.addWidget(del_state_btn)
        state_layout.addLayout(btn_state)
        self.tab.addTab(state_tab, "状態一覧")

        # イベント辞書タブ
        event_tab = QWidget()
        event_layout = QVBoxLayout(event_tab)
        self.event_table = QTableWidget(0, 3)
        self.event_table.setHorizontalHeaderLabels(["名称", "説明", "種類"])
        self.event_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.event_table.setFont(QFont("Consolas", 10))
        event_layout.addWidget(self.event_table)
        btn_event = QHBoxLayout()
        add_event_btn = QPushButton("追加")
        add_event_btn.clicked.connect(self.add_event)
        del_event_btn = QPushButton("削除")
        del_event_btn.clicked.connect(self.delete_event)
        btn_event.addWidget(add_event_btn)
        btn_event.addWidget(del_event_btn)
        event_layout.addLayout(btn_event)
        self.tab.addTab(event_tab, "イベント辞書")

        # ロール関数タブ
        role_tab = QWidget()
        role_layout = QVBoxLayout(role_tab)
        self.role_table = QTableWidget(0, 7)
        self.role_table.setHorizontalHeaderLabels([
            "関数名", "説明", "戻り値型", "引数1型", "引数1名", "引数2型", "引数2名"
        ])
        self.role_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.role_table.setFont(QFont("Consolas", 10))
        role_layout.addWidget(self.role_table)
        btn_role = QHBoxLayout()
        add_role_btn = QPushButton("追加")
        add_role_btn.clicked.connect(self.add_role_function)
        del_role_btn = QPushButton("削除")
        del_role_btn.clicked.connect(self.delete_role_function)
        btn_role.addWidget(add_role_btn)
        btn_role.addWidget(del_role_btn)
        role_layout.addLayout(btn_role)
        self.tab.addTab(role_tab, "ロール関数")

        # 変更検知
        self.state_table.itemChanged.connect(self.on_state_table_item_changed)
        self.event_table.itemChanged.connect(self.on_event_table_item_changed)
        self.role_table.itemChanged.connect(self.on_role_table_item_changed)

        # 状態一覧のセルダブルクリックでActionEditDialogを開く
        self.state_table.cellDoubleClicked.connect(self.on_state_table_cell_double_clicked)

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
            entry_item = QTableWidgetItem(state.entry)
            entry_item.setToolTip("ダブルクリックで編集")
            self.state_table.setItem(row, 2, entry_item)
            exit_item = QTableWidgetItem(state.exit)
            exit_item.setToolTip("ダブルクリックで編集")
            self.state_table.setItem(row, 3, exit_item)
            do_item = QTableWidgetItem(state.do)
            do_item.setToolTip("ダブルクリックで編集")
            self.state_table.setItem(row, 4, do_item)
            self.state_table.setItem(row, 5, QTableWidgetItem(state.type.value))

        events = list(self.sm.events.values())
        self.event_table.setRowCount(len(events))
        for row, event in enumerate(events):
            self.event_table.setItem(row, 0, QTableWidgetItem(event.name if event.name else "（完了）"))
            self.event_table.setItem(row, 1, QTableWidgetItem(event.description))
            self.event_table.setItem(row, 2, QTableWidgetItem(event.kind.value))

        self.populate_role_table()

        self._updating = False
        StaTableLogger.debug(f"Settings populated: {len(states)} states, {len(events)} events, {len(self.sm.role_functions)} roles")

    def populate_role_table(self):
        roles = list(self.sm.role_functions.values())
        self.role_table.setRowCount(len(roles))
        for row, rf in enumerate(roles):
            self.role_table.setItem(row, 0, QTableWidgetItem(rf.name))
            self.role_table.setItem(row, 1, QTableWidgetItem(rf.description))
            self.role_table.setItem(row, 2, QTableWidgetItem(rf.return_type))
            self.role_table.setItem(row, 3, QTableWidgetItem(rf.arg1_type))
            self.role_table.setItem(row, 4, QTableWidgetItem(rf.arg1_name))
            self.role_table.setItem(row, 5, QTableWidgetItem(rf.arg2_type))
            self.role_table.setItem(row, 6, QTableWidgetItem(rf.arg2_name))
    def on_state_table_cell_double_clicked(self, row, col):
        StaTableLogger.debug(f"SettingsPanel.on_state_table_cell_double_clicked: row={row}, col={col}")
        if col not in (2, 3, 4):
            StaTableLogger.debug("  -> Ignored (not entry/exit/do column)")
            return

        item = self.state_table.item(row, col)
        current_text = item.text() if item else ""
        StaTableLogger.debug(f"  -> current text: '{current_text[:50]}...'")

        dlg = ActionEditDialog(
            self,
            action_text=current_text,
            role_functions=self.sm.role_functions,
            global_defs=self.global_defs
        )
        if dlg.exec() == QDialog.Accepted:
            new_text = dlg.get_action_text()
            StaTableLogger.debug(f"  -> ActionEditDialog accepted, new length={len(new_text)}")
            if item:
                item.setText(new_text)
            else:
                item = QTableWidgetItem(new_text)
                self.state_table.setItem(row, col, item)
            self.settings_changed.emit()
        else:
            StaTableLogger.debug("  -> ActionEditDialog cancelled")

    def add_state(self):
        row = self.state_table.rowCount()
        self.state_table.insertRow(row)
        self.state_table.setItem(row, 0, QTableWidgetItem(""))
        self.state_table.setItem(row, 1, QTableWidgetItem(""))
        self.state_table.setItem(row, 2, QTableWidgetItem(""))
        self.state_table.setItem(row, 3, QTableWidgetItem(""))
        self.state_table.setItem(row, 4, QTableWidgetItem(""))
        self.state_table.setItem(row, 5, QTableWidgetItem("normal"))
        self.state_table.editItem(self.state_table.item(row, 0))
        StaTableLogger.debug("Add state row")

    def delete_state(self):
        row = self.state_table.currentRow()
        if row >= 0:
            name = self.state_table.item(row, 0).text().strip() if self.state_table.item(row, 0) else ""
            if name and name in self.sm.states:
                self.sm.transitions = [t for t in self.sm.transitions if t.source != name and t.target != name]
                del self.sm.states[name]
                self.populate()
                self.settings_changed.emit()
                StaTableLogger.info(f"State deleted: {name}")
            else:
                self.state_table.removeRow(row)

    def add_event(self):
        row = self.event_table.rowCount()
        self.event_table.insertRow(row)
        self.event_table.setItem(row, 0, QTableWidgetItem(""))
        self.event_table.setItem(row, 1, QTableWidgetItem(""))
        self.event_table.setItem(row, 2, QTableWidgetItem("signal"))
        self.event_table.editItem(self.event_table.item(row, 0))
        StaTableLogger.debug("Add event row")

    def delete_event(self):
        row = self.event_table.currentRow()
        if row >= 0:
            name = self.event_table.item(row, 0).text().strip() if self.event_table.item(row, 0) else ""
            if name == "（完了）":
                name = ""
            if name and name in self.sm.events:
                self.sm.transitions = [t for t in self.sm.transitions if t.event != name]
                del self.sm.events[name]
                self.populate()
                self.settings_changed.emit()
                StaTableLogger.info(f"Event deleted: {name}")
            else:
                self.event_table.removeRow(row)

    def add_role_function(self):
        dlg = RoleFunctionDialog(self)
        if dlg.exec() == QDialog.Accepted:
            rf = dlg.get_role_function()
            if rf.name in self.sm.role_functions:
                QMessageBox.warning(self, "警告", "同名のロール関数が既に存在します。")
                return
            self.sm.add_role_function(rf)
            self.populate_role_table()
            self.settings_changed.emit()

    def delete_role_function(self):
        row = self.role_table.currentRow()
        if row >= 0:
            name = self.role_table.item(row, 0).text().strip() if self.role_table.item(row, 0) else ""
            if name and name in self.sm.role_functions:
                self.sm.remove_role_function(name)
                self.populate_role_table()
                self.settings_changed.emit()
            else:
                self.role_table.removeRow(row)

    def on_state_table_item_changed(self, item):
        StaTableLogger.debug(f"State table item changed: row={item.row()}, col={item.column()}, text={item.text()}")
        self._debounce_timer.start()

    def on_event_table_item_changed(self, item):
        StaTableLogger.debug(f"Event table item changed: row={item.row()}, col={item.column()}, text={item.text()}")
        self._debounce_timer.start()

    def on_role_table_item_changed(self, item):
        StaTableLogger.debug(f"Role table item changed: row={item.row()}, col={item.column()}, text={item.text()}")
        self._debounce_timer.start()

    def apply_changes(self):
        # 状態テーブル
        for row in range(self.state_table.rowCount()):
            name = self.state_table.item(row, 0).text().strip() if self.state_table.item(row, 0) else ""
            desc = self.state_table.item(row, 1).text().strip() if self.state_table.item(row, 1) else ""
            entry = self.state_table.item(row, 2).text().strip() if self.state_table.item(row, 2) else ""
            exit_ = self.state_table.item(row, 3).text().strip() if self.state_table.item(row, 3) else ""
            do = self.state_table.item(row, 4).text().strip() if self.state_table.item(row, 4) else ""
            type_str = self.state_table.item(row, 5).text().strip() if self.state_table.item(row, 5) else "normal"
            if name:
                if name in self.sm.states:
                    st = self.sm.states[name]
                    st.description = desc
                    st.entry = entry
                    st.exit = exit_
                    st.do = do
                    st.type = StateType(type_str)
                else:
                    self.sm.add_state(State(name, type=StateType(type_str), description=desc,
                                             entry=entry, exit=exit_, do=do))
        # イベントテーブル
        for row in range(self.event_table.rowCount()):
            name = self.event_table.item(row, 0).text().strip() if self.event_table.item(row, 0) else ""
            if name == "（完了）":
                name = ""
            desc = self.event_table.item(row, 1).text().strip() if self.event_table.item(row, 1) else ""
            kind_str = self.event_table.item(row, 2).text().strip() if self.event_table.item(row, 2) else "signal"
            if name:
                if name in self.sm.events:
                    ev = self.sm.events[name]
                    ev.description = desc
                    ev.kind = EventKind(kind_str)
                else:
                    self.sm.add_event(Event(name, kind=EventKind(kind_str), description=desc))
        # ロール関数テーブル
        self.sm.role_functions.clear()
        for row in range(self.role_table.rowCount()):
            name = self.role_table.item(row, 0).text().strip() if self.role_table.item(row, 0) else ""
            if name:
                desc = self.role_table.item(row, 1).text().strip() if self.role_table.item(row, 1) else ""
                ret = self.role_table.item(row, 2).text().strip() if self.role_table.item(row, 2) else "int"
                a1t = self.role_table.item(row, 3).text().strip() if self.role_table.item(row, 3) else "int"
                a1n = self.role_table.item(row, 4).text().strip() if self.role_table.item(row, 4) else "arg1"
                a2t = self.role_table.item(row, 5).text().strip() if self.role_table.item(row, 5) else "int"
                a2n = self.role_table.item(row, 6).text().strip() if self.role_table.item(row, 6) else "arg2"
                self.sm.add_role_function(RoleFunction(name, desc, ret, a1t, a1n, a2t, a2n))
        StaTableLogger.debug("Settings changes applied")


# ----------------------------------------------------------------------
# 単一タブのコンテンツ
# ----------------------------------------------------------------------
class StateMachineTab(QWidget):
    def __init__(self, sm: StateMachine, global_defs: GlobalDefinitions = None, parent=None):
        super().__init__(parent)
        self.sm = sm
        self.global_defs = global_defs if global_defs else GlobalDefinitions()

        layout = QHBoxLayout(self)

        left_split = QSplitter(Qt.Vertical)
        self.table = MatrixTableWidget(sm, global_defs=self.global_defs)
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