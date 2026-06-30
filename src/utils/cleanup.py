# src/utils/cleanup.py

import os
import logging
from typing import Optional


def cleanup_temp_file(temp_file_path: Optional[str]) -> None:
    """
    Safely removes a temporary local file from disk if it exists.
    - gs:// paths (Firebase Storage) are intentionally kept — not deleted.
    - Only local disk temp files are removed.
    Logs success or any failure without raising.
    """
    if not temp_file_path:
        return

    # Firebase Storage files stay permanently — do not delete
    if temp_file_path.startswith("gs://"):
        logging.info("Skipping cleanup for Firebase Storage file (kept): %s", temp_file_path)
        return

    # Delete local temp file
    try:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logging.info("Successfully cleaned up temporary file: %s", temp_file_path)
    except Exception as e:
        logging.exception("Failed to cleanup temporary file %s: %s", temp_file_path, e)
