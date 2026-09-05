# tests/test_drag_event_check.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtGui import QDragMoveEvent

class DebugView(QGraphicsView):
    def dragMoveEvent(self, event):
        print("=== dragMoveEvent ===")
        print("type:", type(event))
        print("dir:", [m for m in dir(event) if not m.startswith('_')])
        # 座標系の確認
        print("event.pos():", event.pos())
        print("event.position():", event.position())
        # mapToGlobal を試す
        print("self.mapToGlobal(event.pos()):", self.mapToGlobal(event.pos()))
        print("=======================")
        super().dragMoveEvent(event)

def main():
    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    view = DebugView(scene)
    view.setWindowTitle("ドラッグイベント確認")
    view.resize(400, 300)
    view.show()
    print("ドラッグ操作をするとメソッドが表示されます。")
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())