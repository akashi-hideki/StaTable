# statable_gui/transition_editor_direct/canvas_widget.py
"""
キャンバスウィジェット（D&D対応、ノード移動・編集・削除対応、デバッグログ強化版）
"""

import json
import logging

from PySide6.QtCore import Qt, Signal, QTimer
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
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            logger.debug(f"FlowNodeItem position changed: type={self.item_type}, pos=({value.x():.1f}, {value.y():.1f})")
        return super().itemChange(change, value)

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
            logger.debug(f"  flow_item[{i}]: type={item.item_type}, params={item.params}")

        self._rebuild()
        logger.debug("=== FlowCanvas init end ===")

    def _rebuild(self):
        logger.debug("Rebuilding canvas")
        self.scene.clear()
        y = 30
        left_x = 30
        child_indent = 30
        prev_bottom = 0
        prev_x = left_x

        for item_idx, item in enumerate(self.draft.flow_items):
            logger.debug(f"Processing flow_item[{item_idx}]: type={item.item_type}")

            if item.item_type == "function":
                node = FlowNodeItem("function", item.display_text(), flow_item=item)
                self.scene.addItem(node)
                node.setPos(left_x, y)
                node.edit_callback = self._on_node_edit_requested
                node.delete_callback = self._on_node_delete_requested
                node.duplicate_callback = self._on_node_duplicate_requested
                node.move_up_callback = self._on_node_move_up_requested
                node.move_down_callback = self._on_node_move_down_requested

                if prev_bottom > 0:
                    self.scene.addItem(QGraphicsLineItem(prev_x + 120, prev_bottom, left_x + 120, y))

                prev_bottom = y + node.rect().height()
                prev_x = left_x
                y += node.rect().height() + 25

            elif item.item_type == "transition":
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                condition = item.params.get('condition', '')
                logger.debug(f"  transition: event='{item.params.get('event','')}', condition='{condition}', pre_actions={pre_actions}, else_actions={else_actions}")

                node = FlowNodeItem("transition", item.display_text(), flow_item=item)
                self.scene.addItem(node)
                node.setPos(left_x, y)
                node.edit_callback = self._on_node_edit_requested
                node.delete_callback = self._on_node_delete_requested
                node.duplicate_callback = self._on_node_duplicate_requested
                node.move_up_callback = self._on_node_move_up_requested
                node.move_down_callback = self._on_node_move_down_requested

                if prev_bottom > 0:
                    self.scene.addItem(QGraphicsLineItem(prev_x + 120, prev_bottom, left_x + 120, y))

                parent_bottom = y + node.rect().height()
                prev_bottom = parent_bottom
                prev_x = left_x

                child_y = y + node.rect().height() + 10

                for pre in pre_actions:
                    child = FlowNodeItem("pre_action", pre, flow_item=item)
                    self.scene.addItem(child)
                    child.setPos(left_x + child_indent, child_y)
                    child.edit_callback = None
                    child.delete_callback = None
                    self.scene.addItem(QGraphicsLineItem(left_x + 120, parent_bottom,
                                                         left_x + child_indent + 120, child_y))
                    child_y += child.rect().height() + 10

                has_else = item.params.get('has_else', True)
                else_target = item.params.get('else_target', '')

                if has_else:
                    else_text = f"else → {else_target}" if else_target else "else（未設定）"
                    else_node = FlowNodeItem("else", else_text, flow_item=item)
                    self.scene.addItem(else_node)
                    else_node.setPos(left_x + child_indent, child_y)
                    else_node.edit_callback = None
                    else_node.delete_callback = None
                    self.scene.addItem(QGraphicsLineItem(left_x + 120, parent_bottom,
                                                         left_x + child_indent + 120, child_y))
                    else_y = child_y + else_node.rect().height() + 10
                    child_y = else_y

                    for ea in else_actions:
                        ea_node = FlowNodeItem("else_action", ea, flow_item=item)
                        self.scene.addItem(ea_node)
                        ea_node.setPos(left_x + child_indent * 2, child_y)
                        ea_node.edit_callback = None
                        ea_node.delete_callback = None
                        self.scene.addItem(QGraphicsLineItem(left_x + child_indent + 120, else_y - 10,
                                                             left_x + child_indent * 2 + 120, child_y))
                        child_y += ea_node.rect().height() + 10

                target = item.params.get('target', '')
                if target:
                    target_label = QGraphicsTextItem(f"遷移先: {target}")
                    target_label.setDefaultTextColor(Qt.darkGreen)
                    target_label.setFont(QFont("Arial", 10, QFont.Bold))
                    target_label.setPos(left_x + child_indent, child_y)
                    self.scene.addItem(target_label)
                    child_y += 30

                y = child_y + 15 if (pre_actions or has_else or else_actions or target) else parent_bottom + 25

        if self.draft.default_target:
            label = QGraphicsTextItem(f"デフォルト遷移先: {self.draft.default_target}")
            label.setPos(left_x, y + 20)
            self.scene.addItem(label)

        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 40))
        self.draft_updated.emit()
        logger.debug("Canvas rebuild completed")

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

    def auto_align(self):
        y = 30
        for item in self.scene.items():
            if isinstance(item, FlowNodeItem) and item.flow_item is not None:
                item.setPos(30, y)
                y += item.rect().height() + 25
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 40))
        self.draft_updated.emit()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = self._zoom_factor if event.angleDelta().y() > 0 else 1 / self._zoom_factor
            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def dragEnterEvent(self, event):
        logger.debug(f"FlowCanvas.dragEnterEvent: formats={event.mimeData().formats()}")
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
            logger.debug("FlowCanvas.dragEnterEvent: accepted")
        else:
            logger.debug("FlowCanvas.dragEnterEvent: rejected (no MIME)")
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            event.acceptProposedAction()
            scene_pos = self.mapToScene(event.position().toPoint())
            item = self.scene.itemAt(scene_pos, self.transform())
            logger.debug(f"FlowCanvas.dragMoveEvent: pos={event.position().toPoint()}, scene_pos={scene_pos}, item={type(item).__name__ if item else 'None'}")
            if isinstance(item, FlowNodeItem):
                QToolTip.showText(self.mapToGlobal(event.position().toPoint()), item.get_guidance_text())
            else:
                QToolTip.hideText()
        else:
            logger.debug(f"FlowCanvas.dragMoveEvent: rejected formats={event.mimeData().formats()}")
            event.ignore()

    def dragLeaveEvent(self, event):
        QToolTip.hideText()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        logger.debug(f"FlowCanvas.dropEvent: formats={event.mimeData().formats()}")
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

                # ★ 再構築を遅延させる（ドロップ処理完了後に実行）
                QTimer.singleShot(0, self._rebuild)
                event.acceptProposedAction()
            else:
                logger.debug(f"FlowCanvas.dropEvent: rejected formats={event.mimeData().formats()}")
                event.ignore()
        except Exception as e:
            logger.error(f"FlowCanvas.dropEvent error: {e}", exc_info=True)
            event.ignore()