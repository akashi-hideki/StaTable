import sys
from pathlib import Path
from typing import Optional, List, Dict

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QColor, QKeyEvent, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QPlainTextEdit, QSplitter, QLabel,
    QHeaderView, QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QTabWidget, QAbstractItemView, QMessageBox,
    QInputDialog, QTabBar, QToolButton, QMenu, QFileDialog
)

# WebEngine対応
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

from statable.model import State, Event, Transition, StateType, EventKind
from statable.state_machine import StateMachine
from statable.mermaid_gen import generate_mermaid

from .logger import StaTableLogger
from .traceball import TraceBallWidget


# ----------------------------------------------------------------------
# リソースパス解決（EXE化対応）
# ----------------------------------------------------------------------
def get_resource_path(filename: str) -> Path:
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS) / "Resources"
    else:
        base_path = Path(__file__).resolve().parent.parent / "Resources"
    path = base_path / filename
    StaTableLogger.debug(f"Resource path for '{filename}': {path}")
    return path


# ----------------------------------------------------------------------
# サンプルデータ作成
# ----------------------------------------------------------------------
def create_sample_state_machine() -> StateMachine:
    sm = StateMachine()
    sm.add_state(State("Idle", entry="init()", description="初期状態"))
    sm.add_state(State("Active", description="動作中"))
    sm.add_state(State("Error", description="エラー状態"))
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
    return sm


# ----------------------------------------------------------------------
# 遷移編集ダイアログ
# ----------------------------------------------------------------------
class TransitionDialog(QDialog):
    def __init__(self, parent=None, state_names=None, event_name="",
                 existing_title="", existing_target="", existing_guard="",
                 existing_action="", existing_type="external"):
        super().__init__(parent)
        self.setWindowTitle("遷移編集")
        self.setMinimumWidth(450)

        layout = QFormLayout(self)
        self.title_edit = QLineEdit(existing_title)
        self.title_edit.setPlaceholderText("例：Active / init()")
        layout.addRow("タイトル", self.title_edit)

        self.target_combo = QComboBox()
        self.target_combo.addItem("")
        if state_names:
            self.target_combo.addItems(state_names)
        if existing_target:
            idx = self.target_combo.findText(existing_target)
            if idx >= 0:
                self.target_combo.setCurrentIndex(idx)
        layout.addRow("遷移先", self.target_combo)

        self.guard_edit = QLineEdit(existing_guard)
        self.guard_edit.setPlaceholderText("C言語式（例：err_code != 0）")
        layout.addRow("ガード", self.guard_edit)

        self.action_edit = QLineEdit(existing_action)
        self.action_edit.setPlaceholderText("動作（例：log();）")
        layout.addRow("動作", self.action_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["external", "internal", "local"])
        if existing_type in ["external", "internal", "local"]:
            self.type_combo.setCurrentText(existing_type)
        layout.addRow("種別", self.type_combo)

        self.event_label = QLabel(event_name if event_name else "完了遷移")
        layout.addRow("イベント", self.event_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return {
            "title": self.title_edit.text().strip(),
            "target": self.target_combo.currentText().strip(),
            "guard": self.guard_edit.text().strip(),
            "action": self.action_edit.text().strip(),
            "type": self.type_combo.currentText().strip(),
        }


# ----------------------------------------------------------------------
# 状態遷移マトリックステーブル
# ----------------------------------------------------------------------
class MatrixTableWidget(QTableWidget):
    """状態遷移マトリックス表示・編集テーブル"""
    transition_changed = Signal()  # 遷移変更シグナル

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
                trans = self._find_transition(state, event)
                if trans:
                    title = self._generate_title(trans)
                    item = QTableWidgetItem(title)
                    item.setData(Qt.UserRole, trans)
                    self.setItem(row, col, item)
                else:
                    item = QTableWidgetItem("")
                    item.setData(Qt.UserRole, None)
                    self.setItem(row, col, item)
        StaTableLogger.debug(f"MatrixTable populated: {len(states)} states, {len(events)} events")

    def _find_transition(self, state: str, event: str):
        for t in self.sm.transitions:
            if t.source == state and t.event == event:
                return t
        return None

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
        existing = item.data(Qt.UserRole) if item else None

        dlg = TransitionDialog(
            self,
            state_names=list(self.sm.states.keys()),
            event_name=event_name,
            existing_title=existing and self._generate_title(existing) or "",
            existing_target=existing.target if existing else "",
            existing_guard=existing.guard if existing else "",
            existing_action=existing.action if existing else "",
            existing_type=existing.transition_type if existing else "external"
        )

        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            if existing:
                self.sm.transitions.remove(existing)
            trans = Transition(
                source=state,
                event=event_name,
                guard=data["guard"],
                action=data["action"],
                target=data["target"],
                transition_type=data["type"]
            )
            self.sm.add_transition(trans)
            self.populate()
            self.transition_changed.emit()
            StaTableLogger.info(f"Transition updated: {state} -{event}-> {data['target'] or '(internal)'}")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_F2):
            current = self.currentItem()
            if current:
                self.open_transition_dialog(current.row(), current.column())
            return
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            current = self.currentItem()
            if current:
                trans = current.data(Qt.UserRole)
                if trans:
                    self.sm.transitions.remove(trans)
                    self.populate()
                    self.transition_changed.emit()
                    StaTableLogger.info(f"Transition deleted: {trans.source} -{trans.event}-> {trans.target or '(internal)'}")
                else:
                    StaTableLogger.debug("No transition to delete in this cell")
            return
        super().keyPressEvent(event)


# ----------------------------------------------------------------------
# Mermaidプレビューウィジェット
# ----------------------------------------------------------------------
class MermaidWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        if WEBENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            layout.addWidget(self.web_view)
        else:
            self.text_view = QPlainTextEdit()
            self.text_view.setReadOnly(True)
            layout.addWidget(self.text_view)
        StaTableLogger.debug("MermaidWidget initialized (WebEngine available: %s)", WEBENGINE_AVAILABLE)

    def set_mermaid_code(self, code: str):
        StaTableLogger.debug(f"Setting Mermaid code:\n{code}")
        if WEBENGINE_AVAILABLE:
            mermaid_js = ""
            try:
                resource_path = get_resource_path("mermaidwin.js")
                if resource_path.exists():
                    mermaid_js = resource_path.read_text(encoding="utf-8")
                    StaTableLogger.debug(f"Loaded mermaidwin.js from {resource_path}")
                else:
                    StaTableLogger.warning(f"mermaidwin.js not found at {resource_path}")
            except Exception as e:
                StaTableLogger.error(f"Failed to read mermaidwin.js: {e}")

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script>{mermaid_js}</script>
                <script>
                    document.addEventListener('DOMContentLoaded', function() {{
                        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
                        mermaid.run();
                    }});
                </script>
            </head>
            <body>
                <pre class="mermaid">
{code}
                </pre>
            </body>
            </html>
            """
            self.web_view.setHtml(html)
        else:
            self.text_view.setPlainText(code)


# ----------------------------------------------------------------------
# 状態/イベント設定パネル（各タブ内の右側）
# ----------------------------------------------------------------------
class SettingsPanel(QWidget):
    """状態一覧とイベント辞書を編集するパネル"""
    settings_changed = Signal()

    def __init__(self, sm: StateMachine, parent=None):
        super().__init__(parent)
        self.sm = sm
        layout = QVBoxLayout(self)

        # タブで状態/イベントを切替
        self.tab = QTabWidget()
        layout.addWidget(self.tab)

        # 状態一覧タブ
        state_tab = QWidget()
        state_layout = QVBoxLayout(state_tab)
        self.state_table = QTableWidget(0, 3)
        self.state_table.setHorizontalHeaderLabels(["名称（英数字）", "内容（説明）", "タイプ"])
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
        self.event_table.setHorizontalHeaderLabels(["名称（英数字）", "内容（説明）", "種類"])
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
        # 状態テーブル
        states = list(self.sm.states.values())
        self.state_table.setRowCount(len(states))
        for row, state in enumerate(states):
            name_item = QTableWidgetItem(state.name)
            desc_item = QTableWidgetItem(state.description)
            type_item = QTableWidgetItem(state.type.value)
            self.state_table.setItem(row, 0, name_item)
            self.state_table.setItem(row, 1, desc_item)
            self.state_table.setItem(row, 2, type_item)
        # イベントテーブル
        events = list(self.sm.events.values())
        self.event_table.setRowCount(len(events))
        for row, event in enumerate(events):
            name_item = QTableWidgetItem(event.name if event.name else "（完了）")
            desc_item = QTableWidgetItem(event.description)
            kind_item = QTableWidgetItem(event.kind.value)
            self.event_table.setItem(row, 0, name_item)
            self.event_table.setItem(row, 1, desc_item)
            self.event_table.setItem(row, 2, kind_item)
        StaTableLogger.debug(f"Settings populated: {len(states)} states, {len(events)} events")

    def add_state(self):
        row = self.state_table.rowCount()
        self.state_table.insertRow(row)
        self.state_table.setItem(row, 0, QTableWidgetItem(""))
        self.state_table.setItem(row, 1, QTableWidgetItem(""))
        self.state_table.setItem(row, 2, QTableWidgetItem("normal"))
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
        # モデルへ反映（簡易実装：後で詳細化可能）
        StaTableLogger.debug(f"State table item changed: row={item.row()}, col={item.column()}, text={item.text()}")

    def on_event_table_item_changed(self, item):
        StaTableLogger.debug(f"Event table item changed: row={item.row()}, col={item.column()}, text={item.text()}")

    def apply_changes(self):
        """テーブル編集内容をステートマシンに反映（必要に応じて）"""
        # 状態テーブル
        for row in range(self.state_table.rowCount()):
            name = self.state_table.item(row, 0).text().strip() if self.state_table.item(row, 0) else ""
            desc = self.state_table.item(row, 1).text().strip() if self.state_table.item(row, 1) else ""
            type_str = self.state_table.item(row, 2).text().strip() if self.state_table.item(row, 2) else "normal"
            if name:
                if name in self.sm.states:
                    self.sm.states[name].description = desc
                    self.sm.states[name].type = StateType(type_str)
                else:
                    self.sm.add_state(State(name, type=StateType(type_str), description=desc))
        # イベントテーブル
        for row in range(self.event_table.rowCount()):
            name = self.event_table.item(row, 0).text().strip() if self.event_table.item(row, 0) else ""
            if name == "（完了）":
                name = ""
            desc = self.event_table.item(row, 1).text().strip() if self.event_table.item(row, 1) else ""
            kind_str = self.event_table.item(row, 2).text().strip() if self.event_table.item(row, 2) else "signal"
            if name:
                if name in self.sm.events:
                    self.sm.events[name].description = desc
                    self.sm.events[name].kind = EventKind(kind_str)
                else:
                    self.sm.add_event(Event(name, kind=EventKind(kind_str), description=desc))
        StaTableLogger.debug("Settings changes applied")


# ----------------------------------------------------------------------
# 単一タブのコンテンツ（状態遷移表＋Mermaid＋設定パネル）
# ----------------------------------------------------------------------
class StateMachineTab(QWidget):
    """1つの状態遷移表を保持するタブ"""
    def __init__(self, sm: StateMachine, parent=None):
        super().__init__(parent)
        self.sm = sm
        layout = QHBoxLayout(self)

        # 左：垂直分割（マトリックス＋Mermaid）
        left_split = QSplitter(Qt.Vertical)
        self.table = MatrixTableWidget(sm)
        self.mermaid = MermaidWidget()
        left_split.addWidget(self.table)
        left_split.addWidget(self.mermaid)
        left_split.setSizes([700, 300])
        layout.addWidget(left_split, stretch=3)

        # 右：設定パネル
        self.settings = SettingsPanel(sm)
        layout.addWidget(self.settings, stretch=1)

        # シグナル接続：遷移変更→Mermaid更新
        self.table.transition_changed.connect(self.update_mermaid)
        self.settings.settings_changed.connect(self.update_mermaid)

        # 初期表示
        self.update_mermaid()
        StaTableLogger.debug("StateMachineTab created")

    def update_mermaid(self):
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

        # ログ初期化
        self.logger = StaTableLogger()
        self.logger.debug("MainWindow initialization started")

        # メインのタブウィジェット
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)

        # 「+」ボタンをタブバーに追加
        self.add_tab_button = QToolButton()
        self.add_tab_button.setText("+")
        self.add_tab_button.setToolTip("新しい状態遷移表を追加")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)

        # メニュー
        self.create_menus()

        # TraceBallドックを追加
        self.traceball = TraceBallWidget(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.traceball)
        self.traceball.hide()  # 初期は非表示

        # 初期タブを追加
        sample_sm = create_sample_state_machine()
        self.add_state_machine_tab("アプリ", sample_sm)

        self.logger.debug("MainWindow initialization completed")

    def create_menus(self):
        menubar = self.menuBar()
        # 表示メニュー
        view_menu = menubar.addMenu("表示")
        toggle_traceball = QAction("TraceBall表示", self)
        toggle_traceball.setCheckable(True)
        toggle_traceball.setChecked(False)
        toggle_traceball.toggled.connect(self.toggle_traceball)
        view_menu.addAction(toggle_traceball)

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        new_tab_action = QAction("新しい状態遷移表", self)
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)

        self.logger.debug("Menus created")

    def add_new_tab(self):
        """新しいタブを追加"""
        name, ok = QInputDialog.getText(self, "新しい状態遷移表", "タブ名を入力してください：")
        if ok and name:
            sm = StateMachine()  # 空のステートマシン
            self.add_state_machine_tab(name, sm)
            self.logger.info(f"New tab added: {name}")

    def add_state_machine_tab(self, name: str, sm: StateMachine):
        """指定された名前とステートマシンでタブを追加"""
        tab = StateMachineTab(sm)
        idx = self.tab_widget.addTab(tab, name)
        self.tab_widget.setCurrentIndex(idx)
        self.logger.debug(f"Tab '{name}' added at index {idx}")

    def close_tab(self, index: int):
        """タブを閉じる"""
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(self, "警告", "少なくとも1つのタブが必要です。")
            return
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        widget.deleteLater()
        self.logger.info(f"Tab closed at index {index}")

    def toggle_traceball(self, checked: bool):
        """TraceBallの表示/非表示"""
        if checked:
            self.traceball.show()
            self.logger.debug("TraceBall shown")
        else:
            self.traceball.hide()
            self.logger.debug("TraceBall hidden")