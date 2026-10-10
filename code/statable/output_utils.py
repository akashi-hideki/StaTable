# statable/output_utils.py
"""Public output-directory utilities.

[v3.5.0] find_orphan_files: detect stale files in an output
directory that were not written by the current code generation.

Used by codegen (to record ``last_orphans``) and by GUI layers
(to warn the user about files that may cause build errors).
"""
from __future__ import annotations

import os

__all__ = ["find_orphan_files"]


def find_orphan_files(
    output_dir: str,
    saved_files: list[str],
) -> list[str]:
    """Return files in output_dir that are NOT in saved_files.

    Args:
        output_dir: Directory to scan (recursively).
        saved_files: Absolute paths written by the current
            generation.  Relative paths are also accepted;
            they are resolved with os.path.abspath().

    Returns:
        Sorted list of absolute paths of orphan (stale) files.
        Empty list if output_dir does not exist or is inaccessible.
    """
    try:
        saved = {
            os.path.normcase(os.path.abspath(p))
            for p in saved_files
        }
        orphans: list[str] = []
        for root, _dirs, files in os.walk(output_dir):
            for name in files:
                full = os.path.abspath(os.path.join(root, name))
                if os.path.normcase(full) not in saved:
                    orphans.append(full)
        orphans.sort()
        return orphans
    except OSError:
        return []
