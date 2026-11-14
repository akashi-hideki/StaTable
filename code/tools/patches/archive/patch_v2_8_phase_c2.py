# code/tools/patch_v2_8_phase_c2.py
"""
Phase C-2 patch for v2.8.0.

Target:
    code/codegen/validate/validation_dialog.py

Integrates ResponseValidator:
  C2-1. Import ResponseValidator.
  C2-2. Instantiate it in __init__ (self.response_validator).
        Add self.validation_outcome = None to store the latest result.
  C2-3. Extend the change tree headers with Priority / Confidence / Status.
  C2-4. In _parse_response: validate parsed changes, show only
        valid_requests in the tree, append Priority/Confidence/Status,
        surface invalid_requests + warnings in the message box.

Safety:
    - Backup once per file.
    - Literal anchors; idempotent.
    - Refuses to apply if an anchor is missing or found >1 times.

Usage:
    cd C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code
    python tools\\patch_v2_8_phase_c2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
TARGET = CODE_DIR / "codegen" / "validate" / "validation_dialog.py"


# ======================================================================
# C2-1: import
# ======================================================================
A1_OLD = "from .clipboard_manager import ClipboardManager\n"
A1_NEW = (
    "from .clipboard_manager import ClipboardManager\n"
    "from .response_validator import ResponseValidator\n"
)


# ======================================================================
# C2-2: __init__ additions
# ======================================================================
A2_OLD = (
    "        self.response_parser = AIResponseParser()\n"
    "        self.clipboard = ClipboardManager()\n"
    "        self.validation_result = None\n"
    "        self.parsed_changes = []\n"
)
A2_NEW = (
    "        self.response_parser = AIResponseParser()\n"
    "        self.response_validator = ResponseValidator()\n"
    "        self.clipboard = ClipboardManager()\n"
    "        self.validation_result = None\n"
    "        self.parsed_changes = []\n"
    "        self.validation_outcome = None\n"
)


# ======================================================================
# C2-3: change tree headers
# ======================================================================
A3_OLD = (
    '        self.change_tree.setHeaderLabels('
    '["Selection", "Action", "Parameter", "Reason"])\n'
    "        self.change_tree.setColumnWidth(0, 50)\n"
    "        self.change_tree.setColumnWidth(1, 150)\n"
    "        self.change_tree.setColumnWidth(2, 400)\n"
    "        self.change_tree.setColumnWidth(3, 250)\n"
)
A3_NEW = (
    '        self.change_tree.setHeaderLabels([\n'
    '            "Selection", "Action", "Parameter", "Reason",\n'
    '            "Priority", "Confidence", "Status",\n'
    '        ])\n'
    "        self.change_tree.setColumnWidth(0, 50)\n"
    "        self.change_tree.setColumnWidth(1, 150)\n"
    "        self.change_tree.setColumnWidth(2, 400)\n"
    "        self.change_tree.setColumnWidth(3, 250)\n"
    "        self.change_tree.setColumnWidth(4, 80)\n"
    "        self.change_tree.setColumnWidth(5, 80)\n"
    "        self.change_tree.setColumnWidth(6, 240)\n"
)


# ======================================================================
# C2-4: _parse_response body
# ======================================================================
A4_OLD = (
    "        self.parsed_changes = self.response_parser.parse(text)\n"
    "        \n"
    "        # Show change list\n"
    "        self.change_tree.clear()\n"
    "        for change in self.parsed_changes:\n"
    "            item = QTreeWidgetItem()\n"
    "            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)\n"
    "            item.setCheckState(0, Qt.Checked)\n"
    "            item.setText(1, change.action.value)\n"
    "            item.setText(2, json.dumps(change.params, ensure_ascii=False))\n"
    "            item.setText(3, change.reason)\n"
    "            self.change_tree.addTopLevelItem(item)\n"
    "        \n"
    "        # Switch the tab to the change list\n"
    "        self.tab_widget.setCurrentIndex(3)\n"
    "        \n"
    "        QMessageBox.information(self, \"Parse complete\",\n"
    "            f\"{len(self.parsed_changes)} change(s) extracted.\")\n"
)

A4_NEW = (
    "        parsed = self.response_parser.parse(text)\n"
    "        self.validation_outcome = self.response_validator.validate(\n"
    "            parsed, self.sm, self.gd)\n"
    "        outcome = self.validation_outcome\n"
    "        self.parsed_changes = list(outcome.valid_requests)\n"
    "        \n"
    "        # Show change list (valid requests only)\n"
    "        self.change_tree.clear()\n"
    "        for change in self.parsed_changes:\n"
    "            item = QTreeWidgetItem()\n"
    "            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)\n"
    "            item.setCheckState(0, Qt.Checked)\n"
    "            item.setText(1, change.action.value)\n"
    "            item.setText(2, json.dumps(change.params, ensure_ascii=False))\n"
    "            item.setText(3, change.reason)\n"
    "            item.setText(4, change.priority)\n"
    "            item.setText(5, f\"{change.confidence:.2f}\")\n"
    "            item.setText(6, \"OK\")\n"
    "            self.change_tree.addTopLevelItem(item)\n"
    "        \n"
    "        # Append invalid requests as unchecked, disabled rows\n"
    "        for req, reason in outcome.invalid_requests:\n"
    "            item = QTreeWidgetItem()\n"
    "            item.setFlags(Qt.ItemIsEnabled)\n"
    "            item.setCheckState(0, Qt.Unchecked)\n"
    "            item.setText(1, req.action.value)\n"
    "            item.setText(2, json.dumps(req.params, ensure_ascii=False))\n"
    "            item.setText(3, req.reason)\n"
    "            item.setText(4, req.priority)\n"
    "            item.setText(5, f\"{req.confidence:.2f}\")\n"
    "            item.setText(6, f\"EXCLUDED: {reason}\")\n"
    "            self.change_tree.addTopLevelItem(item)\n"
    "        \n"
    "        # Switch the tab to the change list\n"
    "        self.tab_widget.setCurrentIndex(3)\n"
    "        \n"
    "        n_ok = len(outcome.valid_requests)\n"
    "        n_ng = len(outcome.invalid_requests)\n"
    "        msg = f\"Parsed {len(parsed)} change(s).\\n\"\n"
    "        msg += f\"Valid: {n_ok}   Excluded: {n_ng}\\n\"\n"
    "        if outcome.warnings:\n"
    "            msg += \"\\nWarnings:\\n\" + \"\\n\".join(\n"
    "                f\"  * {w}\" for w in outcome.warnings)\n"
    "        QMessageBox.information(self, \"Parse complete\", msg)\n"
)


# ======================================================================
# Edit helper
# ======================================================================
def _apply(text: str, anchor: str, replacement: str, label: str) -> str:
    count = text.count(anchor)
    if count == 0:
        print(f"  [SKIP] {label}: anchor not found")
        return text
    if count > 1:
        print(f"  [FAIL] {label}: anchor found {count} times")
        raise SystemExit(1)
    print(f"  [APPLY] {label}")
    return text.replace(anchor, replacement, 1)


def main() -> int:
    print("=" * 70)
    print("  v2.8.0 Phase C-2 patch")
    print("=" * 70)

    if not TARGET.exists():
        print(f"[FAIL] target not found: {TARGET}")
        return 1

    print(f"\nTarget: {TARGET}")
    original = TARGET.read_text(encoding="utf-8")

    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")
        print(f"  Backup: {backup}")
    else:
        print(f"  Backup: already exists, keeping {backup}")

    patched = original
    patched = _apply(patched, A1_OLD, A1_NEW, "C2-1 import ResponseValidator")
    patched = _apply(patched, A2_OLD, A2_NEW, "C2-2 __init__ additions")
    patched = _apply(patched, A3_OLD, A3_NEW, "C2-3 change tree headers")
    patched = _apply(patched, A4_OLD, A4_NEW, "C2-4 _parse_response body")

    if patched == original:
        print()
        print("[INFO] No changes (already up to date).")
        return 0

    TARGET.write_text(patched, encoding="utf-8")
    print()
    print("[DONE] validation_dialog.py patched.")
    print()
    print("Verify:")
    print("  python -c \"import ast; "
          "ast.parse(open(r'codegen/validate/validation_dialog.py', "
          "encoding='utf-8').read()); print('syntax OK')\"")
    print("  python tests\\test_v2_8_p1_ai_prompt.py")
    print("  python tests\\test_v2_8_p2_response_parser.py")
    print("  python tests\\test_v2_8_p3_response_validator.py")
    print("  python tests\\test_v2_2_p12_6.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())