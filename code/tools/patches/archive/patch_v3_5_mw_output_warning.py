"""patch_v3_5_mw_output_warning.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MW = ROOT / "statable_gui" / "main_window.py"


def _must(text, old, new, label):
    if old not in text:
        raise SystemExit(f"[FAIL] {label}: not found")
    if text.count(old) != 1:
        raise SystemExit(f"[FAIL] {label}: not unique")
    return text.replace(old, new, 1)


text = MW.read_text(encoding="utf-8")

# 1) import
text = _must(
    text,
    "from .logger import StaTableLogger\n",
    "from .logger import StaTableLogger\n"
    "from .output_warning import show_orphan_warning\n",
    "import",
)

# 2) orphan warning in save_generated_code_direct
text = _must(
    text,
    "            f\"Layers: {len(layers)}\\n\\n\"\n"
    "            f\"Output: {output_dir}\")\n"
    "\n"
    "        if collector.records:\n",
    "            f\"Layers: {len(layers)}\\n\\n\"\n"
    "            f\"Output: {output_dir}\")\n"
    "\n"
    "        # [v3.5.0] Warn about stale files left in output_dir.\n"
    "        if getattr(generator, \"last_orphans\", None):\n"
    "            show_orphan_warning(\n"
    "                self, generator.last_orphans, output_dir)\n"
    "\n"
    "        if collector.records:\n",
    "save warning",
)

# 3) toolbar Clean generate button
text = _must(
    text,
    "        gen_save_btn.triggered.connect(\n"
    "            self.save_generated_code_direct)\n"
    "        toolbar.addAction(gen_save_btn)\n",
    "        gen_save_btn.triggered.connect(\n"
    "            self.save_generated_code_direct)\n"
    "        toolbar.addAction(gen_save_btn)\n"
    "\n"
    "        gen_clean_btn = QAction(\n"
    "            self.tr(\"Clean generate\"), self)\n"
    "        gen_clean_btn.setToolTip(self.tr(\n"
    "            \"Delete output directory and regenerate \"\n"
    "            \"from scratch\"))\n"
    "        gen_clean_btn.triggered.connect(\n"
    "            self.clean_generate_code)\n"
    "        toolbar.addAction(gen_clean_btn)\n",
    "toolbar",
)

# 4) menu Clean generate action
text = _must(
    text,
    "        gen_save_action.triggered.connect(\n"
    "            self.save_generated_code_direct)\n"
    "        code_gen_menu.addAction(gen_save_action)\n",
    "        gen_save_action.triggered.connect(\n"
    "            self.save_generated_code_direct)\n"
    "        code_gen_menu.addAction(gen_save_action)\n"
    "\n"
    "        gen_clean_action = QAction(\n"
    "            self.tr(\"Clean generate...\"), self)\n"
    "        gen_clean_action.triggered.connect(\n"
    "            self.clean_generate_code)\n"
    "        code_gen_menu.addAction(gen_clean_action)\n",
    "menu",
)

# 5) clean_generate_code method before New Project header
text = _must(
    text,
    "    # ==================================================================\n"
    "    # New Project feature (v2.3 / F-15)\n",
    "    # ------------------------------------------------------------------\n"
    "    # [v3.5.0] Clean generate (delete output_dir and regenerate)\n"
    "    # ------------------------------------------------------------------\n"
    "\n"
    "    def clean_generate_code(self) -> None:\n"
    "        \"\"\"[v3.5.0] Delete output_dir, then regenerate.\"\"\"\n"
    "        config = self.config_manager.get_config()\n"
    "        output_dir = config.output_directory\n"
    "        if not output_dir or not os.path.isdir(output_dir):\n"
    "            self.save_generated_code_direct()\n"
    "            return\n"
    "        reply = QMessageBox.warning(\n"
    "            self, self.tr(\"Clean generate\"),\n"
    "            self.tr(\n"
    "                \"This will DELETE all files under:\\n\"\n"
    "                \"{0}\\n\\n\"\n"
    "                \"then regenerate from scratch.\\n\\n\"\n"
    "                \"Any manual edits in generated files \"\n"
    "                \"(including user code preserved by merge) \"\n"
    "                \"will be lost.\\n\\n\"\n"
    "                \"Continue?\").format(output_dir),\n"
    "            QMessageBox.Yes | QMessageBox.No,\n"
    "            QMessageBox.No)\n"
    "        if reply != QMessageBox.Yes:\n"
    "            return\n"
    "        try:\n"
    "            shutil.rmtree(output_dir)\n"
    "        except OSError as e:\n"
    "            QMessageBox.critical(\n"
    "                self, self.tr(\"Error\"),\n"
    "                self.tr(\n"
    "                    \"Failed to clean output directory:\\n\"\n"
    "                    \"{0}\").format(e))\n"
    "            return\n"
    "        self.save_generated_code_direct()\n"
    "\n"
    "    # ==================================================================\n"
    "    # New Project feature (v2.3 / F-15)\n",
    "clean method",
)

# 6) import shutil
text = _must(
    text,
    "import sys\nimport os\nimport logging\n",
    "import sys\nimport os\nimport shutil\nimport logging\n",
    "shutil",
)

MW.write_text(text, encoding="utf-8")
print(f"[OK] patched {MW}")
