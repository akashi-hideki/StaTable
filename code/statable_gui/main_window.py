# statable_gui/main_window.py
"""
StaTable メインウィンドウ
コード生成機能・検証AI連携機能・共有ライブラリ管理を統合
（複数層対応版）
"""

import sys
import os
import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolButton, QMessageBox,
    QInputDialog, QFileDialog, QDialog, QToolBar
)

from statable.state_machine import StateMachine
from statable.xml_io import (
    project_to_xml, project_from_xml)
from statable.global_defs import GlobalDefinitions
from statable.sample_data import (
    create_sample_state_machine,
    create_sample_global_defs)

from .logger import StaTableLogger
from .traceball import TraceBallWidget
from .config import WINDOW_WIDTH, WINDOW_HEIGHT
from .widgets import StateMachineTab
from .preferences import Preferences
from .global_defs_dialog import GlobalDefinitionsDialog
from .interrupt_handler_edit_dialog import (
    InterruptHandlerEditDialog)
from .event_definition_dialog import EventDefinitionDialog
from .event_delivery_settings_dialog import (
    EventDeliverySettingsDialog)
from .common_widgets import TypeManagerDialog
from .layer_settings_dialog import LayerSettingsDialog

# 共有ライブラリ
try:
    from libcntrl.role_function_library import (
        RoleFunctionLibrary, RoleFunction)
    from libcntrl.condition_library import (
        ConditionLibrary, ConditionTemplate)
    from libcntrl.literal_library import (
        LiteralLibrary, LiteralDefinition)
except ImportError:
    from statable_gui.libcntrl.role_function_library import (
        RoleFunctionLibrary, RoleFunction)
    from statable_gui.libcntrl.condition_library import (
        ConditionLibrary, ConditionTemplate)
    from statable_gui.libcntrl.literal_library import (
        LiteralLibrary, LiteralDefinition)

# コード生成モジュール
sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))),
    'codegen'))

try:
    from codegen.c_code_generator import CCodeGenerator
    from codegen.sample_data import SampleDataGenerator
    from codegen.config import ConfigManager
    from .code_generation_dialog import (
        CodeGenerationDialog, WarningCollector)
    from .code_generation_settings_dialog import (
        CodeGenerationSettingsDialog)
except ImportError:
    from c_code_generator import CCodeGenerator
    from sample_data import SampleDataGenerator
    from config import ConfigManager
    from .code_generation_dialog import (
        CodeGenerationDialog, WarningCollector)
    from .code_generation_settings_dialog import (
        CodeGenerationSettingsDialog)

# 検証・AI連携モジュール
from .validation_dialog import ValidationDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "StaTable - State Transition Editor")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.logger = StaTableLogger()
        self.logger.debug(
            "MainWindow initialization started")

        # 環境設定
        self.prefs = Preferences()

        # コード生成設定マネージャ
        self.config_manager = ConfigManager()

        # グローバル変数・イベントフラグ・割り込み・
        # デバイス・タイマ設定
        self.global_defs = create_sample_global_defs()
        self.global_defs.add_timer_variables()
        StaTableLogger.debug(
            f"MainWindow.global_defs: "
            f"id={id(self.global_defs)}, "
            f"vars={len(self.global_defs.variables)}, "
            f"flags={len(self.global_defs.flags)}, "
            f"interrupts={len(self.global_defs.interrupts)}, "
            f"placeholders={len(self.global_defs.placeholders)}"
        )

        # 共有ライブラリ（プロジェクト全体で共有）
        self.role_function_library = RoleFunctionLibrary()
        self.condition_library = ConditionLibrary()
        self.literal_library = LiteralLibrary()

        # サンプルステートマシンから共有ライブラリへデータ登録
        sample_sm = create_sample_state_machine()

        # ロール関数を共有ライブラリへ登録
        for rf in sample_sm.role_functions.values():
            StaTableLogger.debug(
                f"Attempting to register role function: "
                f"name={rf.name}, title={rf.title}")
            try:
                # RoleFunctionLibrary.add が受け付ける形式に合わせて生成
                lib_rf = RoleFunction(
                    name=rf.name,
                    title=rf.title,
                    description=getattr(rf, 'description', ''),
                )
                self.role_function_library.add(lib_rf)
                StaTableLogger.debug(
                    f"Registered role function to "
                    f"shared library: {rf.name}")
            except Exception as e:
                StaTableLogger.error(
                    f"Failed to register role function "
                    f"{rf.name}: {e}", exc_info=True)

        StaTableLogger.debug(
            f"After role registration: "
            f"roles={len(self.role_function_library.list_all())}")

        # 条件テンプレートを追加
        try:
            self.condition_library.add(ConditionTemplate(
                name="ERROR",
                condition="err_code != 0"))
            self.condition_library.add(ConditionTemplate(
                name="RETRY",
                condition="retry_count < RETRY_THRESHOLD"))
            StaTableLogger.debug(
                "Registered condition templates to "
                "shared library")
        except Exception as e:
            StaTableLogger.warning(
                f"Failed to register condition templates: {e}")

        # リテラルを追加
        try:
            self.literal_library.add(LiteralDefinition(
                name="RETRY_THRESHOLD", value="3",
                literal_type="int",
                description="リトライ回数閾値"))
            self.literal_library.add(LiteralDefinition(
                name="VOLTAGE_MIN", value="2.5",
                literal_type="float",
                description="最小電圧"))
            StaTableLogger.debug(
                "Registered literals to shared library")
        except Exception as e:
            StaTableLogger.warning(
                f"Failed to register literals: {e}")

        # デバッグログ: 共有ライブラリの内容を出力
        StaTableLogger.debug(
            "MainWindow shared libraries initialized: "
            f"roles={len(self.role_function_library.list_all())}, "
            f"conditions={len(self.condition_library.list_all())}, "
            f"literals={len(self.literal_library.list_all())}"
        )

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(
            self.close_tab)
        self.setCentralWidget(self.tab_widget)

        # 「+」ボタン
        self.add_tab_button = QToolButton()
        self.add_tab_button.setText("+")
        self.add_tab_button.setToolTip(
            "Add new state machine")
        self.add_tab_button.clicked.connect(
            self.add_new_tab)
        self.tab_widget.setCornerWidget(
            self.add_tab_button, Qt.TopRightCorner)

        # ダブルクリックでタブ名変更
        self.tab_widget.tabBarDoubleClicked.connect(
            self.rename_tab_at)

        self.create_menus()
        self.create_toolbar()

        self.traceball = TraceBallWidget(self)
        self.addDockWidget(
            Qt.BottomDockWidgetArea, self.traceball)
        self.traceball.hide()

        # 初期タブ
        self.add_state_machine_tab(
            "Application", sample_sm)

        self.logger.debug(
            "MainWindow initialization completed")

    # ------------------------------------------------------------------
    # ツールバー
    # ------------------------------------------------------------------
    def create_toolbar(self):
        toolbar = QToolBar("メインツールバー", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        global_defs_btn = QAction("グローバル定義", self)
        global_defs_btn.setToolTip(
            "グローバル変数・イベントフラグ定義を開く")
        global_defs_btn.triggered.connect(
            self.open_global_defs_dialog)
        toolbar.addAction(global_defs_btn)

        type_defs_btn = QAction("型定義", self)
        type_defs_btn.setToolTip(
            "ユーザー定義型（構造体）を管理")
        type_defs_btn.triggered.connect(
            self.open_type_manager)
        toolbar.addAction(type_defs_btn)

        event_defs_btn = QAction("イベント定義", self)
        event_defs_btn.setToolTip(
            "状態遷移イベント定義を開く")
        event_defs_btn.triggered.connect(
            self.open_event_definition_dialog)
        toolbar.addAction(event_defs_btn)

        delivery_btn = QAction("イベント配送設定", self)
        delivery_btn.setToolTip(
            "イベント配送タイプ設定を開く")
        delivery_btn.triggered.connect(
            self.open_event_delivery_settings)
        toolbar.addAction(delivery_btn)

        interrupt_btn = QAction("割り込み設定", self)
        interrupt_btn.setToolTip(
            "割り込み処理・デバイスリソース・"
            "タイマ設定を開く")
        interrupt_btn.triggered.connect(
            self.open_interrupt_settings)
        toolbar.addAction(interrupt_btn)

        # レイヤ設定
        layer_btn = QAction("レイヤ設定", self)
        layer_btn.setToolTip(
            "層の実行優先度・初期化順序を設定")
        layer_btn.triggered.connect(
            self.open_layer_settings)
        toolbar.addAction(layer_btn)

        toolbar.addSeparator()

        validate_btn = QAction("検証・AI診断", self)
        validate_btn.setToolTip(
            "コード生成前検証・AI連携診断を開く")
        validate_btn.triggered.connect(
            self.open_validation_dialog)
        toolbar.addAction(validate_btn)

        toolbar.addSeparator()

        generate_btn = QAction("コード生成", self)
        generate_btn.setToolTip("Cコードを生成")
        generate_btn.triggered.connect(
            self.open_code_generation_dialog)
        toolbar.addAction(generate_btn)

        gen_settings_btn = QAction("生成設定", self)
        gen_settings_btn.setToolTip(
            "コード生成設定を変更")
        gen_settings_btn.triggered.connect(
            self.open_code_generation_settings)
        toolbar.addAction(gen_settings_btn)

        gen_save_btn = QAction("生成コード保存", self)
        gen_save_btn.setToolTip(
            "生成コードを直接保存")
        gen_save_btn.triggered.connect(
            self.save_generated_code_direct)
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
        new_tab_btn.setToolTip(
            "新しい状態遷移タブを追加")
        new_tab_btn.triggered.connect(self.add_new_tab)
        toolbar.addAction(new_tab_btn)

        rename_btn = QAction("タブ名変更", self)
        rename_btn.setToolTip("現在のタブ名を変更")
        rename_btn.triggered.connect(
            self.rename_current_tab)
        toolbar.addAction(rename_btn)

        toolbar.addSeparator()

        traceball_btn = QAction("ログ表示", self)
        traceball_btn.setCheckable(True)
        traceball_btn.setChecked(False)
        traceball_btn.setToolTip(
            "TraceBallログの表示/非表示")
        traceball_btn.toggled.connect(
            self.toggle_traceball)
        toolbar.addAction(traceball_btn)

        StaTableLogger.debug("Toolbar created")

    # ------------------------------------------------------------------
    # メニュー
    # ------------------------------------------------------------------
    def create_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        open_action = QAction("Open Project...", self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        save_action = QAction("Save Project...", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        rename_action = QAction("Rename Tab...", self)
        rename_action.triggered.connect(
            self.rename_current_tab)
        file_menu.addAction(rename_action)

        file_menu.addSeparator()
        new_tab_action = QAction(
            "New State Machine", self)
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)

        edit_menu = menubar.addMenu("Edit")
        global_defs_action = QAction(
            "Global Definitions...", self)
        global_defs_action.triggered.connect(
            self.open_global_defs_dialog)
        edit_menu.addAction(global_defs_action)

        type_defs_action = QAction(
            "Type Definitions...", self)
        type_defs_action.triggered.connect(
            self.open_type_manager)
        edit_menu.addAction(type_defs_action)

        event_defs_action = QAction(
            "Event Definitions...", self)
        event_defs_action.triggered.connect(
            self.open_event_definition_dialog)
        edit_menu.addAction(event_defs_action)

        delivery_settings_action = QAction(
            "Event Delivery Settings...", self)
        delivery_settings_action.triggered.connect(
            self.open_event_delivery_settings)
        edit_menu.addAction(delivery_settings_action)

        interrupt_action = QAction(
            "Interrupt Settings...", self)
        interrupt_action.triggered.connect(
            self.open_interrupt_settings)
        edit_menu.addAction(interrupt_action)

        # レイヤ設定
        layer_settings_action = QAction(
            "Layer Settings...", self)
        layer_settings_action.triggered.connect(
            self.open_layer_settings)
        edit_menu.addAction(layer_settings_action)

        validation_menu = menubar.addMenu("検証(&V)")
        validate_action = QAction(
            "検証・AI診断...", self)
        validate_action.setShortcut("Ctrl+Shift+V")
        validate_action.triggered.connect(
            self.open_validation_dialog)
        validation_menu.addAction(validate_action)

        code_gen_menu = menubar.addMenu("コード生成(&G)")
        generate_action = QAction(
            "コード生成...", self)
        generate_action.setShortcut("Ctrl+G")
        generate_action.triggered.connect(
            self.open_code_generation_dialog)
        code_gen_menu.addAction(generate_action)

        gen_settings_action = QAction(
            "生成設定...", self)
        gen_settings_action.setShortcut("Ctrl+Shift+G")
        gen_settings_action.triggered.connect(
            self.open_code_generation_settings)
        code_gen_menu.addAction(gen_settings_action)

        code_gen_menu.addSeparator()
        gen_save_action = QAction(
            "生成コードを保存...", self)
        gen_save_action.setShortcut("Ctrl+Shift+S")
        gen_save_action.triggered.connect(
            self.save_generated_code_direct)
        code_gen_menu.addAction(gen_save_action)

        view_menu = menubar.addMenu("View")
        toggle_traceball = QAction("TraceBall", self)
        toggle_traceball.setCheckable(True)
        toggle_traceball.setChecked(False)
        toggle_traceball.toggled.connect(
            self.toggle_traceball)
        view_menu.addAction(toggle_traceball)

    # ------------------------------------------------------------------
    # レイヤ設定
    # ------------------------------------------------------------------
    def open_layer_settings(self):
        """レイヤ設定ダイアログを開く"""
        StaTableLogger.debug(
            "MainWindow.open_layer_settings called")

        layers = []
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if hasattr(tab, 'sm'):
                name = self.tab_widget.tabText(index)
                layers.append((name, tab.sm))
                StaTableLogger.debug(
                    f"  layer[{index}]: name='{name}', "
                    f"priority={getattr(tab.sm, 'layer_priority', 5)}, "
                    f"layer_name='{getattr(tab.sm, 'layer_name', '')}'"
                )

        if not layers:
            QMessageBox.warning(
                self, "Warning",
                "層が定義されていません。")
            return

        StaTableLogger.debug(
            f"Opening LayerSettingsDialog with "
            f"{len(layers)} layers")
        dlg = LayerSettingsDialog(layers, self)
        if dlg.exec() == QDialog.Accepted:
            dlg.apply_settings()
            StaTableLogger.info("Layer settings updated")
            for name, sm in layers:
                StaTableLogger.debug(
                    f"  after apply: '{name}' -> "
                    f"priority={sm.layer_priority}, "
                    f"layer_name='{sm.layer_name}', "
                    f"description='{sm.layer_description}'"
                )
        else:
            StaTableLogger.debug(
                "LayerSettingsDialog cancelled")

    # ------------------------------------------------------------------
    # 各ダイアログ起動メソッド
    # ------------------------------------------------------------------
    def open_type_manager(self):
        StaTableLogger.debug(
            "MainWindow.open_type_manager called")
        dlg = TypeManagerDialog(self, self.global_defs)
        dlg.exec()
        StaTableLogger.debug(
            "TypeManagerDialog closed")

    def open_global_defs_dialog(self):
        StaTableLogger.debug(
            "MainWindow.open_global_defs_dialog called")
        self.global_defs.add_timer_variables()
        dlg = GlobalDefinitionsDialog(
            self.global_defs, self)
        dlg.exec()
        StaTableLogger.debug(
            "GlobalDefinitionsDialog closed")

    def open_event_definition_dialog(self):
        StaTableLogger.debug(
            "MainWindow.open_event_definition_dialog called")

        current_tab = self.tab_widget.currentWidget()
        if current_tab is None or \
           not hasattr(current_tab, 'sm'):
            QMessageBox.warning(
                self, "Warning",
                "状態遷移タブがありません。")
            return
        dlg = EventDefinitionDialog(
            current_tab.sm, self.global_defs, self)
        if dlg.exec() == QDialog.Accepted:
            current_tab.update_mermaid()
            StaTableLogger.info(
                "Event definitions updated")

    def open_event_delivery_settings(self):
        StaTableLogger.debug(
            "MainWindow.open_event_delivery_settings called")
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None or \
           not hasattr(current_tab, 'sm'):
            QMessageBox.warning(
                self, "Warning",
                "状態遷移タブがありません。")
            return

        auto_convert = \
            self.prefs.auto_convert_isr_direct_to_double
        dlg = EventDeliverySettingsDialog(
            current_tab.sm, self.global_defs,
            auto_convert=auto_convert, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.prefs.auto_convert_isr_direct_to_double = \
                dlg.get_auto_convert()
            current_tab.update_mermaid()
            StaTableLogger.info(
                "Event delivery settings updated")

    def open_interrupt_settings(self):
        StaTableLogger.debug(
            "MainWindow.open_interrupt_settings called")

        event_names = []
        role_functions = {}
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if hasattr(tab, 'sm'):
                event_names.extend(tab.sm.events.keys())
                role_functions.update(
                    tab.sm.role_functions)

        event_names = list(set(event_names))
        dlg = InterruptHandlerEditDialog(
            global_defs=self.global_defs,
            event_names=event_names,
            role_functions=role_functions,
            parent=self)
        dlg.exec()
        StaTableLogger.debug(
            "InterruptHandlerEditDialog closed")

    # ------------------------------------------------------------------
    # プロジェクト保存・読込
    # ------------------------------------------------------------------
    def save_project(self):
        """全タブ・グローバル定義・共有ライブラリ・
           プロジェクト設定を保存"""
        StaTableLogger.debug(
            "MainWindow.save_project called")

        tabs = []
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            name = self.tab_widget.tabText(index)
            tabs.append((name, tab.sm))

        last_dir = self.prefs.last_project_dir
        default_path = str(
            Path(last_dir) / "project.xml") \
            if last_dir else "project.xml"

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project", default_path,
            "XML files (*.xml)")
        if not filepath:
            StaTableLogger.debug("Save cancelled")
            return
        try:
            # ★ プロジェクト設定を収集
            config = self.config_manager.get_config()
            project_settings = {
                'project_name': config.project_name,
                'table_type': config.table_type,
                'generation_style':
                    config.generation_style,
                'os_type': config.os_type,
                'folder_structure':
                    config.folder_structure,
                'include_dir_name':
                    config.include_dir_name,
                'source_dir_name':
                    config.source_dir_name,
                'common_dir_name':
                    config.common_dir_name,
                'project_dir_name':
                    config.project_dir_name,
                'generate_super_include':
                    config.generate_super_include,
                'super_include_file':
                    config.super_include_file,
                'external_includes':
                    list(config.external_includes),
                'external_includes_in_super':
                    config.external_includes_in_super,
                'external_includes_in_role':
                    config.external_includes_in_role,
                'external_includes_in_transitions':
                    config.external_includes_in_transitions,
                'external_includes_in_common':
                    config.external_includes_in_common,
                'max_consecutive_pending_events':
                    config.max_consecutive_pending_events,
            }
            StaTableLogger.debug(
                f"Project settings: {project_settings}")

            project_to_xml(
                tabs,
                self.global_defs,
                filepath,
                role_function_library=(
                    self.role_function_library),
                condition_library=self.condition_library,
                literal_library=self.literal_library,
                project_settings=project_settings,
            )
            self.prefs.last_project_dir = str(
                Path(filepath).parent)
            self.logger.info(
                f"Project saved to {filepath}")
        except Exception as e:
            import traceback
            self.logger.error(
                f"Failed to save project: "
                f"{filepath}, error: {e}\n"
                f"{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error",
                f"Failed to save project:\n{e}")

    def open_project(self):
        """プロジェクト全体を読み込む"""
        StaTableLogger.debug(
            "MainWindow.open_project called")

        last_dir = self.prefs.last_project_dir
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project", last_dir,
            "XML files (*.xml)")
        if not filepath:
            StaTableLogger.debug("Open cancelled")
            return
        try:
            StaTableLogger.debug(
                f"Calling project_from_xml: {filepath}")
            (tabs, global_defs, role_lib,
             cond_lib, lit_lib,
             project_settings) = project_from_xml(filepath)

            StaTableLogger.debug(
                f"Loaded: tabs={len(tabs)}, "
                f"project_settings={project_settings}"
            )

            self.close_all_tabs()
            for name, sm in tabs:
                self.add_state_machine_tab(name, sm)

            self.global_defs = global_defs
            self.global_defs.add_timer_variables()

            # ★ 共有ライブラリも置き換え
            if role_lib is not None:
                self.role_function_library = role_lib
            if cond_lib is not None:
                self.condition_library = cond_lib
            if lit_lib is not None:
                self.literal_library = lit_lib

            # ★ プロジェクト設定を反映
            if project_settings:
                config = self.config_manager.get_config()
                for key, value in project_settings.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                        StaTableLogger.debug(
                            f"  config.{key} = {value}")
                self.config_manager.set_config(config)

            # 既存タブのライブラリ参照を更新
            for index in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(index)
                if hasattr(tab, 'role_function_library'):
                    tab.role_function_library = \
                        self.role_function_library
                if hasattr(tab, 'condition_library'):
                    tab.condition_library = \
                        self.condition_library
                if hasattr(tab, 'literal_library'):
                    tab.literal_library = \
                        self.literal_library
                if hasattr(tab, 'table'):
                    tab.table.role_function_library = \
                        self.role_function_library
                    tab.table.condition_library = \
                        self.condition_library
                    tab.table.literal_library = \
                        self.literal_library

            self.prefs.last_project_dir = str(
                Path(filepath).parent)
            self.logger.info(
                f"Project loaded from {filepath}")
        except Exception as e:
            import traceback
            self.logger.error(
                f"Failed to open project: "
                f"{filepath}, error: {e}\n"
                f"{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error",
                f"Failed to open project:\n{e}")

    def close_all_tabs(self):
        StaTableLogger.debug("close_all_tabs called")
        while self.tab_widget.count() > 0:
            widget = self.tab_widget.widget(0)
            self.tab_widget.removeTab(0)
            widget.deleteLater()

    # ------------------------------------------------------------------
    # タブ管理
    # ------------------------------------------------------------------
    def rename_current_tab(self):
        index = self.tab_widget.currentIndex()
        if index >= 0:
            self.rename_tab_at(index)

    def rename_tab_at(self, index: int):
        if index < 0:
            return
        current_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(
            self, "Rename Tab",
            "Enter new tab name:",
            text=current_name)
        if ok and new_name.strip():
            self.tab_widget.setTabText(
                index, new_name.strip())
            self.logger.info(
                f"Tab renamed: {current_name} -> "
                f"{new_name.strip()}")

    def add_new_tab(self):
        name, ok = QInputDialog.getText(
            self, "New State Machine",
            "Enter tab name:")
        if ok and name.strip():
            sm = StateMachine()
            self.add_state_machine_tab(name.strip(), sm)
            self.logger.info(
                f"New tab added: {name.strip()}")

    def add_state_machine_tab(self, name: str,
                              sm: StateMachine):
        StaTableLogger.debug(
            f"add_state_machine_tab: name={name}, "
            f"layer_name='{getattr(sm, 'layer_name', '')}', "
            f"layer_priority={getattr(sm, 'layer_priority', 5)}, "
            f"roles={len(self.role_function_library.list_all())}"
        )

        # 層名未設定ならタブ名をデフォルト層名に
        if not getattr(sm, 'layer_name', ''):
            sm.layer_name = name

        tab = StateMachineTab(
            sm,
            global_defs=self.global_defs,
            role_function_library=self.role_function_library,
            condition_library=self.condition_library,
            literal_library=self.literal_library)
        idx = self.tab_widget.addTab(tab, name)
        self.tab_widget.setCurrentIndex(idx)
        self.logger.debug(
            f"Tab '{name}' added at index {idx} "
            f"(layer_name='{sm.layer_name}')")

    def close_tab(self, index: int):
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(
                self, "Warning",
                "At least one tab is required.")
            return
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        widget.deleteLater()
        self.logger.info(
            f"Tab closed at index {index}")

    # ------------------------------------------------------------------
    # ログ・検証・コード生成
    # ------------------------------------------------------------------
    def toggle_traceball(self, checked: bool):
        if checked:
            self.traceball.show()
            self.logger.debug("TraceBall shown")
        else:
            self.traceball.hide()
            self.logger.debug("TraceBall hidden")

    def _get_current_state_machine(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab is not None and \
           hasattr(current_tab, 'sm'):
            return current_tab.sm
        return None

    def _get_current_data(self):
        sm = self._get_current_state_machine()
        if sm is not None and self.global_defs is not None:
            return sm, self.global_defs

        sample_gen = SampleDataGenerator()
        return sample_gen.get_sample_data()

    # ★ 複数層対応ヘルパー
    def _get_all_layers(self):
        """全タブの (name, sm) リストを優先度昇順で返す"""
        layers = []
        for index in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(index)
            if hasattr(tab, 'sm'):
                name = self.tab_widget.tabText(index)
                layers.append((name, tab.sm))
        layers.sort(
            key=lambda x: getattr(x[1], 'layer_priority', 5)
        )
        return layers

    def open_validation_dialog(self):
        StaTableLogger.debug(
            "MainWindow.open_validation_dialog called")
        sm, gd = self._get_current_data()
        dialog = ValidationDialog(sm, gd, self)
        dialog.exec()
        StaTableLogger.debug(
            "ValidationDialog closed")

    def open_code_generation_dialog(self):
        StaTableLogger.debug(
            "MainWindow.open_code_generation_dialog called")

        # ★ 全タブを層として収集
        layers = self._get_all_layers()
        if layers:
            primary_sm = layers[0][1]
            gd = self.global_defs
        else:
            sample_gen = SampleDataGenerator()
            primary_sm, gd = sample_gen.get_sample_data()
            layers = [(getattr(primary_sm, 'layer_name', ''),
                       primary_sm)]

        dialog = CodeGenerationDialog(
            state_machine=primary_sm,
            global_defs=gd,
            parent=self,
            role_function_library=(
                self.role_function_library),
        )
        # ★ 全層を渡す
        dialog.all_layers = layers
        dialog.config_manager = self.config_manager
        dialog._load_config_to_ui()
        dialog.exec()
        StaTableLogger.debug(
            "CodeGenerationDialog closed")

    def open_code_generation_settings(self):
        StaTableLogger.debug(
            "MainWindow.open_code_generation_settings called")
        dialog = CodeGenerationSettingsDialog(
            config_manager=self.config_manager,
            parent=self)
        dialog.exec()
        StaTableLogger.debug(
            "CodeGenerationSettingsDialog closed")

    # ------------------------------------------------------------------
    # 生成コード直接保存（複数層 + 警告収集対応）
    # ------------------------------------------------------------------
    def save_generated_code_direct(self):
        StaTableLogger.debug(
            "MainWindow.save_generated_code_direct called")
        config = self.config_manager.get_config()
        output_dir = config.output_directory

        if not output_dir:
            QMessageBox.warning(
                self, "警告",
                "出力先ディレクトリが設定されていません。\n"
                "先に設定ダイアログで出力先を"
                "指定してください。")
            self.open_code_generation_settings()
            config = self.config_manager.get_config()
            output_dir = config.output_directory
            if not output_dir:
                return

        # ★ 全タブを層として収集
        layers = self._get_all_layers()
        if not layers:
            QMessageBox.warning(
                self, "警告", "タブがありません。")
            return

        global_defs = self.global_defs
        if global_defs is None:
            sample_gen = SampleDataGenerator()
            _, global_defs = sample_gen.get_sample_data()

        collector = WarningCollector()
        root_logger = logging.getLogger()
        root_logger.addHandler(collector)

        saved_files = []
        try:
            generator = CCodeGenerator(config=config)
            # ★ 複数層生成
            generated_files = generator.generate_all_layers(
                layers,
                global_defs,
                role_function_library=(
                    self.role_function_library),
            )
            os.makedirs(output_dir, exist_ok=True)

            if config.save_with_merge:
                saved_files = (
                    generator
                    .save_generated_code_with_merge(
                        generated_files, output_dir))
            else:
                saved_files = (
                    generator.save_generated_code(
                        generated_files, output_dir))

            StaTableLogger.info(
                f"{len(saved_files)} files saved to "
                f"{output_dir} ({len(layers)} layers)")

        except Exception as e:
            QMessageBox.critical(
                self, "エラー",
                f"コード生成に失敗しました:\n{e}")
            StaTableLogger.error(
                f"Code generation failed: {e}")
            return
        finally:
            root_logger.removeHandler(collector)

        QMessageBox.information(
            self, "保存完了",
            f"{len(saved_files)}ファイルを保存しました。\n"
            f"層数: {len(layers)}\n\n"
            f"出力先: {output_dir}")

        if collector.records:
            seen = set()
            unique = []
            for r in collector.records:
                if r not in seen:
                    seen.add(r)
                    unique.append(r)
            QMessageBox.warning(
                self, "生成時の警告",
                "以下の警告が発生しました:\n\n"
                + "\n".join(f"・{m}" for m in unique))