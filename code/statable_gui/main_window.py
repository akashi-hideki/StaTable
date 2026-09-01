# statable_gui/main_window.py
"""
StaTable メインウィンドウ
コード生成機能を統合
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolButton, QMessageBox, QInputDialog,
    QFileDialog, QDialog, QToolBar
)

from statable.state_machine import StateMachine
from statable.xml_io import project_to_xml, project_from_xml
from statable.global_defs import GlobalDefinitions
from statable.sample_data import create_sample_state_machine, create_sample_global_defs

from .logger import StaTableLogger
from .traceball import TraceBallWidget
from .config import WINDOW_WIDTH, WINDOW_HEIGHT
from .widgets import StateMachineTab
from .preferences import Preferences
from .global_defs_dialog import GlobalDefinitionsDialog
from .interrupt_handler_edit_dialog import InterruptHandlerEditDialog
from .event_definition_dialog import EventDefinitionDialog
from .event_delivery_settings_dialog import EventDeliverySettingsDialog
from .common_widgets import TypeManagerDialog

# コード生成モジュール
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen'))

try:
    from codegen.c_code_generator import CCodeGenerator
    from codegen.sample_data import SampleDataGenerator
    from codegen.config import ConfigManager
    from .code_generation_dialog import CodeGenerationDialog
    from .code_generation_settings_dialog import CodeGenerationSettingsDialog
except ImportError:
    from c_code_generator import CCodeGenerator
    from sample_data import SampleDataGenerator
    from config import ConfigManager
    from .code_generation_dialog import CodeGenerationDialog
    from .code_generation_settings_dialog import CodeGenerationSettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StaTable - State Transition Editor")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.logger = StaTableLogger()
        self.logger.debug("MainWindow initialization started")

        # 環境設定
        self.prefs = Preferences()

        # コード生成設定マネージャ
        self.config_manager = ConfigManager()

        # グローバル変数・イベントフラグ・割り込み・デバイス・タイマ設定
        self.global_defs = create_sample_global_defs()
        self.global_defs.add_timer_variables()
        StaTableLogger.debug(
            f"MainWindow.global_defs: id={id(self.global_defs)}, "
            f"vars={len(self.global_defs.variables)}, "
            f"flags={len(self.global_defs.flags)}, "
            f"interrupts={len(self.global_defs.interrupts)}, "
            f"placeholders={len(self.global_defs.placeholders)}"
        )

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tab_widget)

        # 「+」ボタン
        self.add_tab_button = QToolButton()
        self.add_tab_button.setText("+")
        self.add_tab_button.setToolTip("Add new state machine")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)

        # ダブルクリックでタブ名変更
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_tab_at)

        self.create_menus()
        self.create_toolbar()

        self.traceball = TraceBallWidget(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.traceball)
        self.traceball.hide()

        # 初期タブ
        sample_sm = create_sample_state_machine()
        self.add_state_machine_tab("Application", sample_sm)

        self.logger.debug("MainWindow initialization completed")

    def create_toolbar(self):
        toolbar = QToolBar("メインツールバー", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        global_defs_btn = QAction("グローバル定義", self)
        global_defs_btn.setToolTip("グローバル変数・イベントフラグ定義を開く")
        global_defs_btn.triggered.connect(self.open_global_defs_dialog)
        toolbar.addAction(global_defs_btn)

        type_defs_btn = QAction("型定義", self)
        type_defs_btn.setToolTip("ユーザー定義型（構造体）を管理")
        type_defs_btn.triggered.connect(self.open_type_manager)
        toolbar.addAction(type_defs_btn)

        event_defs_btn = QAction("イベント定義", self)
        event_defs_btn.setToolTip("状態遷移イベント定義を開く")
        event_defs_btn.triggered.connect(self.open_event_definition_dialog)
        toolbar.addAction(event_defs_btn)

        delivery_btn = QAction("イベント配送設定", self)
        delivery_btn.setToolTip("イベント配送タイプ設定を開く")
        delivery_btn.triggered.connect(self.open_event_delivery_settings)
        toolbar.addAction(delivery_btn)

        interrupt_btn = QAction("割り込み設定", self)
        interrupt_btn.setToolTip("割り込み処理・デバイスリソース・タイマ設定を開く")
        interrupt_btn.triggered.connect(self.open_interrupt_settings)
        toolbar.addAction(interrupt_btn)

        toolbar.addSeparator()

        # コード生成ボタン
        generate_btn = QAction("コード生成", self)
        generate_btn.setToolTip("Cコードを生成")
        generate_btn.triggered.connect(self.open_code_generation_dialog)
        toolbar.addAction(generate_btn)

        gen_settings_btn = QAction("生成設定", self)
        gen_settings_btn.setToolTip("コード生成設定を変更")
        gen_settings_btn.triggered.connect(self.open_code_generation_settings)
        toolbar.addAction(gen_settings_btn)

        gen_save_btn = QAction("生成コード保存", self)
        gen_save_btn.setToolTip("生成コードを直接保存")
        gen_save_btn.triggered.connect(self.save_generated_code_direct)
        toolbar.addAction(gen_save_btn)

        toolbar.addSeparator()

        open_btn = QAction("開く", self)
        open_btn.setToolTip("プロジェクトを開く")
        open_btn.triggered.connect(self.open_project)
        toolbar.addAction(open_btn)

        save_btn = QAction("保存", self)
        save_btn.setToolTip("プロジェクトを保存")
        save_btn.triggered.connect(self.save_project)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        new_tab_btn = QAction("新規タブ", self)
        new_tab_btn.setToolTip("新しい状態遷移タブを追加")
        new_tab_btn.triggered.connect(self.add_new_tab)
        toolbar.addAction(new_tab_btn)

        rename_btn = QAction("タブ名変更", self)
        rename_btn.setToolTip("現在のタブ名を変更")
        rename_btn.triggered.connect(self.rename_current_tab)
        toolbar.addAction(rename_btn)

        toolbar.addSeparator()

        traceball_btn = QAction("ログ表示", self)
        traceball_btn.setCheckable(True)
        traceball_btn.setChecked(False)
        traceball_btn.setToolTip("TraceBallログの表示/非表示")
        traceball_btn.toggled.connect(self.toggle_traceball)
        toolbar.addAction(traceball_btn)

        StaTableLogger.debug("Toolbar created")

    def create_menus(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open Project...", self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        save_action = QAction("Save Project...", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        rename_action = QAction("Rename Tab...", self)
        rename_action.triggered.connect(self.rename_current_tab)
        file_menu.addAction(rename_action)

        file_menu.addSeparator()
        new_tab_action = QAction("New State Machine", self)
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        global_defs_action = QAction("Global Definitions...", self)
        global_defs_action.triggered.connect(self.open_global_defs_dialog)
        edit_menu.addAction(global_defs_action)

        type_defs_action = QAction("Type Definitions...", self)
        type_defs_action.triggered.connect(self.open_type_manager)
        edit_menu.addAction(type_defs_action)

        event_defs_action = QAction("Event Definitions...", self)
        event_defs_action.triggered.connect(self.open_event_definition_dialog)
        edit_menu.addAction(event_defs_action)

        delivery_settings_action = QAction("Event Delivery Settings...", self)
        delivery_settings_action.triggered.connect(self.open_event_delivery_settings)
        edit_menu.addAction(delivery_settings_action)

        interrupt_action = QAction("Interrupt Settings...", self)
        interrupt_action.triggered.connect(self.open_interrupt_settings)
        edit_menu.addAction(interrupt_action)

        # Code Generation menu
        code_gen_menu = menubar.addMenu("コード生成(&G)")

        generate_action = QAction("コード生成...", self)
        generate_action.setShortcut("Ctrl+G")
        generate_action.triggered.connect(self.open_code_generation_dialog)
        code_gen_menu.addAction(generate_action)

        gen_settings_action = QAction("生成設定...", self)
        gen_settings_action.setShortcut("Ctrl+Shift+G")
        gen_settings_action.triggered.connect(self.open_code_generation_settings)
        code_gen_menu.addAction(gen_settings_action)

        code_gen_menu.addSeparator()

        gen_save_action = QAction("生成コードを保存...", self)
        gen_save_action.setShortcut("Ctrl+Shift+S")
        gen_save_action.triggered.connect(self.save_generated_code_direct)
        code_gen_menu.addAction(gen_save_action)

        # View menu
        view_menu = menubar.addMenu("View")
        toggle_traceball = QAction("TraceBall", self)
        toggle_traceball.setCheckable(True)
        toggle_traceball.setChecked(False)
        toggle_traceball.toggled.connect(self.toggle_traceball)
        view_menu.addAction(toggle_traceball)

    # ===== 既存のメソッド =====

    def open_type_manager(self):
        """ユーザー定義型管理ダイアログを開く"""
        StaTableLogger.debug("MainWindow.open_type_manager called")
        dlg = TypeManagerDialog(self, self.global_defs)
        dlg.exec()
        StaTableLogger.debug("TypeManagerDialog closed")

    def open_global_defs_dialog(self):
        """グローバル変数・イベントフラグ定義ダイアログを開く"""
        StaTableLogger.debug("MainWindow.open_global_defs_dialog called")
        self.global_defs.add_timer_variables()
        dlg = GlobalDefinitionsDialog(self.global_defs, self)
        dlg.exec()
        StaTableLogger.debug("GlobalDefinitionsDialog closed")

    def open_event_definition_dialog(self):
        """状態遷移イベント定義ダイアログを開く"""
        StaTableLogger.debug("MainWindow.open_event_definition_dialog called")

        # 現在のタブの StateMachine を取得
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None or not hasattr(current_tab, 'sm'):
            QMessageBox.warning(self, "Warning", "状態遷移タブがありません。")
            return
        dlg = EventDefinitionDialog(current_tab.sm, self.global_defs, self)
        if dlg.exec() == QDialog.Accepted:
            current_tab.update_mermaid()
            StaTableLogger.info("Event definitions updated")

    def open_event_delivery_settings(self):
        """イベント配送設定ダイアログを開く"""
        StaTableLogger.debug("MainWindow.open_event_delivery_settings called")
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None or not hasattr(current_tab, 'sm'):
            QMessageBox.warning(self, "Warning", "状態遷移タブがありません。")
            return

        auto_convert = self.prefs.auto_convert_isr_direct_to_double
        dlg = EventDeliverySettingsDialog(
            current_tab.sm, self.global_defs,
            auto_convert=auto_convert, parent=self
        )
        if dlg.exec() == QDialog.Accepted:
            self.prefs.auto_convert_isr_direct_to_double = dlg.get_auto_convert()
            current_tab.update_mermaid()
            StaTableLogger.info("Event delivery settings updated")

    def open_interrupt_settings(self):
        """割り込み処理・デバイスリソース・タイマ設定ダイアログを開く"""
        StaTableLogger.debug("MainWindow.open_interrupt_settings called")

        event_names = []
        role_functions = {}
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if hasattr(tab, 'sm'):
                event_names.extend(tab.sm.events.keys())
                role_functions.update(tab.sm.role_functions)

        event_names = list(set(event_names))
        dlg = InterruptHandlerEditDialog(
            global_defs=self.global_defs,
            event_names=event_names,
            role_functions=role_functions,
            parent=self
        )
        dlg.exec()
        StaTableLogger.debug("InterruptHandlerEditDialog closed")

    def save_project(self):
        """全タブとグローバル定義を1つのXMLファイルに保存する"""
        tabs = []
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            name = self.tab_widget.tabText(index)
            tabs.append((name, tab.sm))

        last_dir = self.prefs.last_project_dir
        default_path = str(Path(last_dir) / "project.xml") if last_dir else "project.xml"

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project", default_path, "XML files (*.xml)"
        )
        if not filepath:
            return
        try:
            project_to_xml(tabs, self.global_defs, filepath)
            self.prefs.last_project_dir = str(Path(filepath).parent)
            self.logger.info(f"Project saved to {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{e}")
            self.logger.error(f"Failed to save project: {filepath}, error: {e}")

    def open_project(self):
        """XMLファイルからプロジェクト全体（タブ＋グローバル定義）を読み込む"""
        last_dir = self.prefs.last_project_dir
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project", last_dir, "XML files (*.xml)"
        )
        if not filepath:
            return
        try:
            tabs, global_defs = project_from_xml(filepath)
            self.close_all_tabs()
            for name, sm in tabs:
                self.add_state_machine_tab(name, sm)
            self.global_defs = global_defs
            self.global_defs.add_timer_variables()
            self.prefs.last_project_dir = str(Path(filepath).parent)
            self.logger.info(f"Project loaded from {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{e}")
            self.logger.error(f"Failed to open project: {filepath}, error: {e}")

    def close_all_tabs(self):
        while self.tab_widget.count() > 0:
            widget = self.tab_widget.widget(0)
            self.tab_widget.removeTab(0)
            widget.deleteLater()

    def rename_current_tab(self):
        index = self.tab_widget.currentIndex()
        if index >= 0:
            self.rename_tab_at(index)

    def rename_tab_at(self, index: int):
        if index < 0:
            return
        current_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(
            self, "Rename Tab", "Enter new tab name:", text=current_name
        )
        if ok and new_name.strip():
            self.tab_widget.setTabText(index, new_name.strip())
            self.logger.info(f"Tab renamed: {current_name} -> {new_name.strip()}")

    def add_new_tab(self):
        name, ok = QInputDialog.getText(
            self, "New State Machine", "Enter tab name:"
        )
        if ok and name.strip():
            sm = StateMachine()
            self.add_state_machine_tab(name.strip(), sm)
            self.logger.info(f"New tab added: {name.strip()}")

    def add_state_machine_tab(self, name: str, sm: StateMachine):
        tab = StateMachineTab(sm, global_defs=self.global_defs)
        idx = self.tab_widget.addTab(tab, name)
        self.tab_widget.setCurrentIndex(idx)
        self.logger.debug(f"Tab '{name}' added at index {idx}")

    def close_tab(self, index: int):
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(self, "Warning", "At least one tab is required.")
            return
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        widget.deleteLater()
        self.logger.info(f"Tab closed at index {index}")

    def toggle_traceball(self, checked: bool):
        if checked:
            self.traceball.show()
            self.logger.debug("TraceBall shown")
        else:
            self.traceball.hide()
            self.logger.debug("TraceBall hidden")

    # ===== コード生成関連メソッド =====

    def _get_current_state_machine(self):
        """現在のタブからStateMachineを取得"""
        current_tab = self.tab_widget.currentWidget()
        if current_tab is not None and hasattr(current_tab, 'sm'):
            return current_tab.sm
        return None

    def _get_current_data(self):
        """現在のタブからデータを取得（フォールバックあり）"""
        sm = self._get_current_state_machine()
        if sm is not None and self.global_defs is not None:
            return sm, self.global_defs
        
        # サンプルデータを使用
        sample_gen = SampleDataGenerator()
        return sample_gen.get_sample_data()

    def open_code_generation_dialog(self):
        """コード生成ダイアログを開く"""
        StaTableLogger.debug("MainWindow.open_code_generation_dialog called")
        
        state_machine, global_defs = self._get_current_data()
        
        dialog = CodeGenerationDialog(
            state_machine=state_machine,
            global_defs=global_defs,
            parent=self
        )
        
        # 設定マネージャを共有
        dialog.config_manager = self.config_manager
        dialog._load_config_to_ui()
        
        dialog.exec()
        StaTableLogger.debug("CodeGenerationDialog closed")

    def open_code_generation_settings(self):
        """コード生成設定ダイアログを開く"""
        StaTableLogger.debug("MainWindow.open_code_generation_settings called")
        
        dialog = CodeGenerationSettingsDialog(
            config_manager=self.config_manager,
            parent=self
        )
        dialog.exec()
        StaTableLogger.debug("CodeGenerationSettingsDialog closed")

    def save_generated_code_direct(self):
        """生成コードを直接保存（ダイアログなし）"""
        StaTableLogger.debug("MainWindow.save_generated_code_direct called")
        
        state_machine, global_defs = self._get_current_data()
        
        config = self.config_manager.get_config()
        output_dir = config.output_directory
        
        if not output_dir:
            QMessageBox.warning(self, "警告", 
                "出力先ディレクトリが設定されていません。\n先に設定ダイアログで出力先を指定してください。")
            self.open_code_generation_settings()
            config = self.config_manager.get_config()
            output_dir = config.output_directory
            if not output_dir:
                return
        
        try:
            generator = CCodeGenerator(config=config)
            generated_files = generator.generate_all(state_machine, global_defs)
            
            os.makedirs(output_dir, exist_ok=True)
            
            if config.save_with_merge:
                saved_files = generator.save_generated_code_with_merge(generated_files, output_dir)
            else:
                saved_files = generator.save_generated_code(generated_files, output_dir)
            
            StaTableLogger.info(f"{len(saved_files)} files saved to {output_dir}")
            
            QMessageBox.information(self, "保存完了", 
                f"{len(saved_files)}ファイルを保存しました。\n\n出力先: {output_dir}")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"コード生成に失敗しました:\n{e}")
            StaTableLogger.error(f"Code generation failed: {e}")