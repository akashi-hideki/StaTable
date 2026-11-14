# code/tools/patches/patch_v3_1_restart_fix.py
r"""
v3.1 fix: prevent restart loop, ensure old process exits.

Problem: QCoreApplication.quit() did not terminate the old process,
causing multiple instances when "Restart now" was clicked.

Fix:
  - Add module-level guard to prevent concurrent restarts
  - Use os._exit(0) after detached start (guaranteed termination)
  - Confirm new process launched before exiting old one

Usage:
    cd code
    python tools\patches\patch_v3_1_restart_fix.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "statable_gui" / "main_window.py"

OLD = (
    '        def _relaunch_application():\n'
    '            """Start a new instance detached, then quit."""\n'
    '            import os\n'
    '            import sys as _sys\n'
    '            from PySide6.QtCore import QProcess, QCoreApplication\n'
    '\n'
    '            # Prefer python -m statable (works in editable & installed)\n'
    '            exe = _sys.executable\n'
    '            args = ["-m", "statable"]\n'
    '            cwd = os.getcwd()\n'
    '            ok = QProcess.startDetached(exe, args, cwd)\n'
    '            if not ok:\n'
    '                QMessageBox.warning(\n'
    '                    self,\n'
    '                    "Restart failed",\n'
    '                    "Could not restart automatically.\\n"\n'
    '                    "Please start StaTable manually.",\n'
    '                )\n'
    '                return\n'
    '            QCoreApplication.quit()\n'
)

NEW = (
    '        def _relaunch_application():\n'
    '            """Start a new instance detached, then quit (guaranteed)."""\n'
    '            import os\n'
    '            import sys as _sys\n'
    '            from PySide6.QtCore import QProcess\n'
    '\n'
    '            # Guard: prevent concurrent restarts\n'
    '            if getattr(self, "_restart_in_progress", False):\n'
    '                return\n'
    '            self._restart_in_progress = True\n'
    '\n'
    '            exe = _sys.executable\n'
    '            args = ["-m", "statable"]\n'
    '            cwd = os.getcwd()\n'
    '\n'
    '            # Disable UI to avoid double-clicks\n'
    '            self.setEnabled(False)\n'
    '\n'
    '            ok = QProcess.startDetached(exe, args, cwd)\n'
    '            if not ok:\n'
    '                self._restart_in_progress = False\n'
    '                self.setEnabled(True)\n'
    '                QMessageBox.warning(\n'
    '                    self,\n'
    '                    "Restart failed",\n'
    '                    "Could not restart automatically.\\n"\n'
    '                    "Please start StaTable manually.",\n'
    '                )\n'
    '                return\n'
    '\n'
    '            # Give the new process a moment to start, then exit\n'
    '            import time\n'
    '            time.sleep(0.3)\n'
    '            os._exit(0)  # immediate exit; no cleanup needed\n'
)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_restart_fix  [{mode}]")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] not found: {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8")
    if "os._exit(0)" in text:
        print("[SKIP] already has os._exit fix")
        return 0

    n = text.count(OLD)
    if n != 1:
        print(f"[FAIL] anchor found {n} times (expected 1)")
        print("--- anchor preview (first 200 chars):")
        print(OLD[:200])
        return 1

    new_text = text.replace(OLD, NEW, 1)
    print("[APPLY] replace _relaunch_application with safe version")
    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply")
        return 0

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_restartfix")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    TARGET.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {TARGET.relative_to(CODE.parent)} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())