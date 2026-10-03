# statable_gui/new_project_wizard.py
"""New Project Wizard (v3.2).

4-page wizard:
  1. Project name and output folder
  2. Template selection
  3. Customize names (editable)
  4. Preview and generate
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QFileDialog, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QRadioButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWizard, QWizardPage,
)

from statable.model import (
    State, Event, EventKind, EventDeliveryType, StateType,
)
from statable.state_machine import StateMachine
from statable.global_defs import (
    GlobalDefinitions, SystemVariable, EventFlag,
    InterruptHandlerDef, EventQueueDef,
)
from statable.xml_io import project_to_xml

from .new_project_templates import (
    TEMPLATES, COMMON_EVENTS, INTERRUPTS, GLOBAL_VARIABLES,
    EVENT_FLAGS, EVENT_QUEUES,
)


# ======================================================================
# Page 1: Project info
# ======================================================================
class PageProjectInfo(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Project Information"))
        self.setSubTitle(self.tr("Enter the project name and output folder."))

        layout = QFormLayout(self)

        self.name_edit = QLineEdit("MyProject")
        self.name_edit.textChanged.connect(self.completeChanged)
        layout.addRow(self.tr("Project name:"), self.name_edit)

        folder_layout = QHBoxLayout()
        self.folder_edit = QLineEdit(
            str(Path.home() / "Documents" / "StaTableProjects"))
        self.folder_edit.textChanged.connect(self.completeChanged)
        folder_layout.addWidget(self.folder_edit)
        browse_btn = QPushButton(self.tr("Browse..."))
        browse_btn.clicked.connect(self._on_browse)
        folder_layout.addWidget(browse_btn)
        layout.addRow(self.tr("Output folder:"), folder_layout)

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self.folder_edit.setText(path)

    def isComplete(self):
        return (bool(self.name_edit.text().strip())
                and bool(self.folder_edit.text().strip()))

    def project_name(self):
        return self.name_edit.text().strip()

    def output_folder(self):
        return Path(self.folder_edit.text().strip())


# ======================================================================
# Page 2: Template selection
# ======================================================================
class PageTemplate(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Template Selection"))
        self.setSubTitle(self.tr("Choose a project structure template."))

        layout = QVBoxLayout(self)
        self.group = QButtonGroup(self)

        self._buttons = {}
        for key in ("three_layer", "basic", "blank"):
            name = self._tr_template_name(key)
            desc = self._tr_template_desc(key)
            rb = QRadioButton(f"{name}\n   {desc}")
            rb.setProperty("template_id", key)
            if key == "three_layer":
                rb.setChecked(True)
            self.group.addButton(rb)
            layout.addWidget(rb)
            self._buttons[key] = rb

        layout.addStretch()

    def _tr_template_name(self, key):
        """Return translated template name (literal for lupdate)."""
        return {
            "three_layer": self.tr(
                "3-Layer (Driver / Middleware / Application) [Recommended]"),
            "basic": self.tr("Basic (Single Layer)"),
            "blank": self.tr("Empty Project"),
        }.get(key, key)

    def _tr_template_desc(self, key):
        """Return translated template description (literal for lupdate)."""
        return {
            "three_layer": self.tr(
                "Full 3-layer structure with all placeholders"),
            "basic": self.tr(
                "Application layer with 5 states + 5 events + 5 role functions"),
            "blank": self.tr(
                "One empty Application layer (existing behavior)"),
        }.get(key, "")

    def selected_template_id(self):
        for key, rb in self._buttons.items():
            if rb.isChecked():
                return key
        return "three_layer"


# ======================================================================
# Page 3: Customize names
# ======================================================================
class PageCustomize(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Customize Names"))
        self.setSubTitle(self.tr(
            "Optionally rename placeholder elements. "
            "Leave 'New Name' blank to keep the default."
        ))

        layout = QVBoxLayout(self)

        info = QLabel(self.tr(
            "Edit the 'New Name' column to rename. "
            "Double-click a cell to edit."
        ))
        info.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(info)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Category", "Layer", "Default Name", "New Name"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_reset = QPushButton(self.tr("Reset All"))
        btn_reset.clicked.connect(self._on_reset)
        btn_layout.addWidget(btn_reset)
        layout.addLayout(btn_layout)

        self._rows = []

    def initializePage(self):
        wiz = self.wizard()
        tpl_id = wiz.page_template.selected_template_id()
        tpl = TEMPLATES[tpl_id]

        self.table.setRowCount(0)
        self._rows = []

        if not tpl["layers"]:
            return

        for layer in tpl["layers"]:
            for st in layer["states"]:
                self._add_row("State", layer["name"], st["name"])

        for layer in tpl["layers"]:
            for rf in layer["role_functions"]:
                self._add_row("Role Function", layer["name"], rf["name"])

        for ev in COMMON_EVENTS:
            self._add_row("Event", "(all layers)", ev["name"])

        for it in INTERRUPTS:
            self._add_row("Interrupt", "(shared)", it["name"])

        for gv in GLOBAL_VARIABLES:
            self._add_row("Variable", "(shared)", gv["name"])

        for fl in EVENT_FLAGS:
            self._add_row("Flag", "(shared)", fl["name"])

        for eq in EVENT_QUEUES:
            self._add_row("Queue", "(shared)", eq["name"])

    def _tr_category(self, category):
        return {
            "State": self.tr("State"),
            "Role Function": self.tr("Role Function"),
            "Event": self.tr("Event"),
            "Interrupt": self.tr("Interrupt"),
            "Variable": self.tr("Variable"),
            "Flag": self.tr("Flag"),
            "Queue": self.tr("Queue"),
        }.get(category, category)

    def _add_row(self, category, layer, default):
        row = self.table.rowCount()
        self.table.insertRow(row)

        for col, text in enumerate(
                [self._tr_category(category), layer, default]):
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, col, item)

        new_item = QTableWidgetItem("")
        self.table.setItem(row, 3, new_item)
        self._rows.append((category, layer, default, row))

    def _on_reset(self):
        for _, _, _, row in self._rows:
            item = self.table.item(row, 3)
            if item:
                item.setText("")

    def get_renames(self):
        renames = {}
        for category, layer, default, row in self._rows:
            item = self.table.item(row, 3)
            if item:
                new_name = item.text().strip()
                if new_name and new_name != default:
                    renames[(category, layer, default)] = new_name
        return renames


# ======================================================================
# Page 4: Preview
# ======================================================================
class PagePreview(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Preview"))
        self.setSubTitle(self.tr("Review what will be generated."))

        layout = QVBoxLayout(self)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)

    def initializePage(self):
        wiz = self.wizard()
        name = wiz.page_info.project_name()
        tpl_id = wiz.page_template.selected_template_id()
        tpl = TEMPLATES[tpl_id]
        renames = (wiz.page_customize.get_renames()
                   if tpl["layers"] else {})

        def rn(cat, layer, nm):
            return renames.get((cat, layer, nm), nm)

        lines = [
            f"Project name: {name}",
            f"Output folder: {wiz.page_info.output_folder()}",
            f"Template: {wiz.page_template._tr_template_name(tpl_id)}",
            f"Custom renames: {len(renames)}",
            "",
        ]

        if not tpl["layers"]:
            lines.append(
                "(Empty project: 1 Application layer, no states)")
        else:
            for layer in tpl["layers"]:
                ln = layer["name"]
                lines.append(
                    f"Layer: {ln} (priority {layer['priority']})")
                lines.append(f"  States ({len(layer['states'])}):")
                for st in layer["states"]:
                    new = rn("State", ln, st["name"])
                    mark = " *" if new != st["name"] else ""
                    lines.append(
                        f"    - {new}{mark} ({st['type']})")
                lines.append(
                    f"  Role functions ({len(layer['role_functions'])}):")
                for rf in layer["role_functions"]:
                    new = rn("Role Function", ln, rf["name"])
                    mark = " *" if new != rf["name"] else ""
                    lines.append(f"    - {new}{mark}")
                lines.append("")

            lines.append(
                f"Events ({len(COMMON_EVENTS)} per layer):")
            for ev in COMMON_EVENTS:
                new = rn("Event", "(all layers)", ev["name"])
                mark = " *" if new != ev["name"] else ""
                lines.append(
                    f"  - {new}{mark} [{ev['delivery']}, {ev['kind']}]")
            lines.append("")

            lines.append(f"Interrupts ({len(INTERRUPTS)}):")
            for it in INTERRUPTS:
                new = rn("Interrupt", "(shared)", it["name"])
                mark = " *" if new != it["name"] else ""
                lines.append(f"  - {new}{mark}")
            lines.append("")

            lines.append(
                f"Global variables ({len(GLOBAL_VARIABLES)}):")
            for gv in GLOBAL_VARIABLES:
                new = rn("Variable", "(shared)", gv["name"])
                mark = " *" if new != gv["name"] else ""
                lines.append(f"  - {new}{mark} ({gv['type']})")
            lines.append("")

            lines.append(f"Flags ({len(EVENT_FLAGS)}):")
            for fl in EVENT_FLAGS:
                new = rn("Flag", "(shared)", fl["name"])
                mark = " *" if new != fl["name"] else ""
                lines.append(f"  - {new}{mark}")
            lines.append("")

            lines.append(f"Event queues ({len(EVENT_QUEUES)}):")
            for eq in EVENT_QUEUES:
                new = rn("Queue", "(shared)", eq["name"])
                mark = " *" if new != eq["name"] else ""
                lines.append(
                    f"  - {new}{mark} (size={eq['size']})")

            if renames:
                lines.append("")
                lines.append("(* = custom name)")

        self.preview.setPlainText("\n".join(lines))


# ======================================================================
# Wizard
# ======================================================================
class NewProjectWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("New Project Wizard"))
        self.setWizardStyle(QWizard.ClassicStyle)
        self.resize(820, 620)

        self.page_info = PageProjectInfo()
        self.page_template = PageTemplate()
        self.page_customize = PageCustomize()
        self.page_preview = PagePreview()

        self.addPage(self.page_info)
        self.addPage(self.page_template)
        self.addPage(self.page_customize)
        self.addPage(self.page_preview)

    def generate(self):
        name = self.page_info.project_name()
        out_dir = self.page_info.output_folder()
        tpl_id = self.page_template.selected_template_id()
        tpl = TEMPLATES[tpl_id]

        renames = (self.page_customize.get_renames()
                   if tpl["layers"] else {})

        def rn(cat, layer, orig):
            return renames.get((cat, layer, orig), orig)

        out_dir.mkdir(parents=True, exist_ok=True)
        xml_path = out_dir / f"{name}.xml"

        gd = GlobalDefinitions()
        try:
            gd.add_timer_variables()
        except Exception:
            pass

        if tpl_id != "blank":
            self._populate_global_defs(gd, rn)

        tabs = []
        if not tpl["layers"]:
            sm = StateMachine()
            sm.layer_name = "Application"
            sm.layer_priority = 5
            tabs.append(("Application", sm))
        else:
            for layer in tpl["layers"]:
                sm = self._build_layer(layer, rn)
                tabs.append((layer["name"], sm))

        project_settings = {
            "project_name": name,
            "table_type": "array",
            "generation_style": "table_driven",
            "os_type": "non_rtos",
            "folder_structure": "by_layer",
            "include_dir_name": "include",
            "source_dir_name": "src",
            "common_dir_name": "common",
            "project_dir_name": "project",
            "generate_super_include": True,
            "super_include_file": "statable_all.h",
            "max_consecutive_pending_events": 16,
        }

        project_to_xml(
            tabs=tabs,
            global_defs=gd,
            filepath=str(xml_path),
            project_settings=project_settings,
        )
        return str(xml_path)

    def _populate_global_defs(self, gd, rn):
        # Variables: SystemVariable(name, type, ...)
        for gv in GLOBAL_VARIABLES:
            nm = rn("Variable", "(shared)", gv["name"])
            try:
                v = SystemVariable(
                    name=nm,
                    type=gv.get("type", "uint32_t"),
                    description=gv.get("description", ""),
                )
                gd.variables.append(v)
            except Exception as e:
                import sys as _sys
                print(f"[WARN] SystemVariable({nm}) failed: {e}",
                      file=_sys.stderr)

        # Flags: EventFlag(name, min_value, max_value, ...)
        for fl in EVENT_FLAGS:
            nm = rn("Flag", "(shared)", fl["name"])
            try:
                f = EventFlag(
                    name=nm,
                    min_value=fl.get("min_value", 0),
                    max_value=fl.get("max_value", 1),
                    description=fl.get("description", ""),
                )
                gd.flags.append(f)
            except Exception as e:
                import sys as _sys
                print(f"[WARN] EventFlag({nm}) failed: {e}",
                      file=_sys.stderr)

        # Interrupts: InterruptHandlerDef(name, description, ...)
        for it in INTERRUPTS:
            nm = rn("Interrupt", "(shared)", it["name"])
            try:
                ih = InterruptHandlerDef(
                    name=nm,
                    description=it.get("description", ""),
                )
                gd.interrupts.append(ih)
            except Exception as e:
                import sys as _sys
                print(f"[WARN] InterruptHandlerDef({nm}) failed: {e}",
                      file=_sys.stderr)

        # Event queues: EventQueueDef(name, size, element_type, ...)
        for eq in EVENT_QUEUES:
            nm = rn("Queue", "(shared)", eq["name"])
            try:
                q = EventQueueDef(
                    name=nm,
                    size=eq.get("size", 16),
                    element_type=eq.get("element_type", "uint16_t"),
                    description=eq.get("description", ""),
                )
                gd.event_queues.append(q)
            except Exception as e:
                import sys as _sys
                print(f"[WARN] EventQueueDef({nm}) failed: {e}",
                      file=_sys.stderr)

    def _build_layer(self, layer, rn):
        sm = StateMachine()
        sm.layer_name = layer["name"]
        sm.layer_priority = layer["priority"]
        if hasattr(sm, "layer_description"):
            sm.layer_description = layer.get("description", "")

        ln = layer["name"]

        for i, st_def in enumerate(layer["states"]):
            nm = rn("State", ln, st_def["name"])
            st = State(name=nm)
            st.description = st_def.get("description", "")
            if st_def.get("type") == "initial":
                st.type = StateType.INITIAL
            sm.add_state(st)
            if i == 0:
                sm.set_initial(nm)

        for i, ev in enumerate(COMMON_EVENTS):
            nm = rn("Event", "(all layers)", ev["name"])
            try:
                ev_obj = Event(name=nm, id=i + 1)
                ev_obj.kind = (EventKind.SIGNAL
                               if ev["kind"] == "signal"
                               else EventKind.TIME)
                ev_obj.delivery_type = (
                    EventDeliveryType.QUEUE
                    if ev["delivery"] == "queue"
                    else EventDeliveryType.DIRECT
                )
                ev_obj.description = ev.get("description", "")
                sm.add_event(ev_obj)
            except Exception:
                pass

        for rf_def in layer["role_functions"]:
            nm = rn("Role Function", ln, rf_def["name"])
            try:
                from statable.model import RoleFunction
                rf = RoleFunction(name=nm)
                if hasattr(rf, "namespace"):
                    rf.namespace = ln
                if hasattr(rf, "title"):
                    rf.title = rf_def.get("description", "")
                if hasattr(rf, "description"):
                    rf.description = rf_def.get("description", "")
                sm.add_role_function(rf)
            except Exception:
                pass

        try:
            from statable.model import ActionStep
            for st_def in layer["states"]:
                new_st = rn("State", ln, st_def["name"])
                do_name = f"{new_st}_Do"
                step = ActionStep(role_function=do_name)
                sm.states[new_st].do_actions.append(step)
        except Exception:
            pass

        return sm
