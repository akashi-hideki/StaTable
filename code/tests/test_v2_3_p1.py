"""Tests for v2.3 New Project feature.

[v2.3 fix] Use a single shared MainWindow for the whole test session.
Creating multiple MainWindow instances triggers a Qt/logger singleton
interaction. The production logger guards against this, but reusing
one window is cleaner and matches real application behavior.
"""

import os
import sys
import traceback
from pathlib import Path
from unittest.mock import patch

# Ensure offscreen before importing PySide6
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication, QMessageBox


# ----------------------------------------------------------------------
# Shared MainWindow
# ----------------------------------------------------------------------
_WINDOW = None


def _get_window():
    global _WINDOW
    if _WINDOW is None:
        from statable_gui.main_window import MainWindow
        _app = QApplication.instance() or QApplication([])
        _WINDOW = MainWindow()
    return _WINDOW


def _reset_window():
    win = _get_window()
    win.setWindowModified(False)
    win.new_project()
    return win


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_new_project_creates_one_application_tab():
    win = _reset_window()
    assert win.tab_widget.count() == 1
    assert win.tab_widget.tabText(0) == "Application"


def test_new_project_resets_state_machine():
    win = _reset_window()
    sm = win._get_current_state_machine()
    assert sm is not None
    assert len(sm.states) == 0
    assert len(sm.events) == 0
    assert len(sm.transitions) == 0
    assert len(sm.role_functions) == 0
    assert sm.layer_name == "Application"
    assert sm.layer_priority == 5


def test_new_project_resets_global_defs():
    win = _reset_window()
    assert len(win.global_defs.flags) == 0
    assert len(win.global_defs.interrupts) == 0
    assert len(win.global_defs.placeholders) == 0
    assert len(win.global_defs.event_queues) == 0
    for v in win.global_defs.variables:
        group = getattr(v, 'group', '')
        assert group == 'Timer', (
            f"Unexpected non-timer variable: "
            f"name={getattr(v, 'name', '?')}, group={group!r}")


def test_new_project_clears_shared_libraries():
    win = _get_window()
    from statable_gui.libcntrl.role_function_library import RoleFunction
    from statable_gui.libcntrl.condition_library import ConditionTemplate
    from statable_gui.libcntrl.literal_library import LiteralDefinition
    win.role_function_library.add(
        RoleFunction(name="test", namespace="Tmp"))
    win.condition_library.add(
        ConditionTemplate(name="tmp_cond", condition="x > 0"))
    win.literal_library.add(
        LiteralDefinition(name="TMP_LIT", value="1", literal_type="int"))
    assert len(win.role_function_library.list_all()) >= 1
    win.setWindowModified(False)
    win.new_project()
    assert len(win.role_function_library.list_all()) == 0
    assert len(win.condition_library.list_all()) == 0
    assert len(win.literal_library.list_all()) == 0


def test_new_project_resets_config_manager():
    win = _get_window()
    win.config_manager.update(output_directory="/tmp/xxx")
    win.setWindowModified(False)
    win.new_project()
    assert win.config_manager.get_config().output_directory == ""


def test_new_project_keeps_preferences():
    win = _get_window()
    prefs_before = win.prefs
    win.setWindowModified(False)
    win.new_project()
    assert win.prefs is prefs_before


def test_new_project_clears_window_modified():
    win = _get_window()
    win.setWindowModified(False)
    win.new_project()
    assert not win.isWindowModified()


def test_new_project_cancelled_by_user():
    win = _get_window()
    win.setWindowModified(True)
    with patch.object(QMessageBox, "warning",
                      return_value=QMessageBox.Cancel):
        win.new_project()
    assert win.tab_widget.count() >= 1
    win.setWindowModified(False)


def test_new_project_discard_proceeds():
    win = _get_window()
    win.setWindowModified(True)
    with patch.object(QMessageBox, "warning",
                      return_value=QMessageBox.Discard):
        win.new_project()
    assert win.tab_widget.count() == 1
    assert win.tab_widget.tabText(0) == "Application"


def test_new_project_save_calls_save_project():
    win = _get_window()
    win.setWindowModified(True)
    with patch.object(QMessageBox, "warning",
                      return_value=QMessageBox.Save), \
         patch.object(win, "save_project", return_value=True) as mock_save:
        win.new_project()
    mock_save.assert_called_once()
    assert win.tab_widget.count() == 1


def test_maybe_save_no_changes_returns_true():
    win = _get_window()
    win.setWindowModified(False)
    assert win._maybe_save() is True


def test_save_project_returns_bool():
    win = _get_window()
    with patch("statable_gui.main_window.QFileDialog.getSaveFileName",
               return_value=("", "")):
        result = win.save_project()
    assert result is False


def test_tab_data_modified_signal_exists():
    win = _reset_window()
    tab = win.tab_widget.widget(0)
    assert hasattr(tab, "dataModified")


def test_tab_data_modified_sets_window_modified():
    win = _reset_window()
    win.setWindowModified(False)
    tab = win.tab_widget.widget(0)
    tab.dataModified.emit()
    assert win.isWindowModified()


# ----------------------------------------------------------------------
# Runner
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("  StaTable v2.3 P1 (New Project) test suite")
    print("=" * 70)

    tests = [v for k, v in list(globals().items())
             if k.startswith("test_") and callable(v)]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  [PASS] {t.__name__}")
        except Exception:
            failed += 1
            print(f"  [FAIL] {t.__name__}")
            traceback.print_exc()

    print()
    print("=" * 70)
    print(f"  TOTAL: {passed + failed}  PASSED: {passed}  FAILED: {failed}")
    print("=" * 70)
    sys.exit(1 if failed else 0)