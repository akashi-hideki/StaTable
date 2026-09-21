# statable_gui/main_window.py
"""
StaTable main window
Integrates code generation, validation/AI integration, and shared library
management (multi-layer support).

Version History
---------------
v1.5    - Pass namespace in RoleFunction registration in __init__ (bug #86)

v2.3    - Add New Project feature (F-15).
          * new_project(): reset to an empty Application layer.
          * _maybe_save(): unified unsaved-changes confirmation.
          * closeEvent(): prompt on window close.
          * _update_window_title(): 'Untitled[*] - StaTable' format.
          * _on_tab_data_modified(): slot for StateMachineTab.dataModified.
          * save_project() now returns bool (success / cancel / failure).
          * open_project() prompts via _maybe_save() at the beginning.
          * add_state_machine_tab() connects dataModified.
          * Tab add / rename / close set windowModified(True).

v2.4    - Provide all layer names to StateMachineTab (v3.11).
          * _get_all_layer_names(): new helper returning every tab
            name (= every layer name in the project).
          * add_state_machine_tab(): pass `layer_names_provider` to
            StateMachineTab, which forwards it to SettingsPanel so
            the namespace combo box (inline editor + RoleFunctionDialog)
            lists all layers, not just the current tab's layer.
          * [C-19 fix] Add missing '\\n' in the output-directory
            warning message so "settings.Please specify." is split
            correctly across two lines.
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

# Shared library (v1.5: integrated into statable_gui/libcntrl)
from statable_gui.libcntrl.role_function_library import (
    RoleFunctionLibrary, RoleFunction)
from statable_gui.libcntrl.condition_library import (
    ConditionLibrary, ConditionTemplate)
from statable_gui.libcntrl.literal_library import (
    LiteralLibrary, LiteralDefinition)
# Code generation module
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

# Validation / AI integration module
from .validation_dialog import ValidationDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "StaTable - State Transition Editor[*]")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.logger = StaTableLogger()
        self.logger.debug(
            "MainWindow initialization started")

        # Preferences
        self.prefs = Preferences()

        # Code generation settings manager
        self.config_manager = ConfigManager()

        # Global variables, event flags, interrupts,
        # Device / timer settings
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

        #Shared library (across project)
        self.role_function_library = RoleFunctionLibrary()
        self.condition_library = ConditionLibrary()
        self.literal_library = LiteralLibrary()

        # Register data from the sample state machine into the shared library
        sample_sm = create_sample_state_machine()

        # ==========================================================
        # [v1.5 fix] register role function into shared library
        #   Also pass namespace (v1.4 section 9.6 #69 / v1.5 #86)
        # ==========================================================
        for rf in sample_sm.role_functions.values():
            StaTableLogger.debug(
                f"Attempting to register role function: "
                f"name={rf.name}, "
                f"namespace={getattr(rf, 'namespace', '')}, "
                f"title={rf.title}")
            try:
                lib_rf = RoleFunction(
                    name=rf.name,
                    namespace=getattr(rf, 'namespace', '') or '',   # ★ v1.5 Add
                    title=rf.title,
                    description=getattr(rf, 'description', ''),
                )
                self.role_function_library.add(lib_rf)
                StaTableLogger.debug(
                    f"Registered role function to "
                    f"shared library: {lib_rf.qualified_name}")
            except Exception as e:
                StaTableLogger.error(
                    f"Failed to register role function "
                    f"{rf.name}: {e}", exc_info=True)

        StaTableLogger.debug(
            f"After role registration: "
            f"roles={len(self.role_function_library.list_all())}")

        # Add condition template
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

        # Add literal
        try:
            self.literal_library.add(LiteralDefinition(
                name="RETRY_THRESHOLD", value="3",
                literal_type="int",
                description="Retry count threshold"))
            self.literal_library.add(LiteralDefinition(
                name="VOLTAGE_MIN", value="2.5",
                literal_type="float",
                description="Min voltage"))
            StaTableLogger.debug(
                "Registered literals to shared library")
        except Exception as e:
            StaTableLogger.warning(
                f"Failed to register literals: {e}")

        #Debug log: output shared library content
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

        # "+" button
        self.add_tab_button = QToolButton()
        self.add_tab_button.setText("+")
        self.add_tab_button.setToolTip(
            "Add new state machine")
        self.add_tab_button.clicked.connect(
            self.add_new_tab)
        self.tab_widget.setCornerWidget(
            self.add_tab_button, Qt.TopRightCorner)

        #Double-click to rename tab
        self.tab_widget.tabBarDoubleClicked.connect(
            self.rename_tab_at)

        self.create_menus()
        self.create_toolbar()

        self.traceball = TraceBallWidget(self)
        self.addDockWidget(
            Qt.BottomDockWidgetArea, self.traceball)
        self.traceball.hide()

        # Initial tab
        self.add_state_machine_tab(
            "Application", sample_sm)

        self.logger.debug(
            "MainWindow initialization completed")

    # ------------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------------
    def create_toolbar(self):
        toolbar = QToolBar("Main toolbar", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        global_defs_btn = QAction("Global definitions", self)
        global_defs_btn.setToolTip(
            "Open global variables / event flag definitions")
        global_defs_btn.triggered.connect(
            self.open_global_defs_dialog)
        toolbar.addAction(global_defs_btn)

        type_defs_btn = QAction("Type definitions", self)
        type_defs_btn.setToolTip(
            "Manage user-defined types (structs)")
        type_defs_btn.triggered.connect(
            self.open_type_manager)
        toolbar.addAction(type_defs_btn)

        event_defs_btn = QAction("Event definitions", self)
        event_defs_btn.setToolTip(
            "Open state transition event definitions")
        event_defs_btn.triggered.connect(
            self.open_event_definition_dialog)
        toolbar.addAction(event_defs_btn)

        delivery_btn = QAction("Event delivery settings", self)
        delivery_btn.setToolTip(
            "Open event delivery type settings")
        delivery_btn.triggered.connect(
            self.open_event_delivery_settings)
        toolbar.addAction(delivery_btn)

        interrupt_btn = QAction("Interrupt settings", self)
        interrupt_btn.setToolTip(
            "Interrupt handler, device resources,"
            "Open timer settings")
        interrupt_btn.triggered.connect(
            self.open_interrupt_settings)
        toolbar.addAction(interrupt_btn)

        # Layer settings
        layer_btn = QAction("Layer settings", self)
        layer_btn.setToolTip(
            "Set layer execution priority and initialization order")
        layer_btn.triggered.connect(
            self.open_layer_settings)
        toolbar.addAction(layer_btn)

        toolbar.addSeparator()

        validate_btn = QAction("Validation / AI diagnosis", self)
        validate_btn.setToolTip(
            "Open pre-generation validation / AI diagnosis")
        validate_btn.triggered.connect(
            self.open_validation_dialog)
        toolbar.addAction(validate_btn)

        toolbar.addSeparator()

        generate_btn = QAction("Code generation", self)
        generate_btn.setToolTip("Generate C code")
        generate_btn.triggered.connect(
            self.open_code_generation_dialog)
        toolbar.addAction(generate_btn)

        gen_settings_btn = QAction("Generation settings", self)
        gen_settings_btn.setToolTip(
            "Change code generation settings")
        gen_settings_btn.triggered.connect(
            self.open_code_generation_settings)
        toolbar.addAction(gen_settings_btn)

        gen_save_btn = QAction("Save generated code", self)
        gen_save_btn.setToolTip(
            "Directly save generated code")
        gen_save_btn.triggered.connect(
            self.save_generated_code_direct)
        toolbar.addAction(gen_save_btn)

        toolbar.addSeparator()

        open_btn = QAction("Open", self)
        open_btn.setToolTip("Open project")
        open_btn.triggered.connect(self.open_project)
        toolbar.addAction(open_btn)

        save_btn = QAction("Save", self)
        save_btn.setToolTip("Save project")
        save_btn.triggered.connect(self.save_project)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        new_tab_btn = QAction("New tab", self)
        new_tab_btn.setToolTip(
            "Add a new state transition tab")
        new_tab_btn.triggered.connect(self.add_new_tab)
        toolbar.addAction(new_tab_btn)

        rename_btn = QAction("Rename tab", self)
        rename_btn.setToolTip("Rename current tab")
        rename_btn.triggered.connect(
            self.rename_current_tab)
        toolbar.addAction(rename_btn)

        toolbar.addSeparator()

        traceball_btn = QAction("Show log", self)
        traceball_btn.setCheckable(True)
        traceball_btn.setChecked(False)
        traceball_btn.setToolTip(
            "Show/hide TraceBall log")
        traceball_btn.toggled.connect(
            self.toggle_traceball)
        toolbar.addAction(traceball_btn)

        StaTableLogger.debug("Toolbar created")

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------
    def create_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        # [v2.3] New Project (Ctrl+N)
        new_project_action = QAction("New Project...", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        file_menu.addSeparator()

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

        # Layer settings
        layer_settings_action = QAction(
            "Layer Settings...", self)
        layer_settings_action.triggered.connect(
            self.open_layer_settings)
        edit_menu.addAction(layer_settings_action)

        validation_menu = menubar.addMenu("Validate(&V)")
        validate_action = QAction(
            "Validation / AI diagnosis...", self)
        validate_action.setShortcut("Ctrl+Shift+V")
        validate_action.triggered.connect(
            self.open_validation_dialog)
        validation_menu.addAction(validate_action)

        code_gen_menu = menubar.addMenu("Code generation(&G)")
        generate_action = QAction(
            "Code generation...", self)
        generate_action.setShortcut("Ctrl+G")
        generate_action.triggered.connect(
            self.open_code_generation_dialog)
        code_gen_menu.addAction(generate_action)

        gen_settings_action = QAction(
            "Generation settings...", self)
        gen_settings_action.setShortcut("Ctrl+Shift+G")
        gen_settings_action.triggered.connect(
            self.open_code_generation_settings)
        code_gen_menu.addAction(gen_settings_action)

        code_gen_menu.addSeparator()
        gen_save_action = QAction(
            "Save generated code...", self)
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
    # Layer settings
    # ------------------------------------------------------------------
    def open_layer_settings(self):
        """Open the layer settings dialog"""
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
                "No layers are defined.")
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
    # Dialog launch methods
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
                "There is no state transition tab.")
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
                "There is no state transition tab.")
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
    # Project save / load
    # ------------------------------------------------------------------
    def save_project(self) -> bool:
        """Save all tabs, global definitions, shared libraries, and
        project settings.

        [v2.3] Returns:
            True on success, False on cancel or failure.
        """
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
            return False
        try:
            # Collect project settings
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

            # [v2.3] Clear modified flag on success
            self.setWindowModified(False)
            self._update_window_title()
            return True
        except Exception as e:
            import traceback
            self.logger.error(
                f"Failed to save project: "
                f"{filepath}, error: {e}\n"
                f"{traceback.format_exc()}")
            QMessageBox.critical(
                self, "Error",
                f"Failed to save project:\n{e}")
            return False

    def open_project(self):
        """Load the whole project"""
        # [v2.3] Prompt to save before loading
        if not self._maybe_save():
            return

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

            # [v2.3] Clear modified flag AFTER tabs are restored,
            #        so dataModified emissions from add_state_machine_tab
            #        do not leave the window marked as modified.
            self.setWindowModified(False)
            self._update_window_title()

            self.global_defs = global_defs
            self.global_defs.add_timer_variables()

            # Replace shared library too
            if role_lib is not None:
                self.role_function_library = role_lib
            if cond_lib is not None:
                self.condition_library = cond_lib
            if lit_lib is not None:
                self.literal_library = lit_lib

            # ============================================================
            # Auto-complete 1: register each tab's SM role functions into the shared library
            #   Even if <SharedLibraries> in the XML is empty, present candidates in the palette
            # ============================================================
            from statable_gui.libcntrl.role_function_library import (
                RoleFunction as LibRoleFunction)
            registered_rfs = 0
            for _tab_name, _sm in tabs:
                for _rf in _sm.role_functions.values():
                    _qn = (getattr(_rf, 'qualified_name', None)
                           or getattr(_rf, 'name', ''))
                    if not _qn:
                        continue
                    #Skip if already present in library
                    if self.role_function_library.get(_qn) is not None:
                        continue
                    try:
                        self.role_function_library.add(LibRoleFunction(
                            name=getattr(_rf, 'name', '') or '',
                            namespace=getattr(_rf, 'namespace', '') or '',
                            title=getattr(_rf, 'title', '') or '',
                            description=getattr(_rf, 'description', '') or '',
                        ))
                        registered_rfs += 1
                    except ValueError:
                        pass  # Duplicates ignored
                    except Exception as e:
                        StaTableLogger.warning(
                            f"Failed to register role function {_qn}: {e}")

            if registered_rfs:
                StaTableLogger.info(
                    f"Registered {registered_rfs} role functions "
                    f"from tabs to shared library "
                    f"(total={len(self.role_function_library.list_all())})"
                )

            # ============================================================
            # Auto-complete 2: register each transition's condition into ConditionLibrary
            # ============================================================
            from statable_gui.libcntrl.condition_library import (
                ConditionTemplate)
            existing_cond_exprs = set()
            for _ct in self.condition_library.list_all():
                _c = (getattr(_ct, 'condition', '') or '').strip()
                if _c:
                    existing_cond_exprs.add(_c)
            existing_cond_names = {
                ct.name for ct in self.condition_library.list_all()
            }

            registered_conds = 0
            for _tab_name, _sm in tabs:
                for _trans in _sm.transitions:
                    _cond = (getattr(_trans, 'condition', '') or '').strip()
                    if not _cond:
                        continue
                    if _cond in existing_cond_exprs:
                        continue

                    _base = _cond[:40]
                    _name = _base
                    _idx = 2
                    while _name in existing_cond_names:
                        _name = f"{_base}_{_idx}"
                        _idx += 1

                    try:
                        self.condition_library.add(ConditionTemplate(
                            name=_name,
                            condition=_cond,
                            description=f"Auto-collected ({_tab_name})",
                        ))
                        existing_cond_exprs.add(_cond)
                        existing_cond_names.add(_name)
                        registered_conds += 1
                    except ValueError:
                        pass
                    except Exception as e:
                        StaTableLogger.warning(
                            f"Failed to register condition '{_name}': {e}")

            if registered_conds:
                StaTableLogger.info(
                    f"Registered {registered_conds} conditions "
                    f"from transitions "
                    f"(total={len(self.condition_library.list_all())})"
                )

            # ============================================================
            # Apply project settings
            # ============================================================
            if project_settings:
                config = self.config_manager.get_config()
                for key, value in project_settings.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                        StaTableLogger.debug(
                            f"  config.{key} = {value}")
                self.config_manager.set_config(config)

            # ============================================================
            # Update library references of existing tabs
            # ============================================================
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
                    if hasattr(tab.table, 'populate'):
                        try:
                            tab.table.populate()
                        except Exception:
                            pass

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
    # Tab management
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
            # [v2.3] Mark modified
            self.setWindowModified(True)
            self._update_window_title()

    def add_new_tab(self):
        name, ok = QInputDialog.getText(
            self, "New State Machine",
            "Enter tab name:")
        if ok and name.strip():
            sm = StateMachine()
            self.add_state_machine_tab(name.strip(), sm)
            self.logger.info(
                f"New tab added: {name.strip()}")
            # [v2.3] Mark modified
            self.setWindowModified(True)
            self._update_window_title()

    def add_state_machine_tab(self, name: str,
                              sm: StateMachine):
        StaTableLogger.debug(
            f"add_state_machine_tab: name={name}, "
            f"layer_name='{getattr(sm, 'layer_name', '')}', "
            f"layer_priority={getattr(sm, 'layer_priority', 5)}, "
            f"roles={len(self.role_function_library.list_all())}"
        )

        #If layer name unset, use tab name
        if not getattr(sm, 'layer_name', ''):
            sm.layer_name = name

        tab = StateMachineTab(
            sm,
            global_defs=self.global_defs,
            role_function_library=self.role_function_library,
            condition_library=self.condition_library,
            literal_library=self.literal_library,
            # [v2.4] Provide all tab names as namespace candidates.
            #        Forwarded to SettingsPanel so the inline combo
            #        box and RoleFunctionDialog list every layer.
            layer_names_provider=self._get_all_layer_names)

        # [v2.3] Relay tab modification signal to MainWindow
        tab.dataModified.connect(self._on_tab_data_modified)

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
        # [v2.3] Mark modified
        self.setWindowModified(True)
        self._update_window_title()

    # ------------------------------------------------------------------
    # Log / validation / code generation
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

    # Multi-layer support helper
    def _get_all_layers(self):
        """Return the (name, sm) list of all tabs sorted by priority ascending"""
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

    def _get_all_layer_names(self) -> list:
        """Return all tab names (= all layer names in the project).

        [v2.4]
          Used by StateMachineTab / SettingsPanel to populate the
          namespace combo box with every layer in the project, not
          just the current tab's layer. Called via the
          `layer_names_provider` callable on every editor creation,
          so newly added / renamed tabs are reflected immediately.
        """
        names = []
        try:
            for i in range(self.tab_widget.count()):
                text = self.tab_widget.tabText(i)
                if text and text not in names:
                    names.append(text)
        except Exception as e:
            StaTableLogger.warning(
                f"_get_all_layer_names failed: {e}")
        return names

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

        # Collect all tabs as layers
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
        # Pass all layers
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
    # Direct save of generated code (multi-layer + warning collection)
    # ------------------------------------------------------------------
    def save_generated_code_direct(self):
        StaTableLogger.debug(
            "MainWindow.save_generated_code_direct called")
        config = self.config_manager.get_config()
        output_dir = config.output_directory

        if not output_dir:
            QMessageBox.warning(
                self, "Warning",
                "Output directory is not set.\n"
                # [C-19 fix] Add the missing '.' and '\n' so the
                # message reads "... in settings.\nPlease specify."
                "First set the output directory in settings.\n"
                "Please specify.")
            self.open_code_generation_settings()
            config = self.config_manager.get_config()
            output_dir = config.output_directory
            if not output_dir:
                return

        # Collect all tabs as layers
        layers = self._get_all_layers()
        if not layers:
            QMessageBox.warning(
                self, "Warning", "There are no tabs.")
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
            # Multi-layer generation
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
                self, "Error",
                f"Code generation failed:\n{e}")
            StaTableLogger.error(
                f"Code generation failed: {e}")
            return
        finally:
            root_logger.removeHandler(collector)

        QMessageBox.information(
            self, "Save complete",
            f"{len(saved_files)} files saved.\n"
            f"Layers: {len(layers)}\n\n"
            f"Output: {output_dir}")

        if collector.records:
            seen = set()
            unique = []
            for r in collector.records:
                if r not in seen:
                    seen.add(r)
                    unique.append(r)
            QMessageBox.warning(
                self, "Warnings during generation",
                "The following warnings occurred:\n\n"
                + "\n".join(f"- {m}" for m in unique))

    # ==================================================================
    # New Project feature (v2.3 / F-15)
    # ==================================================================

    def new_project(self) -> None:
        """Start a new empty project.

        Preserves: Preferences, TraceBall log.
        Clears:    tabs, global definitions, shared libraries,
                   ConfigManager, windowModified flag.
        """
        if not self._maybe_save():
            return

        StaTableLogger.debug("MainWindow.new_project: start")

        # 1. Remove all tabs (close_all_tabs uses removeTab directly)
        self.close_all_tabs()

        # 2. Reset project-scoped global definitions
        self.global_defs = GlobalDefinitions()
        self.global_defs.add_timer_variables()

        # 3. Clear shared libraries (decision #5, revised)
        self.role_function_library = RoleFunctionLibrary()
        self.condition_library = ConditionLibrary()
        self.literal_library = LiteralLibrary()

        # 4. Reset code generation config to defaults
        self.config_manager.reset()

        # 5. One empty Application layer
        empty_sm = StateMachine()
        empty_sm.layer_name = "Application"
        empty_sm.layer_priority = 5
        self.add_state_machine_tab("Application", empty_sm)

        # 6. Reset modified flag and window title
        self.setWindowModified(False)
        self._update_window_title()

        # 7. Status bar notification
        self.statusBar().showMessage("New project created", 3000)

        StaTableLogger.debug("MainWindow.new_project: done")

    def _maybe_save(self) -> bool:
        """Prompt to save if there are unsaved changes.

        Returns True to proceed, False to abort.
        Called from new_project / open_project / closeEvent.
        """
        if not self.isWindowModified():
            return True

        ret = QMessageBox.warning(
            self,
            "Unsaved Changes",
            "The current project has unsaved changes.\n"
            "Do you want to save them before continuing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if ret == QMessageBox.Save:
            return self.save_project()
        return ret == QMessageBox.Discard

    def closeEvent(self, event) -> None:
        """Prompt on window close if there are unsaved changes."""
        if self._maybe_save():
            event.accept()
        else:
            event.ignore()

    def _update_window_title(self) -> None:
        """Update window title with modified marker.

        Qt replaces [*] with '*' when setWindowModified(True).
        """
        self.setWindowTitle("Untitled[*] - StaTable")

    def _on_tab_data_modified(self) -> None:
        """Slot connected to each StateMachineTab.dataModified signal."""
        self.setWindowModified(True)
        self._update_window_title()