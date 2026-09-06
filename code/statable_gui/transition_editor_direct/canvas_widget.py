# statable_gui/transition_editor_direct/canvas_widget.py
"""
キャンバスウィジェット（D&D対応、ダブルクリック編集・削除対応、デバッグログ強化版）
"""

import json
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QAction
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

    def hoverEnterEvent(self, event):
        QToolTip.showText(event.screenPos(), self.get_guidance_text())
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.edit_callback:
            logger.debug(f"FlowNodeItem.mouseDoubleClickEvent: type={self.item_type}")
            self.edit_callback(self)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = QAction("削除", menu)
        delete_action.triggered.connect(lambda: self.delete_callback(self) if self.delete_callback else None)
        menu.addAction(delete_action)
        menu.exec(event.screenPos())
        event.accept()

    def get_guidance_text(self):
        if self.item_type == "transition":
            return "遷移条件ノード\n・上にロール関数をドロップで直前処理追加\n・ダブルクリックで条件を編集\n・右クリックで削除"
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

    def __init__(self, draft: ActionDraft, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setAcceptDrops(True)
        # ビューポートにも設定
        self.viewport().setAcceptDrops(True)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMinimumHeight(500)

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

                if prev_bottom > 0:
                    self.scene.addItem(QGraphicsLineItem(prev_x + 120, prev_bottom, left_x + 120, y))

                parent_bottom = y + node.rect().height()
                prev_bottom = parent_bottom
                prev_x = left_x

                child_y = y + node.rect().height() + 10

                # 直前処理
                for pre in pre_actions:
                    child = FlowNodeItem("pre_action", pre)
                    self.scene.addItem(child)
                    child.setPos(left_x + child_indent, child_y)
                    child.edit_callback = None
                    child.delete_callback = None
                    self.scene.addItem(QGraphicsLineItem(left_x + 120, parent_bottom,
                                                         left_x + child_indent + 120, child_y))
                    child_y += child.rect().height() + 10

                # else条件
                has_else = item.params.get('has_else', True)
                else_target = item.params.get('else_target', '')

                if has_else:
                    else_text = f"else → {else_target}" if else_target else "else（未設定）"
                    else_node = FlowNodeItem("else", else_text)
                    self.scene.addItem(else_node)
                    else_node.setPos(left_x + child_indent, child_y)
                    else_node.edit_callback = None
                    else_node.delete_callback = None
                    self.scene.addItem(QGraphicsLineItem(left_x + 120, parent_bottom,
                                                         left_x + child_indent + 120, child_y))
                    else_y = child_y + else_node.rect().height() + 10
                    child_y = else_y

                    # elseアクション
                    for ea in else_actions:
                        ea_node = FlowNodeItem("else_action", ea)
                        self.scene.addItem(ea_node)
                        ea_node.setPos(left_x + child_indent * 2, child_y)
                        ea_node.edit_callback = None
                        ea_node.delete_callback = None
                        self.scene.addItem(QGraphicsLineItem(left_x + child_indent + 120, else_y - 10,
                                                             left_x + child_indent * 2 + 120, child_y))
                        child_y += ea_node.rect().height() + 10

                # 遷移先表示
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
        if event.mimeData().hasFormat(self.MIME_TYPE):
            data_bytes = event.mimeData().data(self.MIME_TYPE)
            logger.debug(f"FlowCanvas.dropEvent: data_bytes={data_bytes}")
            try:
                data = json.loads(bytes(data_bytes).decode("utf-8"))
            except Exception as e:
                logger.error(f"FlowCanvas.dropEvent: JSON parse error: {e}")
                event.ignore()
                return

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
                        for flow_item in self.draft.flow_items:
                            if flow_item.item_type == "transition":
                                flow_item.params.setdefault('else_actions', []).append(name)
                                logger.debug(f"Added else_action '{name}' to transition")
                                break
                    else:
                        self.draft.flow_items.append(FlowItem(item_type="function", name=name))
                        logger.debug(f"Added function to flow: {name}")
                else:
                    self.draft.flow_items.append(FlowItem(item_type="function", name=name))
                    logger.debug(f"Added function to flow: {name}")

            elif item_type == "transition":
                # 遷移条件ノードは、セルのイベント名をそのまま使用
                event_name = self.draft.event  # 空でもよい（完了遷移）
                display_name = event_name if event_name else "完了"
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

            self._rebuild()
            event.acceptProposedAction()
        else:
            logger.debug(f"FlowCanvas.dropEvent: rejected formats={event.mimeData().formats()}")
            event.ignore()