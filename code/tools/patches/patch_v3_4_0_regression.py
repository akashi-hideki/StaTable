"""v3.4.0 regression fix.

1. test_v2_7_p4.py: test_action_list_widget_operations() was written
   for the old _ActionListWidget (QTableWidgetItem + QLineEdit).
   The new widget uses QComboBox for Target and a container with
   QLineEdit for Condition. Replace the whole function.
2. README.md: suite count 43 -> 44, PASS count 1605 -> 1635
   (test_v2_7_p5.py added 30 PASS assertions).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CODE = ROOT / "code"


NEW_TEST_FUNC = '''def test_action_list_widget_operations():
    print("\\n[5] _ActionListWidget operations")
    app = get_app()
    if app is None:
        RESULT.skip("_ActionListWidget", "PySide6 not available")
        return

    from statable_gui.state_actions_dialog import _ActionListWidget
    from statable.model import ActionStep
    from PySide6.QtWidgets import QLineEdit, QComboBox

    w = _ActionListWidget()

    # set_actions
    w.set_actions([
        ActionStep(role_function="Driver.A"),
        ActionStep(role_function="Driver.B", condition="x > 0"),
    ])
    check("set_actions row count", w.table.rowCount() == 2)
    check("set_actions _rows len", len(w._rows) == 2)
    check("row 0 target (rows)", w._rows[0]["target"] == "Driver.A")
    check("row 1 condition (rows)", w._rows[1]["condition"] == "x > 0")

    # Target column is now QComboBox (cell widget)
    combo0 = w.table.cellWidget(0, w.COL_TARGET)
    check("row 0 target is QComboBox",
          combo0 is not None and isinstance(combo0, QComboBox))

    # Condition column is now a QWidget container with QLineEdit
    cond1 = w.table.cellWidget(1, w.COL_CONDITION)
    check("row 1 condition container exists", cond1 is not None)
    if cond1 is not None:
        edit1 = cond1.findChild(QLineEdit)
        check("row 1 condition has QLineEdit", edit1 is not None)
        if edit1 is not None:
            check("row 1 condition text", edit1.text() == "x > 0")

    # get_actions round-trip
    got = w.get_actions()
    check("get_actions len", len(got) == 2)
    check("get_actions[0].role_function", got[0].role_function == "Driver.A")
    check("get_actions[1].condition", got[1].condition == "x > 0")

    # add
    w._on_add()
    check("_on_add row count", w.table.rowCount() == 3)
    check("_on_add _rows len", len(w._rows) == 3)

    # delete
    w.table.selectRow(2)
    w._on_delete()
    check("_on_delete row count", w.table.rowCount() == 2)
    check("_on_delete _rows len", len(w._rows) == 2)

    # up
    w.table.selectRow(1)
    w._on_up()
    check("_on_up reorder", w._rows[0]["target"] == "Driver.B")
    check("_on_up reorder (2)", w._rows[1]["target"] == "Driver.A")

    # down
    w.table.selectRow(0)
    w._on_down()
    check("_on_down reorder", w._rows[0]["target"] == "Driver.A")

    # empty target is dropped
    w.set_actions([
        ActionStep(role_function="Driver.X"),
        ActionStep(),
    ])
    got = w.get_actions()
    check("empty target dropped", len(got) == 1)
    check("empty target dropped value", got[0].role_function == "Driver.X")

    # fire_event action
    w.set_actions([
        ActionStep(action_type="fire_event", event_name="Driver.TICK"),
    ])
    got = w.get_actions()
    check("fire_event len", len(got) == 1)
    check("fire_event action_type", got[0].action_type == "fire_event")
    check("fire_event event_name", got[0].event_name == "Driver.TICK")


'''


def patch_test() -> bool:
    path = CODE / "tests" / "test_v2_7_p4.py"
    if not path.exists():
        print(f"[ERR]  {path} not found")
        return False
    text = path.read_text(encoding="utf-8")
    if "isinstance(combo0, QComboBox)" in text:
        print("[SKIP] test_v2_7_p4.py already patched")
        return True

    pattern = re.compile(
        r"^def test_action_list_widget_operations\(\):.*?"
        r"(?=^def |^class |^# =|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    new_text, n = pattern.subn(NEW_TEST_FUNC, text, count=1)
    if n == 0:
        print("[ERR]  test_action_list_widget_operations not found")
        return False

    path.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"[OK]   patched {path.name}")
    return True


def patch_readme() -> bool:
    path = ROOT / "README.md"
    if not path.exists():
        print(f"[ERR]  {path} not found")
        return False
    text = path.read_text(encoding="utf-8")
    if "Tests-1635" in text and "44 suites" in text:
        print("[SKIP] README.md already patched")
        return True

    orig = text
    text = text.replace("across 43 suites", "across 44 suites")
    text = text.replace("**43 test suites", "**44 test suites")
    text = text.replace("(43 suites,", "(44 suites,")
    text = text.replace("All 43 suites should pass", "All 44 suites should pass")
    text = text.replace("Tests-1605%20PASS", "Tests-1635%20PASS")
    text = text.replace("**1605 PASS / 0 FAIL / 2 SKIP**",
                        "**1635 PASS / 0 FAIL / 2 SKIP**")
    text = text.replace("(1605 PASS / 2 SKIP)",
                        "(1635 PASS / 2 SKIP)")

    if text == orig:
        print("[WARN] README.md: no changes applied")
        return False

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[OK]   patched {path.name}")
    return True


def main() -> int:
    print("=" * 74)
    print("  v3.4.0 regression fix")
    print("=" * 74)
    ok1 = patch_test()
    ok2 = patch_readme()
    print()
    print(f"  test_v2_7_p4.py : {'OK' if ok1 else 'FAIL'}")
    print(f"  README.md       : {'OK' if ok2 else 'FAIL'}")
    print("=" * 74)
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    sys.exit(main())