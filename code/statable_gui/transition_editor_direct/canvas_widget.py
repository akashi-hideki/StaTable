# statable_gui/transition_editor_direct/canvas_widget.py
"""
キャンバスウィジェット（ガイダンス修正版、elseアクションツリー対応）
"""

import json
import logging

from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QBrush, QColor, QPen, QFont
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QToolTip
)

from .draft import ActionDraft, FlowItem

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

    def __init__(self, item_type, text, parent=None):
        super().__init__(parent)
        self.item_type = item_type
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

    def hoverEnterEvent(self, event):
        # 修正: screenPos() は QPoint を返すため、toPoint() 不要
        QToolTip.showText(event.screenPos(), self.get_guidance_text())
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

    def get_guidance_text(self):
        if self.item_type == "transition":
            return "遷移条件ノード\n・上にロール関数をドロップで直前処理追加\n・ダブルクリックでelse条件・遷移先を設定"
        elif self.item_type == "function":
            return "ロール関数ノード\n・ドラッグで並べ替え"
        elif self.item_type == "pre_action":
            return "遷移直前処理\n・ドラッグで並べ替え"
        elif self.item_type == "else":
            return "else条件\n・上に関数をドロップでelseアクション追加\n・ダブルクリックで遷移先を設定"
        elif self.item_type == "else_action":
            return "elseアクション\n・ドラッグで並べ替え"
        return ""


class FlowCanvas(QGraphicsView):
    MIME_TYPE = "application/x-flow-item"
    draft_updated = Signal()

    def __init__(self, draft: ActionDraft, parent=None):
        super().__init__(parent)
        self.draft = draft
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setMinimumHeight(500)
        self._rebuild()
        logger.debug("FlowCanvas initialized")

    def _rebuild(self):
        logger.debug("Rebuilding canvas")
        self.scene.clear()
        y = 30
        left_x = 30
        child_indent = 30
        prev_bottom = 0
        prev_x = left_x

        for item in self.draft.flow_items:
            if item.item_type == "function":
                node = FlowNodeItem("function", item.display_text())
                self.scene.addItem(node)
                node.setPos(left_x, y)

                if prev_bottom > 0:
                    self.scene.addItem(QGraphicsLineItem(prev_x + 120, prev_bottom, left_x + 120, y))

                prev_bottom = y + node.rect().height()
                prev_x = left_x
                y += node.rect().height() + 25

            elif item.item_type == "transition":
                node = FlowNodeItem("transition", item.display_text())
                self.scene.addItem(node)
                node.setPos(left_x, y)

                if prev_bottom > 0:
                    self.scene.addItem(QGraphicsLineItem(prev_x + 120, prev_bottom, left_x + 120, y))

                parent_bottom = y + node.rect().height()
                prev_bottom = parent_bottom
                prev_x = left_x

                child_y = y + node.rect().height() + 10

                # 直前処理
                pre_actions = item.params.get('pre_actions', [])
                for pre in pre_actions:
                    child = FlowNodeItem("pre_action", pre)
                    self.scene.addItem(child)
                    child.setPos(left_x + child_indent, child_y)
                    self.scene.addItem(QGraphicsLineItem(left_x + 120, parent_bottom,
                                                         left_x + child_indent + 120, child_y))
                    child_y += child.rect().height() + 10

                # else条件
                has_else = item.params.get('has_else', True)
                else_actions = item.params.get('else_actions', [])
                else_target = item.params.get('else_target', '')

                if has_else:
                    else_text = f"else → {else_target}" if else_target else "else（未設定）"
                    else_node = FlowNodeItem("else", else_text)
                    self.scene.addItem(else_node)
                    else_node.setPos(left_x + child_indent, child_y)
                    self.scene.addItem(QGraphicsLineItem(left_x + 120, parent_bottom,
                                                         left_x + child_indent + 120, child_y))
                    else_y = child_y + else_node.rect().height() + 10
                    child_y = else_y

                    # elseアクション（子ノード）
                    for ea in else_actions:
                        ea_node = FlowNodeItem("else_action", ea)
                        self.scene.addItem(ea_node)
                        ea_node.setPos(left_x + child_indent * 2, child_y)
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

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE) or event.mimeData().hasText():
            event.acceptProposedAction()
            logger.debug("Drag enter accepted")

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE) or event.mimeData().hasText():
            event.acceptProposedAction()
            scene_pos = self.mapToScene(event.pos())
            item = self.scene.itemAt(scene_pos, self.transform())
            if isinstance(item, FlowNodeItem):
                # 修正: globalPosition() ではなく mapToGlobal(event.pos()) を使用
                QToolTip.showText(self.mapToGlobal(event.pos()), item.get_guidance_text())
            else:
                QToolTip.hideText()

    def dragLeaveEvent(self, event):
        QToolTip.hideText()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(self.MIME_TYPE):
            data = json.loads(event.mimeData().data(self.MIME_TYPE).data().decode("utf-8"))
            item_type = data.get("item_type", "function")
            name = data.get("name", "")

            scene_pos = self.mapToScene(event.pos())
            target_item = self.scene.itemAt(scene_pos, self.transform())
            logger.debug(f"Drop: type={item_type}, name={name}, target={target_item.item_type if isinstance(target_item, FlowNodeItem) else 'none'}")

            # 関数のドロップ処理
            if item_type == "function":
                if isinstance(target_item, FlowNodeItem):
                    # 遷移ノードの上にドロップ → 直前処理に追加
                    if target_item.item_type == "transition":
                        for flow_item in self.draft.flow_items:
                            if flow_item.item_type == "transition":
                                flow_item.params.setdefault('pre_actions', []).append(name)
                                logger.debug(f"Added pre_action '{name}' to transition")
                                break
                    # elseノードの上にドロップ → elseアクションに追加
                    elif target_item.item_type == "else":
                        for flow_item in self.draft.flow_items:
                            if flow_item.item_type == "transition":
                                flow_item.params.setdefault('else_actions', []).append(name)
                                logger.debug(f"Added else_action '{name}' to transition")
                                break
                    # それ以外（function/pre_action/else_action）はフロー末尾に追加
                    else:
                        self.draft.flow_items.append(FlowItem(item_type="function", name=name))
                        logger.debug(f"Added function to flow: {name}")
                else:
                    # 空白エリアにドロップ → フロー末尾に追加
                    self.draft.flow_items.append(FlowItem(item_type="function", name=name))
                    logger.debug(f"Added function to flow: {name}")

            elif item_type == "transition":
                flow_item = FlowItem(
                    item_type="transition",
                    name=name,
                    params={
                        "event": name,
                        "condition": "",
                        "pre_actions": [],
                        "target": "",
                        "has_else": True,
                        "else_target": "",
                        "else_actions": [],
                    }
                )
                self.draft.flow_items.append(flow_item)
                logger.debug(f"Added transition event: {name} (with else)")

            self._rebuild()
            event.acceptProposedAction()
        else:
            event.ignore()