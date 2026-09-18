"""Event queue definition dialog"""

from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QLineEdit, QSpinBox,
    QCheckBox, QFormLayout, QDialogButtonBox, QMessageBox, QAbstractItemView,
    QWidget, QListWidget, QListWidgetItem
)

from statable.global_defs import GlobalDefinitions, EventQueueDef
from .common_widgets import TitleEditWidget, TypeComboBox
from .logger import StaTableLogger


class DoubleClickTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item:
            self.cellDoubleClicked.emit(item.row(), item.column())


class EventQueueEditDialog(QDialog):
    def __init__(self, parent=None, queue_def: Optional[EventQueueDef] = None,
                 event_names: Optional[List[str]] = None, global_defs=None):
        super().__init__(parent)
        self.global_defs = global_defs if global_defs else GlobalDefinitions()
        self.event_names = event_names or []
        self.setWindowTitle("EventQueueEdit")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        # Title input field (required / provisional title auto-set)
        self.title_widget = TitleEditWidget(self, title=queue_def.title if queue_def else "")
        form.addRow("", self.title_widget)

        # Queue name
        self.name_edit = QLineEdit(queue_def.name if queue_def else "")
        form.addRow("Queue name", self.name_edit)

        # Size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(2, 256)
        self.size_spin.setValue(queue_def.size if queue_def else 8)
        form.addRow("Size", self.size_spin)

        # Element type
        self.type_combo = TypeComboBox(self, global_defs=self.global_defs)
        if queue_def:
            self.type_combo.set_current_text(queue_def.element_type)
        form.addRow("Element type", self.type_combo)

        # Related event selection list
        self.event_list = QListWidget()
        for event_name in self.event_names:
            item = QListWidgetItem(event_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if queue_def and event_name in queue_def.event_ids else Qt.Unchecked)
            self.event_list.addItem(item)
        form.addRow("Related events", self.event_list)

        # With priority
        self.priority_check = QCheckBox()
        self.priority_check.setChecked(queue_def.priority_enabled if queue_def else False)
        form.addRow("With priority", self.priority_check)

        # Interrupt protection
        self.safe_check = QCheckBox()
        self.safe_check.setChecked(queue_def.interrupt_safe if queue_def else True)
        form.addRow("Interrupt protection", self.safe_check)

        # RTOS usage
        self.rtos_check = QCheckBox()
        self.rtos_check.setChecked(queue_def.rtos_enabled if queue_def else False)
        form.addRow("RTOS usage", self.rtos_check)

        # description
        self.desc_edit = QLineEdit(queue_def.description if queue_def else "")
        form.addRow("Description", self.desc_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        StaTableLogger.debug("EventQueueEditDialog initialized")

    def _on_accept(self):
        """OK button: auto-set provisional title if title is empty"""
        auto_title = f"Queue: {self.name_edit.text().strip() or '(unnamed)'}"
        self.title_widget.ensure_title(auto_title)
        self.accept()

    def get_queue_def(self) -> EventQueueDef:
        event_ids = []
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            if item.checkState() == Qt.Checked:
                event_ids.append(item.text())
        return EventQueueDef(
            name=self.name_edit.text().strip(),
            size=self.size_spin.value(),
            element_type=self.type_combo.current_text(),
            event_ids=event_ids,
            priority_enabled=self.priority_check.isChecked(),
            interrupt_safe=self.safe_check.isChecked(),
            rtos_enabled=self.rtos_check.isChecked(),
            description=self.desc_edit.text().strip(),
            title=self.title_widget.get_title(),
        )


class EventQueueDefsDialog(QDialog):
    """Event queue definition list dialog"""
    def __init__(self, global_defs: GlobalDefinitions, event_names: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.global_defs = global_defs
        self.event_names = event_names or []
        self.setWindowTitle("Event queue definition")
        self.setMinimumSize(1100, 600)

        layout = QVBoxLayout(self)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search (prefix match):"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Title, queue name, description")
        self.search_edit.textChanged.connect(self.refresh_table)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # List table (title column added / direct edit)
        self.table = DoubleClickTable(0, 9)
        self.table.setHorizontalHeaderLabels(["Title", "Queue name", "Size", "Element type", "Related events", "Priority", "Interrupt protection", "RTOS", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellDoubleClicked.connect(self.on_double_clicked)
        self.table.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_queue)
        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_queue)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.refresh_table()
        StaTableLogger.debug("EventQueueDefsDialog initialized")

    def refresh_table(self):
        query = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ""
        self.table.setRowCount(0)
        for q in self.global_defs.event_queues:
            if not self._matches(q, query):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)

            title_item = QTableWidgetItem(q.title)
            title_item.setToolTip("Title of this queue. Can be edited directly.")
            self.table.setItem(row, 0, title_item)

            self.table.setItem(row, 1, QTableWidgetItem(q.name))
            self.table.setItem(row, 2, QTableWidgetItem(str(q.size)))
            self.table.setItem(row, 3, QTableWidgetItem(q.element_type))
            self.table.setItem(row, 4, QTableWidgetItem(", ".join(q.event_ids)))
            self.table.setItem(row, 5, QTableWidgetItem("Yes" if q.priority_enabled else "None"))
            self.table.setItem(row, 6, QTableWidgetItem("Yes" if q.interrupt_safe else "None"))
            self.table.setItem(row, 7, QTableWidgetItem("Yes" if q.rtos_enabled else "None"))
            self.table.setItem(row, 8, QTableWidgetItem(q.description))

    def _matches(self, q: EventQueueDef, query: str) -> bool:
        """Search filter (prefix match)"""
        if not query:
            return True
        return (
            q.title.lower().startswith(query) or
            q.name.lower().startswith(query) or
            q.description.lower().startswith(query)
        )

    def on_item_changed(self, item):
        """Handler when the title column is edited directly"""
        if item.column() == 0:
            row = item.row()
            name_item = self.table.item(row, 1)
            if name_item and row < len(self.global_defs.event_queues):
                for q in self.global_defs.event_queues:
                    if q.name == name_item.text():
                        q.title = item.text().strip() or f"Queue: {q.name}"
                        break

    def on_double_clicked(self, row, col):
        if col == 0:
            return
        if row < 0 or row >= len(self.global_defs.event_queues):
            return
        target = self.global_defs.event_queues[row]
        dlg = EventQueueEditDialog(self, queue_def=target, event_names=self.event_names, global_defs=self.global_defs)
        if dlg.exec() == QDialog.Accepted:
            new_q = dlg.get_queue_def()
            if not new_q.name:
                QMessageBox.warning(self, "Warning", "Please enter a queue name.")
                return
            self.global_defs.event_queues[row] = new_q
            self.refresh_table()

    def add_queue(self):
        dlg = EventQueueEditDialog(self, event_names=self.event_names, global_defs=self.global_defs)
        if dlg.exec() == QDialog.Accepted:
            q = dlg.get_queue_def()
            if not q.name:
                QMessageBox.warning(self, "Warning", "Please enter a queue name.")
                return
            self.global_defs.event_queues.append(q)
            self.refresh_table()

    def delete_queue(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.global_defs.event_queues):
            self.global_defs.event_queues.pop(row)
            self.refresh_table()