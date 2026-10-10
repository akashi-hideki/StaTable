# statable_gui/fs_cleanup.py
"""[v3.5.0] Robust directory removal for Windows/OneDrive."""
from __future__ import annotations

import logging
import os
import shutil
import stat
import time

__all__ = ["robust_rmtree"]

logger = logging.getLogger(__name__)


def robust_rmtree(
    path: str,
    max_retries: int = 3,
    retry_delay: float = 0.3,
) -> list:
    """Remove a directory tree, clearing read-only and retrying.

    Returns list of (filepath, exc_type, exc_message) for files
    that could not be deleted.  Empty list on success.
    """
    errors = []

    def _on_error(func, p, exc_info):
        last_exc = exc_info[1]
        for attempt in range(max_retries):
            try:
                os.chmod(p, stat.S_IWRITE)
                func(p)
                logger.info(
                    "robust_rmtree: retry OK on %s (attempt %d)",
                    p, attempt + 1)
                return
            except OSError as e:
                last_exc = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                errors.append((p, type(e).__name__, str(e)))
                logger.warning(
                    "robust_rmtree: failed on %s: %s: %s",
                    p, type(e).__name__, e)

    try:
        shutil.rmtree(path, onerror=_on_error)
    except OSError as e:
        logger.error(
            "robust_rmtree: rmtree raised: %s: %s",
            type(e).__name__, e)

    return errors
