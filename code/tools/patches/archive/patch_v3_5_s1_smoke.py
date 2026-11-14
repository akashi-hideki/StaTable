"""v3.5.0 S-1: frozen exe smoke test expansion (levels 0-3).

Adds / modifies:
  - statable/smoke.py            (new)
  - statable/__main__.py         (modify: --smoke-level=N)
  - tools/smoke_frozen.py        (modify: --smoke-level passthrough)
  - StaTable.spec                (modify: hiddenimports)
  - tests/test_v3_5_s1_smoke.py  (new)
  - .github/workflows/check.yml  (modify: register + smoke step)

Run from repo root (StaTable/):
    python code/tools/patches/patch_v3_5_s1_smoke.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CODE = REPO / "code"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote:   {path.relative_to(REPO)}")


def patch(path: Path, old: str, new: str) -> None:
    txt = path.read_text(encoding="utf-8")
    if old not in txt:
        print(f"[FAIL] pattern not found in {path.relative_to(REPO)}")
        print("----- expected -----")
        print(old[:500])
        sys.exit(1)
    txt = txt.replace(old, new, 1)
    path.write_text(txt, encoding="utf-8")
    print(f"  patched: {path.relative_to(REPO)}")


SMOKE_PY = '''"""statable.smoke - Headless smoke tests for StaTable (levels 0-3).

Levels:
  0 (default) : MainWindow creation + open_project regression (v3.2.2)
  1           : level 0 + basic widget presence
  2           : level 1 + _ActionListWidget operation (v3.4.x)
  3           : level 2 + save/open roundtrip in a temp dir

Usage:
    python -m statable --smoke-test --smoke-level=2

Exit codes:
  0 = all checks pass
  1 = one or more checks fail
  4 = QApplication creation failed
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback

LEVEL_MIN = 0
LEVEL_MAX = 3


class SmokeRunner:
    def __init__(self, level: int) -> None:
        self.level = level
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.checks = []
        self._app = None
        self._window = None

    def check(self, name: str, cond: bool, detail: str = "") -> bool:
        self.total += 1
        ok = bool(cond)
        if ok:
            self.passed += 1
            print(f"  [PASS] {name}", file=sys.stderr)
        else:
            self.failed += 1
            print(f"  [FAIL] {name}"
                  + (f" -- {detail}" if detail else ""),
                  file=sys.stderr)
        self.checks.append({"name": name, "ok": ok, "detail": detail})
        return ok

    def summary_dict(self) -> dict:
        return {
            "level": self.level,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "checks": self.checks,
        }

    def _prepare_env(self) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

    def _patch_dialogs(self) -> None:
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
        except ImportError:
            return
        QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ("", ""))
        QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: ("", ""))
        QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: "")
        QMessageBox.information = staticmethod(lambda *a, **k: None)
        QMessageBox.warning = staticmethod(lambda *a, **k: None)
        QMessageBox.critical = staticmethod(lambda *a, **k: None)
        QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)

    def _get_app(self):
        from PySide6.QtWidgets import QApplication
        self._app = QApplication.instance() or QApplication(sys.argv)
        return self._app

    def _level0(self) -> None:
        from statable_gui.main_window import MainWindow
        self._window = MainWindow()
        self.check("MainWindow constructed", self._window is not None)
        try:
            self._window.open_project(False)
            self._window.open_project(True)
            self.check("open_project(False/True) regression", True)
        except Exception as e:
            self.check("open_project(False/True) regression",
                       False, repr(e))

    def _level1(self) -> None:
        w = self._window
        self.check("menuBar() exists", w.menuBar() is not None)
        self.check("centralWidget() exists", w.centralWidget() is not None)
        title = w.windowTitle()
        self.check("windowTitle() non-empty", bool(title),
                   f"got {title!r}")
        try:
            from PySide6.QtWidgets import QTabWidget
            tabs = w.findChild(QTabWidget)
            self.check("QTabWidget present", tabs is not None)
        except Exception as e:
            self.check("QTabWidget lookup", False, repr(e))

    def _level2(self) -> None:
        try:
            from PySide6.QtWidgets import QComboBox
            from statable_gui.state_actions_dialog import _ActionListWidget
        except Exception as e:
            self.check("import _ActionListWidget", False, repr(e))
            return
        self.check("import _ActionListWidget", True)

        try:
            from statable.model import (
                ActionStep, Event, EventKind, RoleFunction, State)
            from statable.state_machine import StateMachine
            from statable_gui.libcntrl.role_function_library import (
                RoleFunctionLibrary)
            from statable_gui.libcntrl.literal_library import LiteralLibrary
            from statable_gui.libcntrl.condition_library import (
                ConditionLibrary)
            from statable_gui.global_defs import GlobalDefinitions
        except Exception as e:
            self.check("import state_actions deps", False, repr(e))
            return
        self.check("import state_actions deps", True)

        sm = StateMachine()
        sm.layer_name = "Application"
        sm.add_state(State("Idle"))
        sm.add_state(State("Active"))
        sm.events["STAGE_START"] = Event(
            name="STAGE_START", kind=EventKind.SIGNAL)
        sm.role_functions["StartStage"] = RoleFunction(
            name="StartStage", namespace="Application")

        w = _ActionListWidget(
            state_machine=sm,
            role_function_library=RoleFunctionLibrary(),
            literal_library=LiteralLibrary(),
            condition_library=ConditionLibrary(),
            layer_names_provider=lambda: ["Application"],
            global_defs=GlobalDefinitions(),
        )
        self.check("_ActionListWidget constructed", w is not None)
        self.check("table has 3 columns", w.table.columnCount() == 3)

        w._on_add()
        self.check("add row", w.table.rowCount() == 1)

        target_combo = w.table.cellWidget(0, w.COL_TARGET)
        self.check("target is QComboBox",
                   isinstance(target_combo, QComboBox))
        if isinstance(target_combo, QComboBox):
            items = [target_combo.itemText(i)
                     for i in range(target_combo.count())]
            self.check("role candidates include StartStage",
                       "Application.StartStage" in items)

        w2 = _ActionListWidget(
            state_machine=sm,
            role_function_library=RoleFunctionLibrary(),
            literal_library=LiteralLibrary(),
            condition_library=ConditionLibrary(),
            layer_names_provider=lambda: ["Application"],
            global_defs=GlobalDefinitions(),
        )
        w2.set_actions([ActionStep(
            action_type="role",
            role_function="Application.StartStage",
            condition="ctx->data.ok")])
        out = w2.get_actions()
        self.check("set/get roundtrip len 1", len(out) == 1)
        if out:
            self.check("roundtrip role_function",
                       out[0].role_function == "Application.StartStage")

    def _level3(self) -> None:
        w = self._window
        if w is None:
            self.check("level 3 requires window", False)
            return
        with tempfile.TemporaryDirectory() as tmpd:
            target = os.path.join(tmpd, "smoke_project.statable")
            try:
                from PySide6.QtWidgets import QFileDialog
                QFileDialog.getSaveFileName = staticmethod(
                    lambda *a, **k: (target, ""))
                QFileDialog.getOpenFileName = staticmethod(
                    lambda *a, **k: (target, ""))
            except Exception as e:
                self.check("patch QFileDialog for L3", False, repr(e))
                return
            self.check("patch QFileDialog for L3", True)

            try:
                ok = w.save_project()
                self.check("save_project returns True", bool(ok),
                           f"got {ok!r}")
                self.check("file was created", os.path.exists(target))
            except Exception as e:
                self.check("save_project no exception", False, repr(e))
                return

            try:
                w.open_project(target)
                self.check("open_project on saved file", True)
            except Exception as e:
                self.check("open_project on saved file", False, repr(e))

    def run(self) -> int:
        self._prepare_env()
        try:
            self._get_app()
        except Exception as e:
            print(f"QApplication creation failed: {e!r}", file=sys.stderr)
            return 4

        self._patch_dialogs()

        try:
            self._level0()
            if self.level >= 1:
                self._level1()
            if self.level >= 2:
                self._level2()
            if self.level >= 3:
                self._level3()
        except Exception as e:
            traceback.print_exc()
            self.check(
                "smoke execution completed without exception",
                False, repr(e))
        finally:
            try:
                if self._window is not None:
                    self._window.close()
                if self._app is not None:
                    self._app.processEvents()
            except Exception:
                pass

        print(json.dumps(self.summary_dict(), ensure_ascii=False))
        return 0 if self.failed == 0 else 1


def parse_level(argv) -> int:
    """Extract --smoke-level=N (or --smoke-level N) from argv."""
    for i, a in enumerate(argv):
        if a.startswith("--smoke-level="):
            try:
                return int(a.split("=", 1)[1])
            except ValueError:
                return 0
        if a == "--smoke-level" and i + 1 < len(argv):
            try:
                return int(argv[i + 1])
            except ValueError:
                return 0
    return 0


def run(level: int) -> int:
    if level < LEVEL_MIN:
        level = LEVEL_MIN
    if level > LEVEL_MAX:
        level = LEVEL_MAX
    return SmokeRunner(level).run()
'''


TEST_SMOKE_PY = '''"""test_v3_5_s1_smoke.py - unit tests for statable.smoke."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("STATABLE_DISABLE_MERMAID", "1")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from statable.smoke import LEVEL_MAX, LEVEL_MIN, parse_level, run

TOTAL = 0
PASSED = 0
FAILED = 0


def check(name, cond, detail=""):
    global TOTAL, PASSED, FAILED
    TOTAL += 1
    if cond:
        PASSED += 1
        print(f"[PASS] {name}")
    else:
        FAILED += 1
        print(f"[FAIL] {name}" + (f" -- {detail}" if detail else ""))


def main() -> int:
    print("=" * 70)
    print("  test_v3_5_s1_smoke")
    print("=" * 70)

    check("LEVEL_MIN == 0", LEVEL_MIN == 0)
    check("LEVEL_MAX == 3", LEVEL_MAX == 3)

    check("parse_level empty -> 0", parse_level([]) == 0)
    check("parse_level =N form",
          parse_level(["--smoke-level=2"]) == 2)
    check("parse_level space form",
          parse_level(["--smoke-level", "3"]) == 3)
    check("parse_level invalid -> 0",
          parse_level(["--smoke-level=abc"]) == 0)
    check("parse_level ignores others",
          parse_level(["--smoke-test", "--smoke-level=1"]) == 1)

    rc = run(0)
    check("run(0) returns 0", rc == 0, f"rc={rc}")

    print("-" * 70)
    print(f"TOTAL: {TOTAL}  PASSED: {PASSED}  FAILED: {FAILED}")
    print("=" * 70)
    os._exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    sys.exit(main())
'''


def main() -> int:
    print("=" * 70)
    print("  patch_v3_5_s1_smoke")
    print("=" * 70)

    write(CODE / "statable" / "smoke.py", SMOKE_PY)
    write(CODE / "tests" / "test_v3_5_s1_smoke.py", TEST_SMOKE_PY)

    main_py = CODE / "statable" / "__main__.py"
    old_block = '''def run_smoke_test() -> int:
    """Headless smoke test for frozen EXE packaging verification."""
    import os
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["STATABLE_DISABLE_MERMAID"] = "1"

    try:
        from PySide6.QtWidgets import QApplication, QFileDialog
    except ImportError:
        return 1

    # Patch dialogs: no user to interact in headless mode
    QFileDialog.getOpenFileName = staticmethod(lambda *a, **k: ("", ""))
    QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: ("", ""))
    QFileDialog.getExistingDirectory = staticmethod(lambda *a, **k: "")

    try:
        app = QApplication.instance() or QApplication(sys.argv)
    except Exception:
        return 4

    try:
        from statable_gui.main_window import MainWindow
        window = MainWindow()
    except Exception as e:
        sys.stderr.write(f"MainWindow failed: {e!r}\\n")
        return 2

    # v3.2.2 regression scenario
    try:
        window.open_project(False)
        window.open_project(True)
    except Exception as e:
        sys.stderr.write(f"open_project failed: {e!r}\\n")
        return 3

    try:
        window.close()
        app.processEvents()
    except Exception:
        pass

    return 0

def main() -> int:
    if "--smoke-test" in sys.argv:
        return run_smoke_test()'''
    new_block = '''def main() -> int:
    if "--smoke-test" in sys.argv:
        from statable.smoke import parse_level, run as run_smoke
        return run_smoke(parse_level(sys.argv))'''
    patch(main_py, old_block, new_block)

    sf = CODE / "tools" / "smoke_frozen.py"
    patch(
        sf,
        "def run_smoke(exe: Path, timeout: int) -> int:\n"
        '    print(f"[2/3] Launching frozen EXE: {exe}")\n'
        '    print(f"      timeout: {timeout}s")\n'
        "    t0 = time.time()\n"
        "    try:\n"
        "        proc = subprocess.Popen(\n"
        '            [str(exe), "--smoke-test"],',
        "def run_smoke(exe: Path, timeout: int,\n"
        "              smoke_level: int | None = None) -> int:\n"
        '    print(f"[2/3] Launching frozen EXE: {exe}")\n'
        '    print(f"      timeout: {timeout}s")\n'
        "    if smoke_level is not None:\n"
        '        print(f"      level:   {smoke_level}")\n'
        "    t0 = time.time()\n"
        '    argv = [str(exe), "--smoke-test"]\n'
        "    if smoke_level is not None:\n"
        '        argv.append(f"--smoke-level={smoke_level}")\n'
        "    try:\n"
        "        proc = subprocess.Popen(\n"
        "            argv,",
    )
    patch(
        sf,
        '    ap.add_argument("--exe", type=Path, default=None,\n'
        '                    help="override exe path")\n'
        "    args = ap.parse_args()",
        '    ap.add_argument("--exe", type=Path, default=None,\n'
        '                    help="override exe path")\n'
        '    ap.add_argument("--smoke-level", type=int, default=None,\n'
        "                    choices=[0, 1, 2, 3],\n"
        '                    help="smoke test level (0-3)")\n'
        "    args = ap.parse_args()",
    )
    patch(
        sf,
        "    result = run_smoke(exe, args.timeout)",
        "    result = run_smoke(exe, args.timeout, args.smoke_level)",
    )

    spec = CODE / "StaTable.spec"
    patch(
        spec,
        "    'statable.cli',\n",
        "    'statable.cli', 'statable.smoke',\n",
    )

    yml = REPO / ".github" / "workflows" / "check.yml"
    patch(
        yml,
        "          python tests/test_v3_2_s2_signals.py\n\n"
        "      - name: Run CI registration meta test",
        "          python tests/test_v3_2_s2_signals.py\n"
        "          python tests/test_v3_5_s1_smoke.py\n\n"
        "      - name: Run smoke tests (levels 0-3)\n"
        "        run: |\n"
        "          python -m statable --smoke-test --smoke-level=0\n"
        "          python -m statable --smoke-test --smoke-level=1\n"
        "          python -m statable --smoke-test --smoke-level=2\n"
        "          python -m statable --smoke-test --smoke-level=3\n\n"
        "      - name: Run CI registration meta test",
    )

    print()
    print("[OK] patch applied. Next steps:")
    print("     1. cd code")
    print("     2. python tests/test_v3_5_s1_smoke.py")
    print("     3. python -m statable --smoke-test --smoke-level=2")
    print("     4. python tests/test_ci_registration.py")
    print("     5. git add / commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())