from PySide6.QtWidgets import QDockWidget, QPlainTextEdit, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from .logger import StaTableLogger


class TraceBallWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("TraceBall", parent)
        self.setObjectName("TraceBall")
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable
        )

        container = QWidget()
        layout = QVBoxLayout(container)
        self.text_view = QPlainTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setMaximumBlockCount(1000)
        layout.addWidget(self.text_view)
        self.setWidget(container)

        logger = StaTableLogger()
        logger.set_log_callback(self.append_log)

        self.append_log("TraceBall ready.")

    def append_log(self, message: str):
        self.text_view.appendPlainText(message)
        scrollbar = self.text_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        self.text_view.clear()