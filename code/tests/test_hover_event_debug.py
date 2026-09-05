# tests/test_hover_event_debug.py
"""
QGraphicsSceneHoverEvent で利用可能なメソッド確認テスト
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem
)
from PySide6.QtCore import Qt


class DebugRectItem(QGraphicsRectItem):
    """ホバーイベントの内容を出力するアイテム"""

    def hoverEnterEvent(self, event):
        print("=== hoverEnterEvent ===")
        print("type:", type(event))
        print("dir:", [m for m in dir(event) if not m.startswith('_')])
        print("screenPos:", event.screenPos())
        print("scenePos:", event.scenePos())
        print("pos:", event.pos())
        print("=========================")
        super().hoverEnterEvent(event)


def main():
    app = QApplication(sys.argv)

    scene = QGraphicsScene()
    rect = DebugRectItem()
    rect.setRect(0, 0, 200, 50)
    rect.setAcceptHoverEvents(True)
    scene.addItem(rect)

    view = QGraphicsView(scene)
    view.setWindowTitle("ホバーイベント確認")
    view.resize(400, 300)
    view.show()

    print("ノードにマウスを乗せると、利用可能なメソッドが表示されます。")
    print("終了するにはウィンドウを閉じてください。")

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())