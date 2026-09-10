# tests/test_drop_indicator_overlap.py
"""
挿入位置インジケータ方式 評価用テストプログラム
- 挿入位置判定
- インジケータ表示
- 既存ノードとの重なり判定・解消シミュレーション
"""

import sys
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("drop_indicator_overlap_test")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsLineItem
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen


class DummyNode(QGraphicsRectItem):
    """テスト用ダミーノード"""
    def __init__(self, item_type, text, x, y, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.text = text
        self.setRect(0, 0, 160, 40)
        self.setPos(x, y)

        colors = {
            "transition": QColor(70, 130, 180),
            "else": QColor(220, 80, 80),
            "function": QColor(255, 165, 0),
            "pre_action": QColor(255, 200, 100),
        }
        self.setBrush(QBrush(colors.get(item_type, QColor(200, 200, 200))))
        self.setPen(QPen(Qt.black, 1))

    def display_name(self):
        return f"{self.item_type}:{self.text}"


class DropIndicatorView(QGraphicsView):
    """インジケータ表示＋重なり判定付きキャンバス"""

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setScene(QGraphicsScene(self))
        self.setDragMode(QGraphicsView.NoDrag)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMinimumSize(600, 400)

        self.indicator = QGraphicsLineItem()
        self.indicator.setPen(QPen(Qt.gray, 3))
        self.indicator.setZValue(100)
        self.scene().addItem(self.indicator)
        self.indicator.hide()

        self._add_dummy_nodes()

    def _add_dummy_nodes(self):
        """テスト用ノードを配置"""
        self.scene().addItem(DummyNode("transition", "START", 50, 50))
        self.scene().addItem(DummyNode("else", "else", 50, 100))
        self.scene().addItem(DummyNode("function", "CheckSensor", 50, 150))
        self.scene().addItem(DummyNode("transition", "STOP", 50, 200))

    def _get_all_nodes(self):
        return [item for item in self.scene().items() if isinstance(item, DummyNode)]

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-test-item"):
            event.acceptProposedAction()
            logger.debug("dragEnterEvent: accepted")

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-test-item"):
            event.acceptProposedAction()
            scene_pos = self.mapToScene(event.position().toPoint())
            insertion = self._determine_insertion(scene_pos)
            if insertion:
                self._update_indicator(insertion)
                # 挿入後に重なるかどうかシミュレーション
                self._log_overlap_simulation(insertion, scene_pos)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-test-item"):
            scene_pos = self.mapToScene(event.position().toPoint())
            insertion = self._determine_insertion(scene_pos)
            logger.debug(f"dropEvent: final insertion = {insertion}")
            # 重なり最終チェック
            self._log_final_overlap(insertion)
            event.acceptProposedAction()

    def _determine_insertion(self, scene_pos):
        nodes = self._get_all_nodes()
        for node in nodes:
            rect = node.sceneBoundingRect()
            if rect.contains(scene_pos):
                rel_y = (scene_pos.y() - rect.top()) / rect.height()
                if rel_y <= 0.2:
                    return {"type": "before", "node": node, "color": QColor("blue")}
                elif rel_y >= 0.8:
                    return {"type": "after", "node": node, "color": QColor("blue")}
                else:
                    if node.item_type == "transition":
                        return {"type": "child_transition", "node": node, "color": QColor("green")}
                    elif node.item_type == "else":
                        return {"type": "child_else", "node": node, "color": QColor("orange")}
                    else:
                        if rel_y < 0.5:
                            return {"type": "before", "node": node, "color": QColor("blue")}
                        else:
                            return {"type": "after", "node": node, "color": QColor("blue")}
        return {"type": "end", "node": None, "color": QColor("gray")}

    def _update_indicator(self, insertion):
        color = insertion["color"]
        pen = QPen(color, 3)
        self.indicator.setPen(pen)

        node = insertion["node"]
        insert_type = insertion["type"]

        if insert_type == "before":
            y = node.sceneBoundingRect().top() - 5
        elif insert_type == "after":
            y = node.sceneBoundingRect().bottom() + 5
        elif insert_type in ("child_transition", "child_else"):
            y = node.sceneBoundingRect().center().y()
        else:
            max_y = max([it.sceneBoundingRect().bottom() for it in self._get_all_nodes()])
            y = max_y + 10

        self.indicator.setLine(10, y, 400, y)
        self.indicator.show()

    def _log_overlap_simulation(self, insertion, mouse_pos):
        """ドラッグ中に、挿入後をシミュレートして重なりをログ"""
        # 仮の新規ノードを作成（挿入タイプに応じた位置）
        new_node = DummyNode("function", "Dragged", 0, 0)
        new_node.setPos(mouse_pos.x(), mouse_pos.y())

        existing_nodes = self._get_all_nodes()
        overlapping = []
        new_rect = new_node.sceneBoundingRect()
        for node in existing_nodes:
            if new_rect.intersects(node.sceneBoundingRect()):
                overlapping.append(node.display_name())

        if overlapping:
            logger.warning(f"Overlap simulation: '{new_node.display_name()}' overlaps with: {overlapping}")
        else:
            logger.debug("Overlap simulation: no overlap")

    def _log_final_overlap(self, insertion):
        """最終的な重なりを確認"""
        # 実際には挿入処理はしないが、シミュレーションとして新規ノードの予定位置を計算
        if insertion["type"] == "before":
            y = insertion["node"].sceneBoundingRect().top() - 5
        elif insertion["type"] == "after":
            y = insertion["node"].sceneBoundingRect().bottom() + 5
        elif insertion["type"] in ("child_transition", "child_else"):
            y = insertion["node"].sceneBoundingRect().center().y()
        else:
            y = max([it.sceneBoundingRect().bottom() for it in self._get_all_nodes()]) + 10

        new_node = DummyNode("function", "Dragged", 10, y)
        new_rect = new_node.sceneBoundingRect()
        existing_nodes = self._get_all_nodes()
        overlapping = []
        for node in existing_nodes:
            if new_rect.intersects(node.sceneBoundingRect()):
                overlapping.append(node.display_name())

        if overlapping:
            logger.warning(f"Final overlap check: overlaps with {overlapping}")
        else:
            logger.debug("Final overlap check: no overlap")


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("挿入位置インジケータ評価テスト（重なり判定付き）")
        self.setMinimumSize(800, 600)

        self.view = DropIndicatorView()
        self.setCentralWidget(self.view)

        # ドラッグ元（簡易）
        source = QGraphicsRectItem(0, 0, 100, 30)
        source.setPos(500, 50)
        source.setBrush(QBrush(QColor(200, 200, 200)))
        source.setPen(QPen(Qt.black, 1))
        self.view.scene().addItem(source)

        logger.debug("TestWindow initialized")


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())