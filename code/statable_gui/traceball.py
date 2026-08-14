from PySide6.QtWidgets import QDockWidget, QPlainTextEdit, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from .logger import StaTableLogger


class TraceBallWidget(QDockWidget):
    """ログを表示するフローティング可能なドックウィジェット"""
    def __init__(self, parent=None):
        super().__init__("TraceBall", parent)
        self.setObjectName("TraceBall")
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.setFeatures(
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetClosable
        )

        # 内部テキスト表示
        container = QWidget()
        layout = QVBoxLayout(container)
        self.text_view = QPlainTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setMaximumBlockCount(1000)  # 過負荷防止
        layout.addWidget(self.text_view)
        self.setWidget(container)

        # ロガーにコールバック登録
        logger = StaTableLogger()
        logger.set_log_callback(self.append_log)

        # 初期表示
        self.append_log("TraceBall ready.")

    def append_log(self, message: str):
        """ログメッセージを追加"""
        self.text_view.appendPlainText(message)
        # 自動スクロール
        scrollbar = self.text_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        self.text_view.clear()