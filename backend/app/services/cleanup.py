"""
app/services/cleanup.py — Transient Media Auto-Deletion Routine (Security Section 4.3).

Ensures temporary audio voice notes and image downloads do not persist beyond
MEDIA_RETENTION_HOURS (24-48h).
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from app.config import Settings

logger = logging.getLogger(__name__)

TEMP_MEDIA_DIR = Path("/tmp/mitra_media")


def init_media_dir() -> Path:
    TEMP_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    return TEMP_MEDIA_DIR


def purge_expired_media(settings: Settings) -> int:
    """
    Scan transient media storage and delete files older than media_retention_hours.
    Returns number of deleted files.
    """
    if not TEMP_MEDIA_DIR.exists():
        return 0

    retention_seconds = settings.media_retention_hours * 3600
    now = time.time()
    deleted_count = 0

    for entry in TEMP_MEDIA_DIR.iterdir():
        if entry.is_file():
            try:
                mtime = entry.stat().st_mtime
                if (now - mtime) > retention_seconds:
                    entry.unlink(missing_ok=True)
                    deleted_count += 1
            except Exception as e:
                logger.warning("failed_to_delete_transient_media", extra={"file": entry.name, "error": str(e)})

    if deleted_count > 0:
        logger.info("transient_media_purged", extra={"deleted_files": deleted_count})
    return deleted_count
