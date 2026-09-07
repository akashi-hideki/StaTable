# statable_gui/transition_editor_direct/canvas_widget.py
"""
キャンバスウィジェット（C案：再構築時に子ノード含む全体レイアウト再計算）
"""

import json
import logging

from PySide6.QtCore import Qt, Signal, QTimer, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QAction, QPainter
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QToolTip, QMenu
)

from .draft import ActionDraft, FlowItem, ensure_list

logger = logging.getLogger("transition_editor_direct.canvas")


class FlowNodeItem(QGraphicsRectItem):
    COLORS = {
        "function": QColor(255, 165, 0),
        "transition": QColor(70, 130, 180),
        "pre_action": QColor(255, 200, 100),
        "else": QColor(220, 80, 80),
        "else_action": QColor(255, 150, 150),
    }
    ICONS = {
        "function": "🟧",
        "transition": "🟦",
        "pre_action": "🟨",
        "else": "🟥",
        "else_action": "🟪",
    }

    def __init__(self, item_type, text, flow_item=None, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.flow_item = flow_item
        self.edit_callback = None
        self.delete_callback = None
        self.duplicate_callback = None
        self.move_up_callback = None
        self.move_down_callback = None
        self.move_finished_callback = None

        color = self.COLORS.get(item_type, QColor(200, 200, 200))
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 1))
        self.setRect(0, 0, 240, 40)

        label = f"{self.ICONS.get(item_type, '')} {text}"
        self.text_item = QGraphicsTextItem(label, self)
        self.text_item.setDefaultTextColor(Qt.black)
        self.text_item.setFont(QFont("Arial", 9))
        self.text_item.setPos(8, 8)

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        # メインのfunction / transitionのみ移動可能
        if item_type in ("function", "transition"):
            self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        else:
            self.setFlag(QGraphicsRectItem.ItemIsMovable, False)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        logger.debug(f"FlowNodeItem.mousePressEvent: type={self.item_type}")
        event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        logger.debug(f"FlowNodeItem.mouseReleaseEvent: type={self.item_type}")
        # グリッドスナップ
        if self.item_type in ("function", "transition") and self.scene():
            grid = self.scene().views()[0]._grid_size if hasattr(self.scene().views()[0], '_grid_size') else 20
            pos = self.pos()
            snapped_x = round(pos.x() / grid) * grid
            snapped_y = round(pos.y() / grid) * grid
            self.setPos(snapped_x, snapped_y)
            logger.debug(f"Snapped position: ({snapped_x}, {snapped_y})")
        super().mouseReleaseEvent(event)
        if self.move_finished_callback:
            self.move_finished_callback(self)

    def hoverEnterEvent(self, event):
        QToolTip.showText(event.screenPos(), self.get_guidance_text())
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if self.edit_callback:
            logger.debug(f"FlowNodeItem.mouseDoubleClickEvent: type={self.item_type}")
            self.edit_callback(self)

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = QAction("編集", menu)
        edit_action.triggered.connect(lambda: self.edit_callback(self) if self.edit_callback else None)
        menu.addAction(edit_action)

        menu.addSeparator()

        up_action = QAction("上へ", menu)
        up_action.triggered.connect(lambda: self.move_up_callback(self) if self.move_up_callback else None)
        menu.addAction(up_action)

        down_action = QAction("下へ", menu)
        down_action.triggered.connect(lambda: self.move_down_callback(self) if self.move_down_callback else None)
        menu.addAction(down_action)

        menu.addSeparator()

        duplicate_action = QAction("複製", menu)
        duplicate_action.triggered.connect(lambda: self.duplicate_callback(self) if self.duplicate_callback else None)
        menu.addAction(duplicate_action)

        delete_action = QAction("削除", menu)
        delete_action.triggered.connect(lambda: self.delete_callback(self) if self.delete_callback else None)
        menu.addAction(delete_action)

        menu.exec(event.screenPos())
        event.accept()

    def get_guidance_text(self):
        if self.item_type == "transition":
            return "遷移条件ノード\n・上にロール関数をドロップで直前処理追加\n・ダブルクリックで条件を編集\n・右クリックで各種操作"
        elif self.item_type == "function":
            return "ロール関数ノード\n・ダブルクリックで関数名を変更"
        elif self.item_type == "pre_action":
            return "遷移直前処理\n・ドラッグで並べ替え"
        elif self.item_type == "else":
            return "else条件\n・上に関数をドロップでelseアクション追加"
        elif self.item_type == "else_action":
            return "elseアクション\n・ドラッグで並べ替え"
        return ""


class FlowCanvas(QGraphicsView):
    MIME_TYPE = "application/x-flow-item"
    draft_updated = Signal()
    node_edit_requested = Signal(object)
    node_delete_requested = Signal(object)
    node_duplicate_requested = Signal(object)
    node_move_up_requested = Signal(object)
    node_move_down_requested = Signal(object)

    def __init__(self, draft: ActionDraft, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMinimumHeight(500)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self._grid_size = 20
        self._zoom_factor = 1.15

        logger.debug("=== FlowCanvas init ===")
        logger.debug(f"draft.flow_items count = {len(draft.flow_items)}")
        for i, item in enumerate(draft.flow_items):
            logger.debug(f"  flow_item[{i}]: type={item.item_type}, name={item.name}")

        self._rebuild()
        logger.debug("=== FlowCanvas init end ===")

    def _rebuild(self):
        """
        C案: 子ノードを含む全ノードを上から順に配置し、重なりを解消する。
        """
        logger.debug("=== _rebuild START (C案: 全ノード再配置) ===")
        self.scene.clear()

        # ノードと接続線ペアを保持するリスト
        nodes = []                # (FlowNodeItem, indent_x)
        connection_pairs = []     # (parent_node, child_node)

        # 1. flow_items から全ノードを生成
        for item_idx, item in enumerate(self.draft.flow_items):
            if item.item_type == "function":
                node = FlowNodeItem("function", item.display_text(), flow_item=item)
                nodes.append((node, 30))  # インデント30
                self._setup_node_callbacks(node)

            elif item.item_type == "transition":
                # メイン transition
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                has_else = item.params.get('has_else', True)
                else_target = item.params.get('else_target', '')

                main_node = FlowNodeItem("transition", item.display_text(), flow_item=item)
                nodes.append((main_node, 30))
                self._setup_node_callbacks(main_node)

                # pre_actions
                for pre in pre_actions:
                    pre_node = FlowNodeItem("pre_action", pre, flow_item=item)
                    nodes.append((pre_node, 60))
                    connection_pairs.append((main_node, pre_node))

                # else node
                if has_else:
                    else_text = f"else → {else_target}" if else_target else "else（未設定）"
                    else_node = FlowNodeItem("else", else_text, flow_item=item)
                    nodes.append((else_node, 60))
                    connection_pairs.append((main_node, else_node))

                    # else_actions
                    for ea in else_actions:
                        ea_node = FlowNodeItem("else_action", ea, flow_item=item)
                        nodes.append((ea_node, 90))
                        connection_pairs.append((else_node, ea_node))

        # 2. ノードを上から順に配置
        current_y = 30
        placed_nodes = []   # 配置済みノード（重なり判定用）

        for node, indent_x in nodes:
            # X座標はインデント固定
            node.setPos(indent_x, current_y)

            # 既配置ノードと重ならないようにYを調整
            while self._has_overlap_with_any(node, placed_nodes):
                # 重なった相手の下端 + 10 に下げる
                max_bottom = 0
                node_rect = node.sceneBoundingRect()
                for placed in placed_nodes:
                    placed_rect = placed.sceneBoundingRect()
                    if node_rect.intersects(placed_rect):
                        max_bottom = max(max_bottom, placed_rect.bottom())
                new_y = max_bottom + 10
                node.setY(new_y)
                node_rect = node.sceneBoundingRect()

            # 配置済みリストに追加
            placed_nodes.append(node)
            self.scene.addItem(node)

            # 次の初期Y
            current_y = node.sceneBoundingRect().bottom() + 10

        # 3. 接続線を追加
        for parent, child in connection_pairs:
            p_rect = parent.sceneBoundingRect()
            c_rect = child.sceneBoundingRect()
            line = QGraphicsLineItem(
                p_rect.center().x(), p_rect.bottom(),
                c_rect.center().x(), c_rect.top()
            )
            line.setPen(QPen(QColor(100, 100, 100), 1, Qt.DashLine))
            self.scene.addItem(line)

        # 4. シーン矩形更新
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 40))
        self.draft_updated.emit()

        # 5. 全ノードの重なりチェックログ
        self._log_all_overlaps(placed_nodes)

        logger.debug("=== _rebuild END (C案) ===")

    def _has_overlap_with_any(self, node, placed_nodes):
        """配置済みノードのいずれかと重なるか判定"""
        node_rect = node.sceneBoundingRect()
        for placed in placed_nodes:
            if node_rect.intersects(placed.sceneBoundingRect()):
                return True
        return False

    def _log_all_overlaps(self, nodes):
        """全ノードの位置と重なりペアをログ出力"""
        logger.debug("--- All nodes after rebuild ---")
        for node in nodes:
            name = node.flow_item.name if node.flow_item else node.item_type
            rect = node.sceneBoundingRect()
            logger.debug(f"  {node.item_type:12s} '{name:15s}' pos=({rect.x():.0f},{rect.y():.0f}) size=({rect.width():.0f}x{rect.height():.0f})")

        # 重なりペアをチェック
        overlapping_pairs = []
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                if node1.sceneBoundingRect().intersects(node2.sceneBoundingRect()):
                    name1 = node1.flow_item.name if node1.flow_item else node1.item_type
                    name2 = node2.flow_item.name if node2.flow_item else node2.item_type
                    overlapping_pairs.append((name1, name2))

        if overlapping_pairs:
            logger.warning("Overlap still exists after rebuild:")
            for pair in overlapping_pairs:
                logger.warning(f"  - '{pair[0]}' and '{pair[1]}'")
        else:
            logger.debug("No overlaps after rebuild (all nodes)")

    def _setup_node_callbacks(self, node):
        """ノードにコールバックを設定"""
        node.edit_callback = self._on_node_edit_requested
        node.delete_callback = self._on_node_delete_requested
        node.duplicate_callback = self._on_node_duplicate_requested
        node.move_up_callback = self._on_node_move_up_requested
        node.move_down_callback = self._on_node_move_down_requested
        node.move_finished_callback = self._on_node_move_finished

    def _on_node_edit_requested(self, node: FlowNodeItem):
        logger.debug(f"Node edit requested: type={node.item_type}")
        self.node_edit_requested.emit(node)

    def _on_node_delete_requested(self, node: FlowNodeItem):
        logger.debug(f"Node delete requested: type={node.item_type}")
        self.node_delete_requested.emit(node)

    def _on_node_duplicate_requested(self, node: FlowNodeItem):
        logger.debug(f"Node duplicate requested: type={node.item_type}")
        self.node_duplicate_requested.emit(node)

    def _on_node_move_up_requested(self, node: FlowNodeItem):
        logger.debug(f"Node move up requested: type={node.item_type}")
        self.node_move_up_requested.emit(node)

    def _on_node_move_down_requested(self, node: FlowNodeItem):
        logger.debug(f"Node move down requested: type={node.item_type}")
        self.node_move_down_requested.emit(node)

    def _on_node_move_finished(self, node: FlowNodeItem):
        """
        ノード移動終了時：
        C案では、移動後に自動で全体レイアウトを再構築する。
        """
        if node.flow_item and node.item_type in ("function", "transition"):
            pos = node.pos()
            # 位置はFlowItemに保存しない（再構築で自動配置するため）
            logger.debug(f"Node moved: '{node.flow_item.name}' to ({pos.x():.1f}, {pos.y():.1f})")
            # 即座に再構築を予約
            QTimer.singleShot(0, self._rebuild)

    def auto_align(self):
        """全ノードを自動整列（C案では_rebuildと同じ）"""
        self._rebuild()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = self._zoom_factor if event.angleDelta().y() > 0 else 1 / self._zoom_factor
            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def dragEnterEvent(self, event):
        logger.debug(f"FlowCanvas.dragEnterEvent START: formats={event.mimeData().formats()}")
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
            logger.debug("FlowCanvas.dragEnterEvent: accepted")
        else:
            logger.debug("FlowCanvas.dragEnterEvent: rejected (no MIME)")
            event.ignore()
        logger.debug("FlowCanvas.dragEnterEvent END")

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
            scene_pos = self.mapToScene(event.position().toPoint())
            item = self.scene.itemAt(scene_pos, self.transform())
            if isinstance(item, FlowNodeItem):
                QToolTip.showText(self.mapToGlobal(event.position().toPoint()), item.get_guidance_text())
            else:
                QToolTip.hideText()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        logger.debug("FlowCanvas.dragLeaveEvent called")
        QToolTip.hideText()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        logger.debug(f"FlowCanvas.dropEvent START: formats={event.mimeData().formats()}")
        try:
            if event.mimeData().hasFormat(self.MIME_TYPE):
                data_bytes = event.mimeData().data(self.MIME_TYPE)
                logger.debug(f"FlowCanvas.dropEvent: data_bytes={data_bytes}")
                data = json.loads(bytes(data_bytes).decode("utf-8"))

                item_type = data.get("item_type", "function")
                name = data.get("name", "")

                scene_pos = self.mapToScene(event.position().toPoint())
                target_item = self.scene.itemAt(scene_pos, self.transform())
                logger.debug(f"FlowCanvas.dropEvent: type={item_type}, name={name}, target={target_item.item_type if isinstance(target_item, FlowNodeItem) else 'none'}")

                if item_type == "function":
                    if isinstance(target_item, FlowNodeItem):
                        if target_item.item_type == "transition":
                            target_flow_item = target_item.flow_item
                            if target_flow_item:
                                target_flow_item.params.setdefault('pre_actions', []).append(name)
                                logger.debug(f"Added pre_action '{name}' to transition")
                        elif target_item.item_type == "else":
                            target_flow_item = target_item.flow_item
                            if target_flow_item:
                                target_flow_item.params.setdefault('else_actions', []).append(name)
                                logger.debug(f"Added else_action '{name}' to transition")
                        else:
                            self.draft.flow_items.append(FlowItem(item_type="function", name=name))
                            logger.debug(f"Added function to flow: {name}")
                    else:
                        self.draft.flow_items.append(FlowItem(item_type="function", name=name))
                        logger.debug(f"Added function to flow: {name}")

                elif item_type == "transition":
                    event_name = name if name else (self.draft.event or "NewEvent")
                    display_name = event_name
                    flow_item = FlowItem(
                        item_type="transition",
                        name=display_name,
                        edited_text=display_name,
                        params={
                            "event": event_name,
                            "condition": "",
                            "pre_actions": [],
                            "target": "",
                            "has_else": True,
                            "else_target": "",
                            "else_actions": [],
                        }
                    )
                    self.draft.flow_items.append(flow_item)
                    logger.debug(f"Added transition condition: event='{event_name}'")

                logger.debug("Scheduling canvas rebuild...")
                QTimer.singleShot(0, self._rebuild)
                event.acceptProposedAction()
            else:
                logger.debug(f"FlowCanvas.dropEvent: rejected formats={event.mimeData().formats()}")
                event.ignore()
        except Exception as e:
            logger.error(f"FlowCanvas.dropEvent error: {e}", exc_info=True)
            event.ignore()
        logger.debug("FlowCanvas.dropEvent END")