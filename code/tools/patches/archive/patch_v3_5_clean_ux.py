"""patch_v3_5_clean_ux.py

v3.5.0 refinement:
- clean_generate_code: robust_rmtree + skip_confirm
- show_orphan_warning: pass on_clean callback
- dialog._clean_and_resave: clean then re-save
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _must(text, old, new, label):
    if old not in text:
        raise SystemExit(f"[FAIL] {label}: anchor not found")
    if text.count(old) != 1:
        raise SystemExit(f"[FAIL] {label}: not unique")
    return text.replace(old, new, 1)


# ============ main_window.py ============
MW = ROOT / "statable_gui" / "main_window.py"
t = MW.read_text(encoding="utf-8")

t = _must(
    t,
    "from .output_warning import show_orphan_warning\n",
    "from .output_warning import show_orphan_warning\n"
    "from .fs_cleanup import robust_rmtree\n",
    "mw import fs_cleanup",
)

t = _must(
    t,
    "        gen_clean_btn.triggered.connect(\n"
    "            self.clean_generate_code)\n",
    "        gen_clean_btn.triggered.connect(\n"
    "            lambda: self.clean_generate_code())\n",
    "mw toolbar lambda",
)

t = _must(
    t,
    "        gen_clean_action.triggered.connect(\n"
    "            self.clean_generate_code)\n",
    "        gen_clean_action.triggered.connect(\n"
    "            lambda: self.clean_generate_code())\n",
    "mw menu lambda",
)

t = _must(
    t,
    "        # [v3.5.0] Warn about stale files left in output_dir.\n"
    "        if getattr(generator, \"last_orphans\", None):\n"
    "            show_orphan_warning(\n"
    "                self, generator.last_orphans, output_dir)\n",
    "        # [v3.5.0] Warn about stale files left in output_dir.\n"
    "        _orph = getattr(generator, \"last_orphans\", None)\n"
    "        if _orph:\n"
    "            show_orphan_warning(\n"
    "                self, _orph, output_dir,\n"
    "                on_clean=lambda: self.clean_generate_code(\n"
    "                    skip_confirm=True))\n",
    "mw show_orphan_warning",
)

old_clean = '''    def clean_generate_code(self) -> None:
        """[v3.5.0] Delete output_dir, then regenerate."""
        config = self.config_manager.get_config()
        output_dir = config.output_directory
        if not output_dir or not os.path.isdir(output_dir):
            self.save_generated_code_direct()
            return
        reply = QMessageBox.warning(
            self, self.tr("Clean generate"),
            self.tr(
                "This will DELETE all files under:\\n"
                "{0}\\n\\n"
                "then regenerate from scratch.\\n\\n"
                "Any manual edits in generated files "
                "(including user code preserved by merge) "
                "will be lost.\\n\\n"
                "Continue?").format(output_dir),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            shutil.rmtree(output_dir)
        except OSError as e:
            QMessageBox.critical(
                self, self.tr("Error"),
                self.tr(
                    "Failed to clean output directory:\\n"
                    "{0}").format(e))
            return
        self.save_generated_code_direct()
'''

new_clean = '''    def clean_generate_code(self, skip_confirm: bool = False) -> None:
        """[v3.5.0] Delete output_dir, then regenerate.

        Args:
            skip_confirm: Skip the confirmation dialog (used
                when called from the stale-files warning
                dialog, where intent is already clear).
        """
        config = self.config_manager.get_config()
        output_dir = config.output_directory
        if not output_dir or not os.path.isdir(output_dir):
            self.save_generated_code_direct()
            return
        if not skip_confirm:
            reply = QMessageBox.warning(
                self, self.tr("Clean generate"),
                self.tr(
                    "This will DELETE all files under:\\n"
                    "{0}\\n\\n"
                    "then regenerate from scratch.\\n\\n"
                    "Any manual edits in generated files "
                    "(including user code preserved by merge) "
                    "will be lost.\\n\\n"
                    "Continue?").format(output_dir),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        StaTableLogger.info(
            f"clean_generate_code: removing {output_dir}")
        errors = robust_rmtree(output_dir)
        if errors:
            detail = "\\n".join(
                f"- {p}\\n    {typ}: {msg}"
                for p, typ, msg in errors[:10])
            if len(errors) > 10:
                detail += f"\\n... and {len(errors) - 10} more"
            QMessageBox.critical(
                self, self.tr("Clean failed"),
                self.tr(
                    "Failed to delete some files under:\\n"
                    "{0}\\n\\n"
                    "Errors:\\n{1}").format(
                        output_dir, detail))
            return
        StaTableLogger.info(
            f"clean_generate_code: removed {output_dir}")
        self.save_generated_code_direct()
'''

t = _must(t, old_clean, new_clean, "mw clean body")
MW.write_text(t, encoding="utf-8")
print(f"[OK] patched {MW}")


# ============ code_generation_dialog.py ============
DG = ROOT / "statable_gui" / "code_generation_dialog.py"
t = DG.read_text(encoding="utf-8")

t = _must(
    t,
    "try:\n"
    "    from .output_warning import show_orphan_warning\n"
    "except ImportError:\n"
    "    from output_warning import show_orphan_warning\n",
    "try:\n"
    "    from .output_warning import show_orphan_warning\n"
    "except ImportError:\n"
    "    from output_warning import show_orphan_warning\n"
    "\n"
    "try:\n"
    "    from .fs_cleanup import robust_rmtree\n"
    "except ImportError:\n"
    "    from fs_cleanup import robust_rmtree\n",
    "dg import fs_cleanup",
)

t = _must(
    t,
    "            # [v3.5.0] Warn about stale files left in output_dir.\n"
    "            if getattr(generator, \"last_orphans\", None):\n"
    "                show_orphan_warning(\n"
    "                    self, generator.last_orphans, output_dir)\n",
    "            # [v3.5.0] Warn about stale files left in output_dir.\n"
    "            _orph = getattr(generator, \"last_orphans\", None)\n"
    "            if _orph:\n"
    "                show_orphan_warning(\n"
    "                    self, _orph, output_dir,\n"
    "                    on_clean=self._clean_and_resave)\n",
    "dg show_orphan_warning",
)

t = _must(
    t,
    "    def _on_close(self):\n",
    "    def _clean_and_resave(self):\n"
    "        \"\"\"[v3.5.0] Delete output_dir, then re-save.\"\"\"\n"
    "        output_dir = self.output_dir_edit.text().strip()\n"
    "        if not output_dir:\n"
    "            return\n"
    "        logger.info(\n"
    "            f\"_clean_and_resave: removing {output_dir}\")\n"
    "        errors = robust_rmtree(output_dir)\n"
    "        if errors:\n"
    "            detail = \"\\n\".join(\n"
    "                f\"- {p}\\n    {typ}: {msg}\"\n"
    "                for p, typ, msg in errors[:10])\n"
    "            if len(errors) > 10:\n"
    "                detail += f\"\\n... and {len(errors) - 10} more\"\n"
    "            QMessageBox.critical(\n"
    "                self, self.tr(\"Clean failed\"),\n"
    "                self.tr(\n"
    "                    \"Failed to delete some files under:\\n\"\n"
    "                    \"{0}\\n\\n\"\n"
    "                    \"Errors:\\n{1}\").format(\n"
    "                        output_dir, detail))\n"
    "            return\n"
    "        logger.info(\n"
    "            f\"_clean_and_resave: removed {output_dir}\")\n"
    "        self._save_code()\n"
    "\n"
    "    def _on_close(self):\n",
    "dg clean method",
)

DG.write_text(t, encoding="utf-8")
print(f"[OK] patched {DG}")
print("[DONE]")
