# tests/test_drop_indicator_overlap.py
"""
挿入位置インジケータ方式 評価用テストプログラム（重なり解消対応版）
修正版3: ノード順序をY座標基準で管理し、ドロップ位置に応じた挿入を正しく反映
"""

import sys
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("drop_indicator_overlap_test")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsLineItem, QLabel
)
from PySide6.QtCore import Qt, QRectF, QPointF, QMimeData
from PySide6.QtGui import QBrush, QColor, QPen, QDrag, QPixmap, QPainter


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
        self.setPen(QPen(Qt.black, 2))

    def display_name(self):
        return f"{self.item_type}:{self.text}"


class DraggableSource(QGraphicsRectItem):
    """ドラッグ元アイテム"""
    def __init__(self, text, x, y):
        super().__init__(0, 0, 100, 30)
        self.text = text
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(200, 200, 200)))
        self.setPen(QPen(Qt.black, 2))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.scenePos()
            logger.debug("DraggableSource.mousePressEvent")
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and hasattr(self, '_drag_start_pos'):
            if (event.scenePos() - self._drag_start_pos).manhattanLength() > 10:
                logger.debug("DraggableSource.mouseMoveEvent: start drag")
                mime = QMimeData()
                mime.setData("application/x-test-item", b"drag")

                pixmap = QPixmap(110, 40)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                painter.setBrush(QColor(200, 200, 200))
                painter.setPen(QPen(Qt.black, 2))
                painter.drawRect(0, 0, 100, 30)
                painter.drawText(10, 20, self.text)
                painter.end()

                drag = QDrag(self.scene().views()[0])
                drag.setMimeData(mime)
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPointF(50, 15).toPoint())
                drag.exec_(Qt.CopyAction)
                event.accept()
                return
        super().mouseMoveEvent(event)


class DropIndicatorView(QGraphicsView):
    """インジケータ表示＋重なり解消付きキャンバス"""

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setScene(QGraphicsScene(self))
        self.setDragMode(QGraphicsView.NoDrag)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMinimumSize(600, 400)

        # インジケータ線
        self.indicator = QGraphicsLineItem()
        pen = QPen(Qt.gray, 5, Qt.DashLine)
        self.indicator.setPen(pen)
        self.indicator.setZValue(100)
        self.scene().addItem(self.indicator)
        self.indicator.hide()

        self._add_dummy_nodes()
        self._add_draggable_source()

    def _add_dummy_nodes(self):
        self.scene().addItem(DummyNode("transition", "START", 50, 50))
        self.scene().addItem(DummyNode("else", "else", 50, 100))
        self.scene().addItem(DummyNode("function", "CheckSensor", 50, 150))
        self.scene().addItem(DummyNode("transition", "STOP", 50, 200))

    def _add_draggable_source(self):
        source = DraggableSource("DragMe", 350, 50)
        self.scene().addItem(source)
        logger.debug("DraggableSource added")

    def _get_all_dummy_nodes(self):
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
                self._log_overlap_simulation(insertion, scene_pos)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-test-item"):
            scene_pos = self.mapToScene(event.position().toPoint())
            insertion = self._determine_insertion(scene_pos)
            logger.debug(f"dropEvent: final insertion = {insertion}")

            # 実際に挿入し、重なりを解消
            self._insert_and_resolve_overlap(insertion, scene_pos)
            event.acceptProposedAction()

    def _determine_insertion(self, scene_pos):
        nodes = self._get_all_dummy_nodes()
        for node in nodes:
            rect = node.sceneBoundingRect()
            if rect.contains(scene_pos):
                rel_y = (scene_pos.y() - rect.top()) / rect.height()
                if rel_y <= 0.2:
                    logger.debug(f"  rel_y={rel_y:.2f} -> before")
                    return {"type": "before", "node": node, "color": QColor("blue")}
                elif rel_y >= 0.8:
                    logger.debug(f"  rel_y={rel_y:.2f} -> after")
                    return {"type": "after", "node": node, "color": QColor("blue")}
                else:
                    if node.item_type == "transition":
                        logger.debug(f"  rel_y={rel_y:.2f} -> child_transition")
                        return {"type": "child_transition", "node": node, "color": QColor("green")}
                    elif node.item_type == "else":
                        logger.debug(f"  rel_y={rel_y:.2f} -> child_else")
                        return {"type": "child_else", "node": node, "color": QColor("orange")}
                    else:
                        if rel_y < 0.5:
                            logger.debug(f"  rel_y={rel_y:.2f} -> before (function)")
                            return {"type": "before", "node": node, "color": QColor("blue")}
                        else:
                            logger.debug(f"  rel_y={rel_y:.2f} -> after (function)")
                            return {"type": "after", "node": node, "color": QColor("blue")}
        logger.debug("  no node under cursor -> end")
        return {"type": "end", "node": None, "color": QColor("gray")}

    def _update_indicator(self, insertion):
        color = insertion["color"]
        pen = QPen(color, 5, Qt.DashLine)
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
            max_y = max([it.sceneBoundingRect().bottom() for it in self._get_all_dummy_nodes()])
            y = max_y + 10

        self.indicator.setLine(10, y, 400, y)
        self.indicator.show()

    def _log_overlap_simulation(self, insertion, mouse_pos):
        new_node = DummyNode("function", "Dragged", 0, 0)
        # 挿入位置をシミュレートして重なりを確認
        if insertion["type"] == "before":
            target = insertion["node"]
            y = target.sceneBoundingRect().top() - 45
        elif insertion["type"] == "after":
            target = insertion["node"]
            y = target.sceneBoundingRect().bottom() + 5
        elif insertion["type"] in ("child_transition", "child_else"):
            target = insertion["node"]
            y = target.sceneBoundingRect().bottom() + 5
        else:  # end
            all_nodes = self._get_all_dummy_nodes()
            y = max([it.sceneBoundingRect().bottom() for it in all_nodes]) + 10
        new_node.setPos(50, y)

        existing_nodes = self._get_all_dummy_nodes()
        overlapping = []
        new_rect = new_node.sceneBoundingRect()
        for node in existing_nodes:
            if new_rect.intersects(node.sceneBoundingRect()):
                overlapping.append(node.display_name())
        if overlapping:
            logger.warning(f"Overlap simulation: overlaps with: {overlapping}")
        else:
            logger.debug("Overlap simulation: no overlap")

    def _insert_and_resolve_overlap(self, insertion, scene_pos):
        """挿入を実行し、Y座標ソート済みリストで正しい順序に再配置する"""
        new_node = DummyNode("function", f"New_{insertion['type']}", 0, 0)
        self.scene().addItem(new_node)

        # 新ノードを除く既存ノードをY座標でソート
        existing_nodes = [n for n in self._get_all_dummy_nodes() if n is not new_node]
        sorted_existing = sorted(existing_nodes, key=lambda n: n.sceneBoundingRect().top())

        # 挿入タイプに応じて、ソート済みリスト内の適切な位置に新ノードを挿入
        insert_type = insertion["type"]
        target = insertion["node"]

        if insert_type == "before":
            target_index = sorted_existing.index(target) if target in sorted_existing else len(sorted_existing)
            sorted_existing.insert(target_index, new_node)
        elif insert_type == "after":
            target_index = sorted_existing.index(target) if target in sorted_existing else len(sorted_existing)
            sorted_existing.insert(target_index + 1, new_node)
        elif insert_type in ("child_transition", "child_else"):
            # 子ノードはターゲット直後に挿入（簡易的に「after」と同じ扱い）
            target_index = sorted_existing.index(target) if target in sorted_existing else len(sorted_existing)
            sorted_existing.insert(target_index + 1, new_node)
        else:  # end
            sorted_existing.append(new_node)

        # Y座標を再割り当て（50間隔）
        current_y = 50
        for node in sorted_existing:
            node.setPos(50, current_y)
            current_y += 50  # 40 + 10間隔

        logger.debug("After insert and resolve:")
        for node in sorted_existing:
            logger.debug(f"  {node.display_name()} pos=({node.sceneBoundingRect().x():.0f},{node.sceneBoundingRect().y():.0f})")

        # 最終重なりチェック
        overlapping_pairs = []
        nodes = sorted_existing
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i+1:]:
                if n1.sceneBoundingRect().intersects(n2.sceneBoundingRect()):
                    overlapping_pairs.append((n1.display_name(), n2.display_name()))

        if overlapping_pairs:
            logger.warning(f"After resolve, still overlaps: {overlapping_pairs}")
        else:
            logger.debug("After resolve, no overlaps")


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("挿入位置インジケータ評価テスト（重なり解消対応）")
        self.setMinimumSize(800, 600)
        self.view = DropIndicatorView()
        self.setCentralWidget(self.view)
        logger.debug("TestWindow initialized")


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())