# statable_gui/transition_editor_direct/canvas_widget.py
"""
キャンバスウィジェット（案C：順序リスト方式対応版）
- ノードのドラッグ移動を無効化
- ドラッグ試行時にメッセージ表示
- フローアイテムの順序に基づく自動整列（子ノード込み）
"""

import json
import logging

from PySide6.QtCore import Qt, Signal, QTimer, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QAction, QPainter
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QToolTip, QMenu,
    QMessageBox, QApplication
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

        # ★ キャンバス内でのドラッグ移動を完全に無効化（案C）
        self.setFlag(QGraphicsRectItem.ItemIsMovable, False)

        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)

        # ドラッグ試行検出用
        self._drag_start_pos = None

    def itemChange(self, change, value):
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.scenePos()
            logger.debug(f"FlowNodeItem.mousePressEvent: type={self.item_type}, pos={self._drag_start_pos}")
        event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # 左ボタンを押しながら一定距離動いたらメッセージ表示
        if event.buttons() & Qt.LeftButton and self._drag_start_pos is not None:
            if (event.scenePos() - self._drag_start_pos).manhattanLength() > QApplication.startDragDistance():
                logger.debug(f"FlowNodeItem.mouseMoveEvent: drag attempted on type={self.item_type}")
                QMessageBox.information(
                    None,
                    "操作不可",
                    "キャンバス内でのノード移動はできません。\n順序リストで並べ替えてください。"
                )
                self._drag_start_pos = None  # 連続表示を防止
                event.ignore()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        logger.debug(f"FlowNodeItem.mouseReleaseEvent: type={self.item_type}")
        self._drag_start_pos = None
        # 移動不可のため、move_finished_callback は呼ばない
        super().mouseReleaseEvent(event)

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
            return "遷移直前処理\n・順序リストで並べ替え"
        elif self.item_type == "else":
            return "else条件\n・上に関数をドロップでelseアクション追加"
        elif self.item_type == "else_action":
            return "elseアクション\n・順序リストで並べ替え"
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
            logger.debug(f"  flow_item[{i}]: type={item.item_type}, name={item.name}, pos=({item.pos_x},{item.pos_y})")

        self._rebuild()
        logger.debug("=== FlowCanvas init end ===")

    def _rebuild(self):
        logger.debug("=== _rebuild START ===")
        self.scene.clear()

        # フローアイテムを順序（order_index）でソート（現状はリスト順）
        # 将来的には order_index を使う
        flow_items = self.draft.flow_items

        # 表示開始Y座標
        current_y = 30

        for item in flow_items:
            logger.debug(f"Processing flow_item: type={item.item_type}, name={item.name}")
            if item.item_type == "function":
                node = FlowNodeItem("function", item.display_text(), flow_item=item)
                self._setup_node_callbacks(node)
                self.scene.addItem(node)
                node.setPos(30, current_y)
                logger.debug(f"  function '{item.name}' placed at y={current_y}")

                # 次のメインノードの開始Yを更新
                current_y += node.rect().height() + 20  # 40 + 20間隔

            elif item.item_type == "transition":
                pre_actions = ensure_list(item.params.get('pre_actions', []))
                else_actions = ensure_list(item.params.get('else_actions', []))
                has_else = item.params.get('has_else', True)
                else_target = item.params.get('else_target', '')

                main_node = FlowNodeItem("transition", item.display_text(), flow_item=item)
                self._setup_node_callbacks(main_node)
                self.scene.addItem(main_node)
                main_node.setPos(30, current_y)
                logger.debug(f"  transition '{item.name}' placed at y={current_y}")

                # 子ノードの開始Y
                child_y = current_y + main_node.rect().height() + 10

                for pre in pre_actions:
                    pre_node = FlowNodeItem("pre_action", pre, flow_item=item)
                    self.scene.addItem(pre_node)
                    pre_node.setPos(60, child_y)
                    logger.debug(f"    child pre_action '{pre}' placed at y={child_y}")
                    child_y += pre_node.rect().height() + 10

                if has_else:
                    else_text = f"else → {else_target}" if else_target else "else（未設定）"
                    else_node = FlowNodeItem("else", else_text, flow_item=item)
                    self.scene.addItem(else_node)
                    else_node.setPos(60, child_y)
                    logger.debug(f"    child else placed at y={child_y}")
                    child_y += else_node.rect().height() + 10

                    for ea in else_actions:
                        ea_node = FlowNodeItem("else_action", ea, flow_item=item)
                        self.scene.addItem(ea_node)
                        ea_node.setPos(90, child_y)
                        logger.debug(f"    child else_action '{ea}' placed at y={child_y}")
                        child_y += ea_node.rect().height() + 10

                # 次のメインノードの開始Yを更新（子ノードの終端＋間隔）
                # child_y は最後の子ノードの次を指しているので、そのまま使う
                current_y = child_y + 20  # 子ノード群の後に間隔を空ける

            else:
                logger.warning(f"Unknown item_type: {item.item_type}")

        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 40))
        self.draft_updated.emit()

        # ログ出力
        self._log_all_nodes_after_rebuild()
        self._log_main_overlaps()

        logger.debug("=== _rebuild END ===")

    def _log_flow_items_before_rebuild(self):
        """再構築前の全フローアイテムの保存位置を出力"""
        logger.debug("--- flow_items before rebuild ---")
        for i, item in enumerate(self.draft.flow_items):
            logger.debug(f"  [{i}] type={item.item_type}, name={item.name}, pos=({item.pos_x},{item.pos_y})")

    def _log_all_nodes_after_rebuild(self):
        """再構築後の全ノード位置とサイズを出力"""
        all_nodes = [item for item in self.scene.items() if isinstance(item, FlowNodeItem)]
        logger.debug("--- All nodes after rebuild ---")
        for node in all_nodes:
            name = node.flow_item.name if node.flow_item else node.item_type
            rect = node.sceneBoundingRect()
            logger.debug(f"  {node.item_type:12s} '{name:15s}' pos=({rect.x():.0f},{rect.y():.0f}) size=({rect.width():.0f}x{rect.height():.0f})")

    def _log_main_overlaps(self):
        """メインノード同士の重なりチェック"""
        main_nodes = [item for item in self.scene.items()
                      if isinstance(item, FlowNodeItem) and item.item_type in ("function", "transition")]

        overlapping_pairs = []
        for i, node1 in enumerate(main_nodes):
            for node2 in main_nodes[i+1:]:
                if node1.sceneBoundingRect().intersects(node2.sceneBoundingRect()):
                    name1 = node1.flow_item.name if node1.flow_item else node1.item_type
                    name2 = node2.flow_item.name if node2.flow_item else node2.item_type
                    overlapping_pairs.append((name1, name2))

        if overlapping_pairs:
            logger.warning("Overlap still exists after rebuild (main nodes):")
            for pair in overlapping_pairs:
                logger.warning(f"  - '{pair[0]}' and '{pair[1]}'")
        else:
            logger.debug("No overlaps after rebuild (main nodes)")

    def _setup_node_callbacks(self, node):
        node.edit_callback = self._on_node_edit_requested
        node.delete_callback = self._on_node_delete_requested
        node.duplicate_callback = self._on_node_duplicate_requested
        node.move_up_callback = self._on_node_move_up_requested
        node.move_down_callback = self._on_node_move_down_requested
        node.move_finished_callback = self._on_node_move_finished

    def _on_node_edit_requested(self, node):
        logger.debug(f"Node edit requested: type={node.item_type}")
        self.node_edit_requested.emit(node)

    def _on_node_delete_requested(self, node):
        logger.debug(f"Node delete requested: type={node.item_type}")
        self.node_delete_requested.emit(node)

    def _on_node_duplicate_requested(self, node):
        logger.debug(f"Node duplicate requested: type={node.item_type}")
        self.node_duplicate_requested.emit(node)

    def _on_node_move_up_requested(self, node):
        logger.debug(f"Node move up requested: type={node.item_type}")
        self.node_move_up_requested.emit(node)

    def _on_node_move_down_requested(self, node):
        logger.debug(f"Node move down requested: type={node.item_type}")
        self.node_move_down_requested.emit(node)

    def _on_node_move_finished(self, node):
        """移動終了時（現在は呼ばれない）"""
        logger.debug("_on_node_move_finished called but node movement is disabled.")

    def auto_align(self):
        """自動整列：フローアイテムの順序に従い、子ノード込みで上から等間隔に配置"""
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
                            new_item = FlowItem(item_type="function", name=name)
                            new_item.pos_x = scene_pos.x()
                            new_item.pos_y = scene_pos.y()
                            self.draft.flow_items.append(new_item)
                            logger.debug(f"Added function to flow: {name}")
                    else:
                        new_item = FlowItem(item_type="function", name=name)
                        new_item.pos_x = scene_pos.x()
                        new_item.pos_y = scene_pos.y()
                        self.draft.flow_items.append(new_item)
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
                    flow_item.pos_x = scene_pos.x()
                    flow_item.pos_y = scene_pos.y()
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