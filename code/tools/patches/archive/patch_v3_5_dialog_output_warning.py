"""patch_v3_5_dialog_output_warning.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DG = ROOT / "statable_gui" / "code_generation_dialog.py"


def _must(text, old, new, label):
    if old not in text:
        raise SystemExit(f"[FAIL] {label}: not found")
    if text.count(old) != 1:
        raise SystemExit(f"[FAIL] {label}: not unique")
    return text.replace(old, new, 1)


text = DG.read_text(encoding="utf-8")

# 1) import (follow existing try/except pattern)
text = _must(
    text,
    "try:\n"
    "    from .code_generation_settings_dialog import (\n"
    "        CodeGenerationSettingsDialog,\n"
    "    )\n"
    "except ImportError:\n"
    "    from code_generation_settings_dialog import (\n"
    "        CodeGenerationSettingsDialog,\n"
    "    )\n",
    "try:\n"
    "    from .code_generation_settings_dialog import (\n"
    "        CodeGenerationSettingsDialog,\n"
    "    )\n"
    "except ImportError:\n"
    "    from code_generation_settings_dialog import (\n"
    "        CodeGenerationSettingsDialog,\n"
    "    )\n"
    "\n"
    "try:\n"
    "    from .output_warning import show_orphan_warning\n"
    "except ImportError:\n"
    "    from output_warning import show_orphan_warning\n",
    "import",
)

# 2) orphan warning after save info
text = _must(
    text,
    "            QMessageBox.information(\n"
    "                self, self.tr(\"Save complete\"),\n"
    "                f\"{len(saved_files)} files \"\n"
    "                f\"saved.\\n\\n\"\n"
    "                f\"Output: {output_dir}\")\n"
    "        except Exception as e:\n",
    "            QMessageBox.information(\n"
    "                self, self.tr(\"Save complete\"),\n"
    "                f\"{len(saved_files)} files \"\n"
    "                f\"saved.\\n\\n\"\n"
    "                f\"Output: {output_dir}\")\n"
    "            # [v3.5.0] Warn about stale files left in output_dir.\n"
    "            if getattr(generator, \"last_orphans\", None):\n"
    "                show_orphan_warning(\n"
    "                    self, generator.last_orphans, output_dir)\n"
    "        except Exception as e:\n",
    "save warning",
)

DG.write_text(text, encoding="utf-8")
print(f"[OK] patched {DG}")
