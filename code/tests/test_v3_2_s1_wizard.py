# tests/test_v3_2_s1_wizard.py
"""Test New Project Wizard (v3.2).

Covers:
  - Template data structure (3 templates, 5 elements each)
  - Wizard XML generation (offscreen Qt)
  - Round-trip: generate -> load -> verify
  - Rename functionality
  - File menu cleanup (no Empty action)
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    from statable_gui.new_project_templates import (
        TEMPLATES, COMMON_EVENTS, INTERRUPTS, GLOBAL_VARIABLES,
        EVENT_FLAGS, EVENT_QUEUES, LAYERS_3LAYER,
    )

    passed = 0
    failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"[PASS] {name}")
        else:
            failed += 1
            print(f"[FAIL] {name}")

    # ==== T1: Template data ====
    print("=" * 70)
    print("  T1: Template data structure")
    print("=" * 70)

    check("TEMPLATES has 3 entries", len(TEMPLATES) == 3)
    check("'blank' present", "blank" in TEMPLATES)
    check("'basic' present", "basic" in TEMPLATES)
    check("'three_layer' present", "three_layer" in TEMPLATES)

    check("blank has no layers", len(TEMPLATES["blank"]["layers"]) == 0)
    check("basic has 1 layer", len(TEMPLATES["basic"]["layers"]) == 1)
    check("three_layer has 3 layers",
          len(TEMPLATES["three_layer"]["layers"]) == 3)

    check("COMMON_EVENTS has 5", len(COMMON_EVENTS) == 5)
    check("INTERRUPTS has 5", len(INTERRUPTS) == 5)
    check("GLOBAL_VARIABLES has 5", len(GLOBAL_VARIABLES) == 5)
    check("EVENT_FLAGS has 5", len(EVENT_FLAGS) == 5)
    check("EVENT_QUEUES has 5", len(EVENT_QUEUES) == 5)

    check("LAYERS_3LAYER has 3 layers", len(LAYERS_3LAYER) == 3)
    for layer in LAYERS_3LAYER:
        nm = layer["name"]
        check(f"{nm}: 5 states", len(layer["states"]) == 5)
        check(f"{nm}: 5 role functions",
              len(layer["role_functions"]) == 5)

    deliveries = {ev["delivery"] for ev in COMMON_EVENTS}
    check("Events include 'queue'", "queue" in deliveries)
    check("Events include 'direct'", "direct" in deliveries)

    kinds = {ev["kind"] for ev in COMMON_EVENTS}
    check("Events include 'signal'", "signal" in kinds)
    check("Events include 'time'", "time" in kinds)

    # ==== T2: Wizard generation ====
    print()
    print("=" * 70)
    print("  T2: Wizard XML generation (offscreen Qt)")
    print("=" * 70)

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from statable_gui.new_project_wizard import NewProjectWizard
        from statable.xml_io import project_from_xml

        # T2a: three_layer
        with tempfile.TemporaryDirectory() as tmpdir:
            wiz = NewProjectWizard()
            wiz.page_info.name_edit.setText("TestThree")
            wiz.page_info.folder_edit.setText(tmpdir)
            wiz.page_template._buttons["three_layer"].setChecked(True)

            xml_path = wiz.generate()
            check("generate() returned path", xml_path is not None)
            check("XML file exists", Path(xml_path).exists())
            check("XML stem matches", Path(xml_path).stem == "TestThree")

            tabs, gd, rf, cl, ll, settings = project_from_xml(xml_path)
            check("Roundtrip: 3 tabs", len(tabs) == 3)
            tab_names = [t[0] for t in tabs]
            check("Tab Driver", "Driver" in tab_names)
            check("Tab Middleware", "Middleware" in tab_names)
            check("Tab Application", "Application" in tab_names)

            for nm, sm in tabs:
                check(f"{nm}: 5 states", len(sm.states) == 5)
                check(f"{nm}: 5 events", len(sm.events) == 5)
                check(f"{nm}: 5 role functions",
                      len(sm.role_functions) == 5)

            check("5 interrupts", len(gd.interrupts) == 5)
            check(">=5 variables", len(gd.variables) >= 5)
            check(">=5 flags", len(gd.flags) >= 5)
            check("5 event queues", len(gd.event_queues) == 5)
            check("project_name preserved",
                  settings.get("project_name") == "TestThree")

        # T2b: basic
        with tempfile.TemporaryDirectory() as tmpdir:
            wiz = NewProjectWizard()
            wiz.page_info.name_edit.setText("TestBasic")
            wiz.page_info.folder_edit.setText(tmpdir)
            wiz.page_template._buttons["basic"].setChecked(True)

            xml_path = wiz.generate()
            tabs, _, _, _, _, _ = project_from_xml(xml_path)
            check("Basic: 1 tab", len(tabs) == 1)
            check("Basic tab = Application", tabs[0][0] == "Application")
            check("Basic: 5 states", len(tabs[0][1].states) == 5)

        # T2c: blank
        with tempfile.TemporaryDirectory() as tmpdir:
            wiz = NewProjectWizard()
            wiz.page_info.name_edit.setText("TestBlank")
            wiz.page_info.folder_edit.setText(tmpdir)
            wiz.page_template._buttons["blank"].setChecked(True)

            xml_path = wiz.generate()
            tabs, _, _, _, _, _ = project_from_xml(xml_path)
            check("Blank: 1 tab", len(tabs) == 1)
            check("Blank tab = Application", tabs[0][0] == "Application")
            check("Blank: 0 states", len(tabs[0][1].states) == 0)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        check(f"Wizard generation failed: {e}", False)

    # ==== T3: Rename ====
    print()
    print("=" * 70)
    print("  T3: Rename functionality")
    print("=" * 70)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            wiz = NewProjectWizard()
            wiz.page_info.name_edit.setText("TestRename")
            wiz.page_info.folder_edit.setText(tmpdir)
            wiz.page_template._buttons["three_layer"].setChecked(True)

            wiz.page_customize.initializePage()

            renamed = 0
            for cat, layer, default, row in wiz.page_customize._rows:
                if cat == "State" and default == "Driver_Init":
                    item = wiz.page_customize.table.item(row, 3)
                    item.setText("Motor_Init")
                    renamed += 1

            check("Found Driver_Init row", renamed == 1)

            xml_path = wiz.generate()
            tabs, _, _, _, _, _ = project_from_xml(xml_path)
            driver_sm = next(sm for name, sm in tabs if name == "Driver")
            state_names = list(driver_sm.states.keys())
            check("Motor_Init present", "Motor_Init" in state_names)
            check("Driver_Init absent", "Driver_Init" not in state_names)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        check(f"Rename test failed: {e}", False)

    # ==== T4: File menu ====
    print()
    print("=" * 70)
    print("  T4: File menu cleanup")
    print("=" * 70)

    mw_path = (Path(__file__).parent.parent /
               "statable_gui" / "main_window.py")
    mw_src = mw_path.read_text(encoding="utf-8")

    check("'New Project (Empty)' removed",
          "New Project (Empty)" not in mw_src)
    check("'New Project (Wizard)' removed",
          "New Project (Wizard)" not in mw_src)
    check("'New Project...' present",
          'self.tr("New Project...")' in mw_src)
    check("Ctrl+N shortcut present",
          'new_wizard_action.setShortcut("Ctrl+N")' in mw_src)
    check("new_project_wizard method present",
          "def new_project_wizard" in mw_src)

    # ==== Summary ====
    print()
    print("=" * 70)
    print(f"  TOTAL: {passed + failed}   "
          f"PASSED: {passed}   FAILED: {failed}")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    os._exit(main())