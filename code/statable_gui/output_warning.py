# statable_gui/output_warning.py
"""[v3.5.0] Shared GUI warning for stale (orphan) files."""
from __future__ import annotations

import logging
import os

from PySide6.QtWidgets import QMessageBox

__all__ = ["show_orphan_warning"]

logger = logging.getLogger(__name__)


def show_orphan_warning(
    parent,
    orphans: list,
    output_dir: str,
    on_clean=None,
) -> None:
    """Show a warning about stale files in output_dir.

    Args:
        parent: Parent widget (for tr() and dialog parenting).
        orphans: Absolute paths of stale files.
        output_dir: Base directory (for relative display).
        on_clean: If provided, adds a "Clean && Regenerate"
            button.  Called when the user clicks it.

    Does nothing if orphans is empty.
    """
    if not orphans:
        return
    logger.debug(
        "show_orphan_warning: %d orphan(s) in %s",
        len(orphans), output_dir)
    for p in orphans:
        logger.debug("  orphan: %s", p)

    preview = "\n".join(
        f"- {os.path.relpath(p, output_dir)}"
        for p in orphans[:20]
    )
    if len(orphans) > 20:
        preview += f"\n... and {len(orphans) - 20} more"

    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(parent.tr("Stale files detected"))
    msg.setText(parent.tr(
        "The output directory contains {0} file(s) not "
        "written by this generation:\n\n{1}").format(
            len(orphans), preview))
    msg.setInformativeText(parent.tr(
        "These files may cause build errors (e.g., "
        "references to undefined variables)."))

    if on_clean is not None:
        clean_btn = msg.addButton(
            parent.tr("Clean && Regenerate"),
            QMessageBox.AcceptRole)
        msg.addButton(
            parent.tr("Ignore"),
            QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() is clean_btn:
            on_clean()
    else:
        msg.addButton(QMessageBox.Ok)
        msg.exec()
