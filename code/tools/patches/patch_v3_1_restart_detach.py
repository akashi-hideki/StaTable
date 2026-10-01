# code/tools/patches/patch_v3_1_restart_detach.py
r"""
v3.1 fix: fully detach restarted process from parent console.

Problem: QProcess.startDetached inherits stdout/stderr on Windows,
so the new process's logs flood the original shell.

Fix: use subprocess.Popen with DEVNULL and DETACHED_PROCESS.

Usage:
    cd code
    python tools\patches\patch_v3_1_restart_detach.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent.parent
TARGET = CODE / "statable_gui" / "main_window.py"

OLD = (
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

NEW = (
    '            exe = _sys.executable\n'
    '            args = [exe, "-m", "statable"]\n'
    '            cwd = os.getcwd()\n'
    '\n'
    '            # Disable UI to avoid double-clicks\n'
    '            self.setEnabled(False)\n'
    '\n'
    '            # Fully detach: redirect I/O to null, new process group\n'
    '            ok = False\n'
    '            try:\n'
    '                import subprocess\n'
    '                kwargs = {\n'
    '                    "cwd": cwd,\n'
    '                    "stdin": subprocess.DEVNULL,\n'
    '                    "stdout": subprocess.DEVNULL,\n'
    '                    "stderr": subprocess.DEVNULL,\n'
    '                    "close_fds": True,\n'
    '                }\n'
    '                if os.name == "nt":\n'
    '                    kwargs["creationflags"] = (\n'
    '                        0x00000008  # DETACHED_PROCESS\n'
    '                        | 0x00000200  # CREATE_NEW_PROCESS_GROUP\n'
    '                    )\n'
    '                else:\n'
    '                    kwargs["start_new_session"] = True\n'
    '                subprocess.Popen(args, **kwargs)\n'
    '                ok = True\n'
    '            except Exception:\n'
    '                ok = False\n'
    '\n'
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
    '            # Exit immediately (no cleanup needed)\n'
    '            os._exit(0)\n'
)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 70)
    print(f"  patch_v3_1_restart_detach  [{mode}]")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] not found: {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8")
    if "DETACHED_PROCESS" in text:
        print("[SKIP] already has detached-process fix")
        return 0

    n = text.count(OLD)
    if n != 1:
        print(f"[FAIL] anchor found {n} times (expected 1)")
        return 1

    new_text = text.replace(OLD, NEW, 1)
    print("[APPLY] replace startDetached with subprocess.Popen(DETACHED)")
    if not args.apply:
        print()
        print("[DRY-RUN] no file written; pass --apply")
        return 0

    bak = TARGET.with_suffix(TARGET.suffix + ".bak_detach")
    if not bak.exists():
        bak.write_text(text, encoding="utf-8")
        print(f"  Backup: {bak.name}")

    TARGET.write_text(new_text, encoding="utf-8")
    print(f"[DONE] {TARGET.relative_to(CODE.parent)} updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())