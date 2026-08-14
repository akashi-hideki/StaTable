import sys
import tempfile
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QColor, QKeyEvent, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QPlainTextEdit, QSplitter, QLabel,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QTabWidget, QAbstractItemView, QMessageBox,
    QInputDialog, QToolButton
)

# WebEngine対応
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

from statable.model import State, Event, Transition, StateType, EventKind
from statable.state_machine import StateMachine
from statable.mermaid_gen import generate_mermaid

from .logger import StaTableLogger
from .traceball import TraceBallWidget


# ----------------------------------------------------------------------
# リソースパス解決（EXE化対応・ディレクトリも返せる）
# ----------------------------------------------------------------------
def get_resource_path(filename: str = "") -> Path:
    """リソースファイルのパスを取得する。
    PyInstallerでEXE化した場合は sys._MEIPASS 以下を参照する。
    filename が空の場合は Resources ディレクトリ自体を返す。
    """
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS) / "Resources"
    else:
        base_path = Path(__file__).resolve().parent.parent / "Resources"
    if filename:
        return base_path / filename
    return base_path


# ----------------------------------------------------------------------
# サンプルデータ作成
# ----------------------------------------------------------------------
def create_sample_state_machine() -> StateMachine:
    sm = StateMachine()
    sm.add_state(State("Idle", entry="Idle_entry", description="初期状態"))
    sm.add_state(State("Active", do="Active_do", description="動作中"))
    sm.add_state(State("Error", entry="Error_entry", exit="Error_exit", description="エラー状態"))
    sm.add_state(State("Halt", type=StateType.FINAL, description="停止状態"))
    sm.add_event(Event("start", id=1, description="起動要求"))
    sm.add_event(Event("stop", id=2, description="停止要求"))
    sm.add_event(Event("error", id=3, params=["uint8_t err_code"], description="エラー通知"))
    sm.add_event(Event("", id=0, kind=EventKind.SIGNAL, description="完了遷移"))
    sm.set_initial("Idle")
    sm.add_transition(Transition("Idle", "start", "", "init()", "Active"))
    sm.add_transition(Transition("Active", "stop", "", "stop()", "Idle"))
    sm.add_transition(Transition("Active", "error", "err_code != 0", "log()", "Error"))
    sm.add_transition(Transition("Error", "", "retry_count < 3", "retry_count++", "Active"))
    sm.add_transition(Transition("Error", "", "retry_count >= 3", "", "Halt"))
    # 複数条件の例
    sm.add_transition(Transition("Active", "error", "err_code == 0", "ignore()", "Active"))
    return sm


# ----------------------------------------------------------------------
# 遷移編集ダイアログ（複数条件対応・一括編集）
# ----------------------------------------------------------------------
class TransitionListDialog(QDialog):
    """1セル内の複数の遷移条件を一括編集するダイアログ"""
    def __init__(self, parent=None, state_names=None, event_name="", existing_transitions=None):
        super().__init__(parent)
        self.setWindowTitle("遷移編集（複数条件）")
        self.setMinimumSize(700, 400)
        self.state_names = state_names or []

        layout = QVBoxLayout(self)

        event_label = QLabel(f"イベント: {event_name if event_name else '完了遷移'}")
        layout.addWidget(event_label)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["遷移条件", "動作", "遷移先", "表示タイトル"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setFont(QFont("Consolas", 10))
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("行追加")
        add_btn.clicked.connect(self.add_row)
        del_btn = QPushButton("行削除")
        del_btn.clicked.connect(self.delete_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if existing_transitions:
            for trans in existing_transitions:
                self.add_row(trans)
        else:
            self.add_row()

    def add_row(self, trans: Optional[Transition] = None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        cond_item = QTableWidgetItem(trans.guard if trans else "")
        cond_item.setToolTip("C言語式（例：err_code != 0）")
        self.table.setItem(row, 0, cond_item)

        act_item = QTableWidgetItem(trans.action if trans else "")
        act_item.setToolTip("実行する処理（例：log();）")
        self.table.setItem(row, 1, act_item)

        target_combo = QComboBox()
        target_combo.addItem("")
        target_combo.addItems(self.state_names)
        if trans and trans.target:
            idx = target_combo.findText(trans.target)
            if idx >= 0:
                target_combo.setCurrentIndex(idx)
        self.table.setCellWidget(row, 2, target_combo)

        title = self._generate_title(trans) if trans else ""
        title_item = QTableWidgetItem(title)
        title_item.setToolTip("表に表示する短いラベル（空なら自動生成）")
        self.table.setItem(row, 3, title_item)

    def _generate_title(self, trans: Optional[Transition]) -> str:
        if not trans:
            return ""
        parts = [trans.target] if trans.target else ["(内部)"]
        if trans.guard:
            parts.append(f"[{trans.guard}]")
        if trans.action:
            parts.append(f"/ {trans.action}")
        return " ".join(parts)

    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def get_transitions(self) -> List[Transition]:
        transitions = []
        for row in range(self.table.rowCount()):
            guard = self.table.item(row, 0).text().strip() if self.table.item(row, 0) else ""
            action = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else ""
            target_widget = self.table.cellWidget(row, 2)
            target = target_widget.currentText().strip() if target_widget else ""
            title_item = self.table.item(row, 3)
            title = title_item.text().strip() if title_item else ""
            if not title and (guard or action or target):
                title = self._generate_title(Transition(source="", event="", guard=guard, action=action, target=target))
            transitions.append(Transition(
                source="",
                event="",
                guard=guard,
                action=action,
                target=target,
                transition_type="external"
            ))
        return transitions


# ----------------------------------------------------------------------
# 状態遷移マトリックステーブル
# ----------------------------------------------------------------------
class MatrixTableWidget(QTableWidget):
    transition_changed = Signal()

    def __init__(self, sm: StateMachine, parent=None):
        super().__init__(0, 0, parent)
        self.sm = sm
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().setMinimumWidth(120)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cellDoubleClicked.connect(self.open_transition_dialog)
        self.setFont(QFont("Consolas", 10))
        self.populate()
        StaTableLogger.debug("MatrixTableWidget initialized")

    def populate(self):
        states = list(self.sm.states.keys())
        events = list(self.sm.events.keys())
        self.clear()
        self.setRowCount(len(states))
        self.setColumnCount(len(events))
        self.setHorizontalHeaderLabels([e if e else "完了" for e in events])
        self.setVerticalHeaderLabels(states)

        for row, state in enumerate(states):
            for col, event in enumerate(events):
                trans_list = self._find_transitions(state, event)
                if trans_list:
                    titles = [self._generate_title(t) for t in trans_list]
                    display = "\n".join(titles)
                    item = QTableWidgetItem(display)
                    item.setData(Qt.UserRole, trans_list)
                    item.setToolTip("ダブルクリックまたは Enter で編集")
                    self.setItem(row, col, item)
                else:
                    item = QTableWidgetItem("")
                    item.setData(Qt.UserRole, [])
                    self.setItem(row, col, item)
        StaTableLogger.debug(f"MatrixTable populated: {len(states)} states, {len(events)} events")

    def _find_transitions(self, state: str, event: str) -> List[Transition]:
        return [t for t in self.sm.transitions if t.source == state and t.event == event]

    def _generate_title(self, trans: Transition) -> str:
        if trans.target:
            parts = [trans.target]
            if trans.guard:
                parts.append(f"[{trans.guard}]")
            if trans.action:
                parts.append(f"/ {trans.action}")
            return " ".join(parts)
        else:
            return f"internal: {trans.event or '完了'} / {trans.action}".strip()

    def open_transition_dialog(self, row: int, col: int):
        state = self.verticalHeaderItem(row).text() if self.verticalHeaderItem(row) else ""
        event = self.horizontalHeaderItem(col).text() if self.horizontalHeaderItem(col) else ""
        if event == "完了":
            event_name = ""
        else:
            event_name = event

        item = self.item(row, col)
        existing_list = item.data(Qt.UserRole) if item else []

        dlg = TransitionListDialog(
            self,
            state_names=list(self.sm.states.keys()),
            event_name=event_name,
            existing_transitions=existing_list
        )

        if dlg.exec() == QDialog.Accepted:
            new_transitions = dlg.get_transitions()
            self.sm.transitions = [t for t in self.sm.transitions
                                   if not (t.source == state and t.event == event_name)]
            for trans in new_transitions:
                trans.source = state
                trans.event = event_name
                self.sm.add_transition(trans)
            self.populate()
            self.transition_changed.emit()
            StaTableLogger.info(f"Transition updated: {state} -{event_name or '完了'}-> {len(new_transitions)} transition(s)")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_F2):
            current = self.currentItem()
            if current:
                self.open_transition_dialog(current.row(), current.column())
            return
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            current = self.currentItem()
            if current:
                trans_list = current.data(Qt.UserRole)
                if trans_list:
                    for trans in trans_list:
                        self.sm.transitions.remove(trans)
                    self.populate()
                    self.transition_changed.emit()
                    StaTableLogger.info(f"Transition deleted: {len(trans_list)} transition(s)")
            return
        super().keyPressEvent(event)


# ----------------------------------------------------------------------
# Mermaidプレビューウィジェット（動作確認済みの方式）
# ----------------------------------------------------------------------
class MermaidWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.web_view = None
        self.text_view = None

        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            # ローカルファイルアクセスを許可
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
            # mermaidwin.js の絶対URLを取得
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

            # 一時HTMLファイルを作成してロード
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

    def __init__(self, sm: StateMachine, parent=None):
        super().__init__(parent)
        self.sm = sm
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

        # 変更検知
        self.state_table.itemChanged.connect(self.on_state_table_item_changed)
        self.event_table.itemChanged.connect(self.on_event_table_item_changed)

        self.populate()
        StaTableLogger.debug("SettingsPanel initialized")

    def populate(self):
        states = list(self.sm.states.values())
        self.state_table.setRowCount(len(states))
        for row, state in enumerate(states):
            self.state_table.setItem(row, 0, QTableWidgetItem(state.name))
            self.state_table.setItem(row, 1, QTableWidgetItem(state.description))
            self.state_table.setItem(row, 2, QTableWidgetItem(state.entry))
            self.state_table.setItem(row, 3, QTableWidgetItem(state.exit))
            self.state_table.setItem(row, 4, QTableWidgetItem(state.do))
            self.state_table.setItem(row, 5, QTableWidgetItem(state.type.value))

        events = list(self.sm.events.values())
        self.event_table.setRowCount(len(events))
        for row, event in enumerate(events):
            self.event_table.setItem(row, 0, QTableWidgetItem(event.name if event.name else "（完了）"))
            self.event_table.setItem(row, 1, QTableWidgetItem(event.description))
            self.event_table.setItem(row, 2, QTableWidgetItem(event.kind.value))
        StaTableLogger.debug(f"Settings populated: {len(states)} states, {len(events)} events")

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

    def on_state_table_item_changed(self, item):
        StaTableLogger.debug(f"State table item changed: row={item.row()}, col={item.column()}, text={item.text()}")

    def on_event_table_item_changed(self, item):
        StaTableLogger.debug(f"Event table item changed: row={item.row()}, col={item.column()}, text={item.text()}")

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
        StaTableLogger.debug("Settings changes applied")


# ----------------------------------------------------------------------
# 単一タブのコンテンツ
# ----------------------------------------------------------------------
class StateMachineTab(QWidget):
    def __init__(self, sm: StateMachine, parent=None):
        super().__init__(parent)
        self.sm = sm
        layout = QHBoxLayout(self)

        left_split = QSplitter(Qt.Vertical)
        self.table = MatrixTableWidget(sm)
        self.mermaid = MermaidWidget()
        left_split.addWidget(self.table)
        left_split.addWidget(self.mermaid)
        left_split.setSizes([700, 300])
        layout.addWidget(left_split, stretch=3)

        self.settings = SettingsPanel(sm)
        layout.addWidget(self.settings, stretch=1)

        # シグナル接続
        self.table.transition_changed.connect(self.update_mermaid)
        self.settings.settings_changed.connect(self.update_mermaid)

        self.update_mermaid()
        StaTableLogger.debug("StateMachineTab created")

    def update_mermaid(self):
        self.settings.apply_changes()
        code = generate_mermaid(self.sm)
        self.mermaid.set_mermaid_code(code)
        StaTableLogger.info("Mermaid updated for current tab")


# ----------------------------------------------------------------------
# メインウィンドウ
# ----------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StaTable - 状態遷移表エディタ")
        self.resize(1800, 1200)

        self.logger = StaTableLogger()
        self.logger.debug("MainWindow initialization started")

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)

        # 「+」ボタン
        self.add_tab_button = QToolButton()
        self.add_tab_button.setText("+")
        self.add_tab_button.setToolTip("新しい状態遷移表を追加")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)

        # メニュー
        self.create_menus()

        # TraceBallドック
        self.traceball = TraceBallWidget(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.traceball)
        self.traceball.hide()

        # 初期タブ
        sample_sm = create_sample_state_machine()
        self.add_state_machine_tab("アプリ", sample_sm)

        self.logger.debug("MainWindow initialization completed")

    def create_menus(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu("表示")
        toggle_traceball = QAction("TraceBall表示", self)
        toggle_traceball.setCheckable(True)
        toggle_traceball.setChecked(False)
        toggle_traceball.toggled.connect(self.toggle_traceball)
        view_menu.addAction(toggle_traceball)

        file_menu = menubar.addMenu("ファイル")
        new_tab_action = QAction("新しい状態遷移表", self)
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)

    def add_new_tab(self):
        name, ok = QInputDialog.getText(self, "新しい状態遷移表", "タブ名を入力してください：")
        if ok and name:
            sm = StateMachine()
            self.add_state_machine_tab(name, sm)
            self.logger.info(f"New tab added: {name}")

    def add_state_machine_tab(self, name: str, sm: StateMachine):
        tab = StateMachineTab(sm)
        idx = self.tab_widget.addTab(tab, name)
        self.tab_widget.setCurrentIndex(idx)
        self.logger.debug(f"Tab '{name}' added at index {idx}")

    def close_tab(self, index: int):
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(self, "警告", "少なくとも1つのタブが必要です。")
            return
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        widget.deleteLater()
        self.logger.info(f"Tab closed at index {index}")

    def toggle_traceball(self, checked: bool):
        if checked:
            self.traceball.show()
            self.logger.debug("TraceBall shown")
        else:
            self.traceball.hide()
            self.logger.debug("TraceBall hidden")